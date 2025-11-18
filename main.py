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

import requests
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

from utils import (
    is_uniswap_swap,
    estimate_ev_wei,
    estimate_ev_universal_wei,
    estimate_ev_dynamic_wei,
    decode_swap_intent,
    build_sandwich_bundle,
    describe_tx,
    validate_token_liquidity,
    is_token_blacklisted,
)

# ------------ Setup ------------
load_dotenv("private.env")

# Use WebSocket endpoints with multiple fallbacks (Alchemy/Infura/QuickNode etc.)
ETH_WS_URL = os.getenv("ETH_WS_URL").strip()
ETH_WS_URL_FALLBACK = os.getenv("ETH_WS_URL_FALLBACK", "").strip()
ETH_WS_URL_FALLBACK2 = os.getenv("ETH_WS_URL_FALLBACK2", "").strip()
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
FLASHBOTS_KEY = os.getenv("FLASHBOTS_KEY")

# Optional tuning parameters
MIN_PROFIT_ETH = float(os.getenv("MIN_PROFIT_ETH", "0.0005"))  # Lowered from 0.001 to 0.0005 ETH to find more opportunities
PRIORITY_FEE_GWEI = int(os.getenv("PRIORITY_FEE_GWEI", "1"))   # Default 1 gwei priority fee
DRY_RUN = bool(int(os.getenv("DRY_RUN", "0")))                # Default false (actually execute trades)

# Build list of available WebSocket URLs
WS_URLS = [url for url in [ETH_WS_URL, ETH_WS_URL_FALLBACK, ETH_WS_URL_FALLBACK2] if url and url.startswith(("ws://", "wss://"))]

if not PRIVATE_KEY or not FLASHBOTS_KEY:
    raise RuntimeError("Missing PRIVATE_KEY or FLASHBOTS_KEY in environment.")
if not WS_URLS:
    raise RuntimeError("Set at least one valid WebSocket URL (ETH_WS_URL, ETH_WS_URL_FALLBACK, ETH_WS_URL_FALLBACK2).")

# Web3 over WebSocket with fallback capability
current_ws_index = 0
current_ws_url = WS_URLS[current_ws_index]

# Try to connect to providers at startup, fallback if needed
for i, ws_url in enumerate(WS_URLS):
    try:
        print(f"[boot] Trying provider {i+1}: {ws_url}")
        w3 = Web3(WebsocketProvider(ws_url, websocket_timeout=10))
        # Test connection with a simple call
        block_num = w3.eth.block_number
        current_ws_index = i
        current_ws_url = ws_url
        print(f"[boot] Connected successfully to provider {i+1}, latest block: {block_num}")
        break
    except Exception as e:
        print(f"[boot] Provider {i+1} failed: {e}")
        if i == len(WS_URLS) - 1:
            raise RuntimeError("All WebSocket providers failed to connect")
        continue

searcher = Account.from_key(PRIVATE_KEY)
fb_signer = Account.from_key(FLASHBOTS_KEY)
flashbot(w3, fb_signer)

print(f"[boot] chain={w3.eth.chain_id} searcher={searcher.address}")
print(f"[rpc] ws  ={current_ws_url}")
print(f"[config] MIN_PROFIT_ETH={MIN_PROFIT_ETH}, PRIORITY_FEE_GWEI={PRIORITY_FEE_GWEI}, DRY_RUN={DRY_RUN}")

# ------------ Multi-Builder Configuration ------------
class MEVBuilder:
    def __init__(self, name: str, endpoint: str, requires_auth: bool = False, auth_header: str = None):
        self.name = name
        self.endpoint = endpoint
        self.requires_auth = requires_auth
        self.auth_header = auth_header
        self.success_count = 0
        self.total_submissions = 0
        self.last_success_time = 0
        
    def get_success_rate(self) -> float:
        return self.success_count / max(1, self.total_submissions)
        
    def record_submission(self, success: bool):
        self.total_submissions += 1
        if success:
            self.success_count += 1
            self.last_success_time = time.time()

