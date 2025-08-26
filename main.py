import os
import time
import json
import queue
from threading import Thread
from dotenv import load_dotenv
from web3 import Web3
from web3.providers.websocket import WebsocketProvider
from eth_account import Account

# Try Web3 v6-compatible Flashbots first; fall back to legacy package
try:
    from web3_flashbots import flashbot  # pip install web3-flashbots
except ImportError:
    from flashbots import flashbot        # pip install flashbots

from utils import (
    is_uniswap_swap,
    estimate_ev_wei,
    estimate_ev_universal_wei,
    decode_swap_intent,
    build_sandwich_bundle,
    describe_tx,
    validate_token_liquidity,
    is_token_blacklisted,
)

# ------------ Setup ------------
load_dotenv("private.env")

# Use a WebSocket endpoint only (Alchemy/Infura/QuickNode etc.)
ETH_WS_URL = (os.getenv("ETH_WS_URL") or os.getenv("ETH_NODE_URL") or "").strip()
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
FLASHBOTS_KEY = os.getenv("FLASHBOTS_KEY")

if not PRIVATE_KEY or not FLASHBOTS_KEY:
    raise RuntimeError("Missing PRIVATE_KEY or FLASHBOTS_KEY in environment.")
if not ETH_WS_URL.startswith(("ws://", "wss://")):
    raise RuntimeError("Set ETH_WS_URL or ETH_NODE_URL to a wss:// (or ws://) endpoint.")

# Web3 over WebSocket only
w3 = Web3(WebsocketProvider(ETH_WS_URL, websocket_timeout=60))

searcher = Account.from_key(PRIVATE_KEY)
fb_signer = Account.from_key(FLASHBOTS_KEY)
flashbot(w3, fb_signer)

print(f"[boot] chain={w3.eth.chain_id} searcher={searcher.address}")
print(f"[rpc] ws  ={ETH_WS_URL}")

# ------------ Pending tx subscription via WebSocket ------------
pending_tx_queue: "queue.Queue[str]" = queue.Queue()

def start_ws_thread():
    try:
        import websocket  # pip install websocket-client
    except Exception:
        print("[warn] websocket-client not installed; run: pip install websocket-client")
        return

    def on_open(ws):
        sub = {"jsonrpc": "2.0", "id": 1, "method": "eth_subscribe", "params": ["newPendingTransactions"]}
        ws.send(json.dumps(sub))

    def on_message(ws, message):
        try:
            data = json.loads(message)
            params = data.get("params") or {}
            tx_hash = params.get("result")
            if isinstance(tx_hash, str) and tx_hash.startswith("0x") and len(tx_hash) == 66:
                pending_tx_queue.put(tx_hash)
        except Exception:
            pass

    def on_error(ws, error):
        print(f"[ws error] {error}")

    def on_close(ws, code, msg):
        print(f"[ws close] code={code} msg={msg}")

    def run():
        while True:
            try:
                ws = websocket.WebSocketApp(
                    ETH_WS_URL,
                    on_open=on_open,
                    on_message=on_message,
                    on_error=on_error,
                    on_close=on_close,
                )
                ws.run_forever(ping_interval=20, ping_timeout=10)
            except Exception as e:
                print(f"[ws fatal] {e}")
            time.sleep(3)

    Thread(target=run, daemon=True).start()

start_ws_thread()

# ------------ Main loop ------------
def main():
    ev_passed = 0
    ev_missed = 0
    while True:
        try:
            try:
                tx_hash = pending_tx_queue.get(timeout=1.0)
            except queue.Empty:
                time.sleep(0.05)
                continue

            try:
                tx = w3.eth.get_transaction(tx_hash)
            except Exception:
                continue

            if not is_uniswap_swap(tx):
                continue

            print(f"[mempool] {describe_tx(tx)}")

            # Check if transaction is worth processing
            intent = decode_swap_intent(w3, tx)
            if not intent or not intent.token_out:
                ev_missed += 1
                continue

            # Strict estimator, then universal fallback  
            res = estimate_ev_wei(w3, tx, priority_fee_gwei=1)
            if res is None:
                res = estimate_ev_universal_wei(w3, tx, buy_portion_bps=300, priority_fee_gwei=1)

            if res is None:
                ev_missed += 1
                if ev_missed % 50 == 0:
                    print(f"[stats] EV Passed: {ev_passed} | Missed: {ev_missed}")
                continue

            ev_wei, gas_wei, my_eth_in, back = res
            if ev_wei <= 0:
                continue

            # Decode victim for token_out
            intent = decode_swap_intent(w3, tx)
            token_out = intent.token_out if intent else None
            if not token_out:
                continue
            
            # Token validation: check blacklist and liquidity
            if is_token_blacklisted(token_out):
                ev_missed += 1
                continue
                
            # Validate token liquidity (skip validation for common stable tokens to save time)
            common_tokens = {"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "0xdAC17F958D2ee523a2206206994597C13D831ec7", "0x6B175474E89094C44Da98b954EedeAC495271d0F"}
            if token_out.lower() not in {t.lower() for t in common_tokens}:
                if not validate_token_liquidity(w3, token_out):
                    ev_missed += 1
                    continue

            # Fetch the victim raw tx (needed for inclusion)
            try:
                victim_raw = w3.eth.get_raw_transaction(tx_hash)
            except Exception:
                continue

            bundle = build_sandwich_bundle(
                w3, searcher, victim_raw, tx, token_out, my_eth_in, fee=3000, priority_fee_gwei=1
            )
            if not bundle:
                continue

            # Target next block
            target_block = w3.eth.block_number + 1
            try:
                result = w3.flashbots.send_bundle(bundle, target_block_number=target_block)
                receipts = result.wait()
                included = False
                if isinstance(receipts, list):
                    included = any((r or {}).get("status") == 1 for r in receipts)
                if included:
                    ev_passed += 1
                print(
                    f"[bundle] sent -> target={target_block} included={included} "
                    f"ev={Web3.from_wei(ev_wei, 'ether')} "
                    f"gas={Web3.from_wei(gas_wei, 'ether')} "
                    f"in={Web3.from_wei(my_eth_in, 'ether')} "
                    f"back={Web3.from_wei(back, 'ether')}"
                )
            except Exception as sb:
                print(f"[bundle error] {sb}")
                time.sleep(0.3)

            if ev_passed % 10 == 0 and ev_passed > 0:
                print(f"[stats] EV Passed: {ev_passed} | Missed: {ev_missed}")

        except KeyboardInterrupt:
            print("bye")
            break
        except Exception as outer:
            em = str(outer).lower()
            if any(phrase in em for phrase in ["value must be between", "invalid literal for int", "overflow", "out of range"]):
                continue
            print(f"[loop error] {outer}")
            time.sleep(0.3)

if __name__ == "__main__":
    main()
