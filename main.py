import os
import time
from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account

# Try Web3 v6-compatible Flashbots first; fall back to legacy package
try:
    from web3_flashbots import flashbot  # pip install web3-flashbots
except ImportError:
    from flashbots import flashbot        # pip install flashbots

from utils import is_uniswap_swap, build_sandwich_bundle, estimate_ev_wei

# ------------ Setup ------------
load_dotenv("private.env")

ETH_NODE_URL = os.getenv("ETH_NODE_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
FLASHBOTS_KEY = os.getenv("FLASHBOTS_KEY")

# Optional tuning
MIN_PROFIT_ETH = float(os.getenv("MIN_PROFIT_ETH", "0.0001"))  # skip if EV < this (lowered threshold)
PRIORITY_FEE_GWEI = int(os.getenv("PRIORITY_FEE_GWEI", "1"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"  # build + simulate only; don't send

if not ETH_NODE_URL or not PRIVATE_KEY or not FLASHBOTS_KEY:
    raise RuntimeError("Missing ETH_NODE_URL, PRIVATE_KEY or FLASHBOTS_KEY in environment.")

w3 = Web3(Web3.WebsocketProvider(ETH_NODE_URL))

# Accounts
searcher = Account.from_key(PRIVATE_KEY)
signer = Account.from_key(FLASHBOTS_KEY)

# Initialize Flashbots (adds w3.flashbots.*)
flashbot(w3, signer)

is_connected = getattr(w3, "is_connected", None)
connected = is_connected() if callable(is_connected) else w3.isConnected()
print(f"Connected: {connected} | Chain ID: {w3.eth.chain_id}")
print(f"Searcher: {searcher.address}")
print(f"MIN_PROFIT_ETH={MIN_PROFIT_ETH} | PRIORITY_FEE_GWEI={PRIORITY_FEE_GWEI} | DRY_RUN={DRY_RUN}")

# Pending tx feed using WebSocket subscription
import asyncio
from threading import Thread
import queue

pending_tx_queue = queue.Queue()

# More comprehensive Uniswap detection
def is_uniswap_swap_comprehensive(tx) -> bool:
    """More comprehensive detection for Uniswap and DEX swaps"""
    try:
        if not tx.to or not tx.input or len(tx.input) < 10:
            return False
        
        # Handle both string and bytes for transaction data
        to_addr = tx.to.lower() if hasattr(tx.to, 'lower') else Web3.to_checksum_address(tx.to).lower()
        
        # Handle input data - could be string or bytes
        if isinstance(tx.input, bytes):
            input_hex = tx.input.hex().lower()
        else:
            input_hex = tx.input.lower()
            if input_hex.startswith('0x'):
                input_hex = input_hex[2:]
        
        sig = "0x" + input_hex[:8]
        
        # Known Uniswap router addresses (lowercase)
        uniswap_routers = {
            "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",  # V2 Router
            "0xe592427a0aece92de3edee1f18e0157c05861564",  # V3 Router
            "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45",  # V3 Router 2
            "0xef1c6e67703c7bd7107eed8303fbe6ec2554bf6b",  # Universal Router
        }
        
        # Common swap function signatures
        swap_signatures = {
            # V2 swaps
            "0x38ed1739",  # swapExactTokensForTokens
            "0x7ff36ab5",  # swapExactETHForTokens  
            "0x18cbafe5",  # swapExactTokensForETH
            "0x4a25d94a",  # swapTokensForExactETH
            "0x791ac947",  # swapExactTokensForETHSupportingFeeOnTransferTokens
            "0xb6f9de95",  # swapExactETHForTokensSupportingFeeOnTransferTokens
            
            # V3 swaps
            "0x04e45aaf",  # exactInputSingle
            "0xb858183f",  # exactInput
            "0x09b81346",  # exactOutputSingle
            "0x5023b4df",  # exactOutput
            
            # Universal Router
            "0x3593564c",  # execute
            "0x24856bc3",  # execute (overloaded)
            
            # Common DEX patterns
            "0xa9059cbb",  # transfer (sometimes part of swaps)
            "0x095ea7b3",  # approve (often precedes swaps)
        }
        
        # Check if transaction is to a known router with swap signature
        if to_addr in uniswap_routers and sig in swap_signatures:
            return True
            
        # Check if transaction has ETH value + swap signature (common pattern)
        try:
            if tx.value and int(tx.value) > 0 and sig in swap_signatures:
                return True
        except (ValueError, TypeError, OverflowError):
            # Skip transactions with invalid value fields
            pass
            
        # Look for swap-related keywords in transaction data (broader detection)
        full_input = "0x" + input_hex
        if any(keyword in full_input for keyword in [
            "c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # WETH address
        ]):
            return True
        
        return False
        
    except Exception as e:
        # If there's any error in detection, fall back to original function
        return is_uniswap_swap(tx)

# Debug counters
tx_received_count = 0
tx_processed_count = 0
uniswap_detected_count = 0
ev_passed_count = 0

# WebSocket subscription function
def subscribe_pending_txs():
    """Subscribe to pending transactions via WebSocket"""
    try:
        # Use the websocket provider directly
        import json
        import websockets
        import asyncio
        
        async def listen():
            while True:  # Reconnection loop
                try:
                    uri = ETH_NODE_URL.replace('https://mainnet.infura.io/v3/', 'wss://mainnet.infura.io/ws/v3/')
                    print(f"[websocket] Connecting to {uri[:50]}...")
                    
                    async with websockets.connect(uri, ping_interval=20) as websocket:
                        # Subscribe to pending transactions
                        subscription_request = {
                            "id": 1,
                            "method": "eth_subscribe",
                            "params": ["newPendingTransactions"]
                        }
                        await websocket.send(json.dumps(subscription_request))
                        print("[websocket] Subscribed to pending transactions")
                        
                        # Listen for responses
                        while True:
                            try:
                                message = await websocket.recv()
                                data = json.loads(message)
                                
                                # Check if it's a subscription notification
                                if 'params' in data and 'result' in data['params']:
                                    tx_hash = data['params']['result']
                                    if tx_hash:
                                        global tx_received_count
                                        tx_received_count += 1
                                        pending_tx_queue.put(tx_hash)
                                        
                            except websockets.exceptions.ConnectionClosed:
                                print("[websocket] Connection closed, reconnecting...")
                                break
                            except Exception as e:
                                print(f"[websocket error] {e}")
                                
                except Exception as e:
                    print(f"[websocket connection error] {e}")
                    print("[websocket] Retrying in 5 seconds...")
                    await asyncio.sleep(5)
        
        asyncio.run(listen())
    except Exception as e:
        print(f"[subscription setup error] {e}")

def start_subscription_thread():
    """Start the WebSocket subscription in a separate thread"""
    def run_subscription():
        try:
            subscribe_pending_txs()
        except Exception as e:
            print(f"[subscription error] {e}")
    
    thread = Thread(target=run_subscription, daemon=True)
    thread.start()
    return thread

# ------------ Main loop ------------
def main():
    print("Scanner started. Watching pending mempool for Uniswap V2/V3 swaps...")
    
    # Start WebSocket subscription thread
    start_subscription_thread()
    print("WebSocket subscription started...")
    
    last_stats_time = time.time()
    
    while True:
        try:
            global tx_processed_count, uniswap_detected_count, ev_passed_count
            
            # Print stats every 30 seconds regardless of queue state
            if time.time() - last_stats_time > 30:
                print(f"[stats] Received: {tx_received_count}, Processed: {tx_processed_count}, Uniswap: {uniswap_detected_count}, EV Passed: {ev_passed_count}")
                last_stats_time = time.time()
            
            try:
                tx_hash = pending_tx_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            tx_processed_count += 1

            # web3 v5/v6 compatibility
            get_tx = getattr(w3.eth, "get_transaction", None) or w3.eth.getTransaction
            try:
                tx = get_tx(tx_hash)
            except Exception as e:
                error_msg = str(e).lower()
                # Skip common mempool errors silently
                if any(phrase in error_msg for phrase in [
                    "internal error", 
                    "not found", 
                    "transaction with hash",
                    "could not find transaction"
                ]):
                    continue  # Skip silently for common mempool issues
                print(f"[tx_fetch_error] {e}")
                continue

            # More comprehensive Uniswap detection
            try:
                if not is_uniswap_swap_comprehensive(tx):
                    continue
            except Exception as e:
                print(f"[detection_error] {e}")
                continue
                
            uniswap_detected_count += 1
            # Debug: Show transaction details to understand what we're detecting
            to_addr = tx.to.lower() if hasattr(tx.to, 'lower') else Web3.to_checksum_address(tx.to).lower()
            if isinstance(tx.input, bytes):
                input_hex = tx.input.hex().lower()
            else:
                input_hex = tx.input.lower()
                if input_hex.startswith('0x'):
                    input_hex = input_hex[2:]
            sig = "0x" + input_hex[:8]
            value_eth = Web3.from_wei(tx.value or 0, "ether") if tx.value else 0
            print(f"[uniswap] Found swap tx: {tx_hash} | To: {to_addr[-6:]} | Sig: {sig} | Value: {value_eth:.4f} ETH")

            # 1) EV gate (quick pre-check, conservative)
            try:
                ev_info = estimate_ev_wei(w3, tx, priority_fee_gwei=PRIORITY_FEE_GWEI)
            except Exception as e:
                error_msg = str(e).lower()
                # Skip common errors silently
                if any(phrase in error_msg for phrase in [
                    "internal error",
                    "value must be between",
                    "execution reverted",
                    "call exception",
                    "invalid argument"
                ]):
                    continue  # Skip silently for common issues
                print(f"[ev_error] {e}")
                continue
                
            if not ev_info:
                continue

            ev_wei, gas_wei, spent_wei, recv_wei = ev_info
            ev_eth = Web3.from_wei(ev_wei, "ether")
            if ev_eth < MIN_PROFIT_ETH:
                print(f"[ev_gate] EV too low: {ev_eth:.6f} ETH < {MIN_PROFIT_ETH} ETH")
                continue
            
            ev_passed_count += 1

            print(f"[candidate] {tx.hash.hex()} EV≈{ev_eth:.6f} ETH "
                  f"(recv≈{Web3.from_wei(recv_wei,'ether'):.6f} - "
                  f"spent≈{Web3.from_wei(spent_wei,'ether'):.6f} - "
                  f"gas≈{Web3.from_wei(gas_wei,'ether'):.6f})")

            # 2) Build bundle
            try:
                bundle = build_sandwich_bundle(w3, tx, searcher, priority_fee_gwei=PRIORITY_FEE_GWEI)
            except Exception as e:
                print(f"[build error] {e}")
                continue

            if not bundle:
                continue

            target_block = getattr(w3.eth, "block_number", None) or w3.eth.blockNumber
            target_block += 1

            # 3) Optional simulation (best-effort)
            try:
                sim_result = w3.flashbots.simulate(bundle, target_block)
                print(f"[simulate] ok: {sim_result}")
            except Exception as e:
                print(f"[simulate] failed (continuing anyway): {e}")

            if DRY_RUN:
                print("[dry-run] NOT sending bundle.")
                continue

            # 4) Send
            try:
                send_result = w3.flashbots.send_bundle(bundle, target_block)
                print(f"[send] submitted for block {target_block}: {send_result}")
            except Exception as e:
                print(f"[send error] {e}")

            time.sleep(0.05)  # avoid busy spin
        except Exception as outer:
            error_msg = str(outer).lower()
            # Skip common value overflow errors silently
            if any(phrase in error_msg for phrase in [
                "value must be between",
                "invalid literal for int",
                "overflow",
                "out of range"
            ]):
                continue  # Skip silently
            print(f"[loop error] {outer}")
            time.sleep(1.0)

if __name__ == "__main__":
    main()