# MEV Builder endpoints
BUILDERS = {
    "flashbots": MEVBuilder("Flashbots", "https://relay.flashbots.net", True),
    "beaver": MEVBuilder("Beaver Build", "https://buildai.net", True),  
    "titan": MEVBuilder("Titan Builder", "https://rpc.titanbuilder.xyz", True),
    "bloxroute": MEVBuilder("bloXroute", "https://mev.api.blxrbdn.com", True),
    "eden": MEVBuilder("Eden Network", "https://api.edennetwork.io/v1", True),
}

# Builder success tracking
builder_stats = {name: {"sent": 0, "included": 0} for name in BUILDERS.keys()}

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
        global current_ws_index, current_ws_url, w3
        print(f"[ws error] {error}")
        
        # Check for rate limiting in WebSocket error
        error_str = str(error).lower()
        if any(phrase in error_str for phrase in ["429", "too many requests", "quota", "limit exceeded"]):
            print(f"[ws] Rate limit detected in error, switching providers...")
            if current_ws_index < len(WS_URLS) - 1:
                current_ws_index += 1
            else:
                current_ws_index = 0
                print(f"[ws] All providers exhausted, cycling back with delay...")
            
            current_ws_url = WS_URLS[current_ws_index]
            print(f"[ws] Switching to provider {current_ws_index + 1}: {current_ws_url}")
            
            # Update main Web3 instance
            try:
                w3.provider = WebsocketProvider(current_ws_url, websocket_timeout=60)
                print(f"[ws] Updated Web3 provider to {current_ws_url}")
            except Exception as e:
                print(f"[ws] Failed to update Web3 provider: {e}")

    def on_close(ws, code, msg):
        global current_ws_index, current_ws_url, w3
        print(f"[ws close] code={code} msg={msg}")
        
        # Check for rate limiting in close message
        if code == 1008 or (msg and "too many requests" in str(msg).lower()):
            print(f"[ws] Rate limit detected in close, switching providers...")
            if current_ws_index < len(WS_URLS) - 1:
                current_ws_index += 1
            else:
                current_ws_index = 0
                print(f"[ws] All providers exhausted, will retry after delay...")
            
            current_ws_url = WS_URLS[current_ws_index] 
            print(f"[ws] Switching to provider {current_ws_index + 1}: {current_ws_url}")
            
            # Update main Web3 instance
            try:
                w3.provider = WebsocketProvider(current_ws_url, websocket_timeout=60)
                print(f"[ws] Updated Web3 provider to {current_ws_url}")
            except Exception as e:
                print(f"[ws] Failed to update Web3 provider: {e}")

    def run():
        global current_ws_index, current_ws_url, w3
        
        while True:
            try:
                ws_url = WS_URLS[current_ws_index]
                provider_name = ["Primary", "Fallback", "Fallback2"][current_ws_index] if current_ws_index < 3 else f"Provider{current_ws_index+1}"
                print(f"[ws] Connecting to {provider_name} WebSocket...")
                
                ws = websocket.WebSocketApp(
                    ws_url,
                    on_open=on_open,
                    on_message=on_message,
                    on_error=on_error,
                    on_close=on_close,
                )
                ws.run_forever(ping_interval=20, ping_timeout=10)
                # Only reset to primary on successful connection that lasted > 30 seconds
                time.sleep(0.1)  # Brief delay before continuing
                
            except Exception as e:
                error_str = str(e).lower()
                print(f"[ws fatal] {e}")
                
                # Check for rate limiting or quota exceeded
                if any(phrase in error_str for phrase in ["429", "too many requests", "quota", "limit exceeded", "credits"]):
                    # Cycle to next provider
                    if current_ws_index < len(WS_URLS) - 1:
                        current_ws_index += 1
                    else:
                        current_ws_index = 0  # Cycle back to start
                        print(f"[ws] All providers tried, waiting before retry...")
                        time.sleep(30)  # Wait 30 seconds before cycling through again
                        
                    current_ws_url = WS_URLS[current_ws_index]
                    print(f"[ws] Switching to next provider due to rate limiting: {current_ws_url}")
                    
                    # Update main Web3 instance
                    try:
                        w3.provider = WebsocketProvider(current_ws_url, websocket_timeout=60)
                        print(f"[ws] Updated main Web3 provider to index {current_ws_index}")
                    except Exception as provider_error:
                        print(f"[ws] Failed to update Web3 provider: {provider_error}")
                    continue
                else:
                    time.sleep(1)  # Minimal delay for non-rate-limit errors

    Thread(target=run, daemon=True).start()

start_ws_thread()

# ------------ Multi-Builder Bundle Submission ------------
def submit_bundle_to_builder(builder_name: str, bundle: list, target_block: int, priority_fee_gwei: int = 1):
    """Submit bundle to a specific MEV builder"""
    try:
        builder = BUILDERS[builder_name]
        
        if builder_name == "flashbots":
            # Use existing Flashbots integration
            result = w3.flashbots.send_bundle(bundle, target_block_number=target_block)
            receipts = result.wait()
            included = False
            if isinstance(receipts, list):
                included = any((r or {}).get("status") == 1 for r in receipts)
            return included, "flashbots"
            
        else:
            # Generic builder submission via HTTP API
            bundle_hex = [tx.hex() if isinstance(tx, bytes) else tx for tx in bundle]
            
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_sendBundle",
                "params": [{
                    "txs": bundle_hex,
                    "blockNumber": hex(target_block),
                    "minTimestamp": 0,
                    "maxTimestamp": 0
                }]
            }
            
            headers = {
                "Content-Type": "application/json",
            }
            
            # Add auth if required
            if builder.requires_auth and builder.auth_header:
                headers["Authorization"] = builder.auth_header
                
            response = requests.post(
                builder.endpoint,
                json=payload,
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                return True, builder_name  # Assume success if no error
            else:
                print(f"[{builder_name}] HTTP error {response.status_code}: {response.text}")
                return False, builder_name
                
    except Exception as e:
        print(f"[{builder_name}] Submission error: {e}")
        return False, builder_name

def submit_bundle_multi_builder(bundle: list, target_block: int, priority_fee_gwei: int = 1):
    """Submit bundle to multiple builders simultaneously"""
    
    # Select builders based on recent performance
    active_builders = []
    current_time = time.time()
    
    # Always include Flashbots
    active_builders.append("flashbots")
    
    # Include other builders based on recent success
    for name, builder in BUILDERS.items():
        if name == "flashbots":
            continue
            
        # Include builder if:
        # 1. It has good success rate (>10%), OR  
        # 2. It hasn't been tried much yet (<10 attempts), OR
        # 3. It had recent success (within last hour)
        success_rate = builder.get_success_rate()
        recent_success = (current_time - builder.last_success_time) < 3600  # 1 hour
        
        if success_rate > 0.1 or builder.total_submissions < 10 or recent_success:
            active_builders.append(name)
    
    # Limit to top 4 builders to avoid spam
    active_builders = active_builders[:4]
    
    print(f"[multi-builder] Submitting to: {', '.join(active_builders)}")
    
    # Submit to all builders concurrently
    with ThreadPoolExecutor(max_workers=len(active_builders)) as executor:
        futures = []
        
        for builder_name in active_builders:
            future = executor.submit(
                submit_bundle_to_builder, 
                builder_name, 
                bundle, 
                target_block, 
                priority_fee_gwei
            )
            futures.append(future)
        
        # Collect results
        results = []
        any_included = False
        
        for future in futures:
            try:
                included, builder_name = future.result(timeout=10)
                results.append((builder_name, included))
                
                # Update builder stats
                BUILDERS[builder_name].record_submission(included)
                builder_stats[builder_name]["sent"] += 1
                
                if included:
                    builder_stats[builder_name]["included"] += 1
                    any_included = True
                    
            except Exception as e:
                print(f"[multi-builder] Future error: {e}")
        
        return any_included, results

def print_builder_stats():
    """Print builder performance statistics"""
    print("\n[builder-stats] Performance Summary:")
    for name, stats in builder_stats.items():
        if stats["sent"] > 0:
            rate = (stats["included"] / stats["sent"]) * 100
            builder = BUILDERS[name]
            total_rate = builder.get_success_rate() * 100
            print(f"  {name}: {stats['included']}/{stats['sent']} ({rate:.1f}%) total_rate={total_rate:.1f}%")

# ------------ Main loop ------------
def main():
    ev_passed = 0
    ev_missed = 0
    last_stats_time = time.time()
    stats_interval = 300  # Print builder stats every 5 minutes
    
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
                print(f"[debug] Failed intent decode: intent={intent is not None}, token_out={getattr(intent, 'token_out', None) if intent else None}")
                continue

            print(f"[debug] Processing swap: {intent.token_in} -> {intent.token_out}, amount={intent.amount_in_wei}, kind={intent.kind}")

            # Early validation: check if token addresses look valid
            if intent.token_out and not validate_token_liquidity(w3, intent.token_out):
                ev_missed += 1
                print(f"[debug] Token validation failed for {intent.token_out}")
                continue

            # Try dynamic sizing first (most advanced), then fallback to other methods
            res = estimate_ev_dynamic_wei(w3, tx, priority_fee_gwei=PRIORITY_FEE_GWEI)
            estimator_used = "dynamic"
            if res is None:
                # Fallback to strict estimator
                res = estimate_ev_wei(w3, tx, priority_fee_gwei=PRIORITY_FEE_GWEI)
                estimator_used = "strict"
            if res is None:
                # Final fallback to universal estimator with more generous parameters
                res = estimate_ev_universal_wei(w3, tx, buy_portion_bps=500, priority_fee_gwei=PRIORITY_FEE_GWEI)  # Increased from 300 to 500 bps
                estimator_used = "universal"

            if res is None:
                ev_missed += 1
                print(f"[debug] All EV estimators failed for {intent.token_out}")
                if ev_missed % 50 == 0:
                    print(f"[stats] EV Passed: {ev_passed} | Missed: {ev_missed}")
                continue

            ev_wei, gas_wei, my_eth_in, back = res
            profit_eth = Web3.from_wei(back - my_eth_in, 'ether')
            print(f"[debug] EV result from {estimator_used}: ev={Web3.from_wei(ev_wei, 'ether'):.6f} ETH, profit={profit_eth:.6f} ETH")
            
            if ev_wei <= 0:
                print(f"[debug] Negative EV: {Web3.from_wei(ev_wei, 'ether'):.6f} ETH")
                continue
                
            # Apply MIN_PROFIT_ETH threshold
            if profit_eth < MIN_PROFIT_ETH:
                print(f"[debug] Profit {profit_eth:.6f} ETH below minimum threshold {MIN_PROFIT_ETH} ETH")
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
                w3, searcher, victim_raw, tx, token_out, my_eth_in, fee=3000, priority_fee_gwei=PRIORITY_FEE_GWEI
            )
            if not bundle:
                continue

            # Target next block
            target_block = w3.eth.block_number + 1
            try:
                # Submit bundle to multiple builders
                included, results = submit_bundle_multi_builder(bundle, target_block, priority_fee_gwei=PRIORITY_FEE_GWEI)
                
                if included:
                    ev_passed += 1
                
                # Show which builders succeeded
                success_builders = [name for name, success in results if success]
                all_builders = [name for name, _ in results]
                
                print(
                    f"[bundle] sent -> target={target_block} included={included} "
                    f"builders={'/'.join(all_builders)} success={'/'.join(success_builders) if success_builders else 'none'} "
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
            
            # Print builder stats periodically
            current_time = time.time()
            if current_time - last_stats_time > stats_interval:
                print_builder_stats()
                last_stats_time = current_time

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
