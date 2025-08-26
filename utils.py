import time
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
from eth_account import Account
from web3 import Web3

# --------- Addresses (Ethereum mainnet) ---------
UNISWAP_V2_ROUTER   = Web3.to_checksum_address("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")
UNISWAP_V3_ROUTER   = Web3.to_checksum_address("0xE592427A0AEce92De3Edee1F18E0157C05861564")
UNISWAP_V3_PERIPH   = Web3.to_checksum_address("0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45")  # v3 periphery
UNISWAP_V3_QUOTERV2 = Web3.to_checksum_address("0x61fFE014bA17989E743c5F6cB21bF9697530B21e")
UNIVERSAL_ROUTER    = Web3.to_checksum_address("0xEf1c6E67703c7BD7107eed8303Fbe6EC2554BF6B")
ONEINCH_V5          = Web3.to_checksum_address("0x1111111254EEB25477B68fb85Ed929f73A960582")
ZEROX_EX            = Web3.to_checksum_address("0xDef1C0ded9bec7F1a1670819833240f027b25EfF")  # 0x Exchange Proxy
PARASWAP            = Web3.to_checksum_address("0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57")
WETH9               = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
USDC                = Web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606EB48")

KNOWN_ROUTERS: Dict[str, str] = {
    UNISWAP_V2_ROUTER: "Uniswap V2",
    UNISWAP_V3_ROUTER: "Uniswap V3",
    UNISWAP_V3_PERIPH: "Uniswap V3 Periphery",
    UNIVERSAL_ROUTER:  "Uniswap Universal Router",
    ONEINCH_V5:        "1inch v5",
    ZEROX_EX:          "0x Exchange",
    PARASWAP:          "ParaSwap",
}

UNISWAP_V2_ROUTERS = {UNISWAP_V2_ROUTER}
UNISWAP_V3_ROUTERS = {UNISWAP_V3_ROUTER, UNISWAP_V3_PERIPH}
ONEINCH_ROUTERS    = {ONEINCH_V5}

# --------- ABIs (minimal) ---------
UNISWAP_V2_ROUTER_ABI = [
    {"type":"function","name":"swapExactETHForTokens","stateMutability":"payable",
     "inputs":[
        {"name":"amountOutMin","type":"uint256"},
        {"name":"path","type":"address[]"},
        {"name":"to","type":"address"},
        {"name":"deadline","type":"uint256"}],
     "outputs":[{"name":"amounts","type":"uint256[]"}]},
    {"type":"function","name":"swapExactTokensForETH","stateMutability":"nonpayable",
     "inputs":[
        {"name":"amountIn","type":"uint256"},
        {"name":"amountOutMin","type":"uint256"},
        {"name":"path","type":"address[]"},
        {"name":"to","type":"address"},
        {"name":"deadline","type":"uint256"}],
     "outputs":[{"name":"amounts","type":"uint256[]"}]},
    {"type":"function","name":"swapExactTokensForTokens","stateMutability":"nonpayable",
     "inputs":[
        {"name":"amountIn","type":"uint256"},
        {"name":"amountOutMin","type":"uint256"},
        {"name":"path","type":"address[]"},
        {"name":"to","type":"address"},
        {"name":"deadline","type":"uint256"}],
     "outputs":[{"name":"amounts","type":"uint256[]"}]},
    {"type":"function","name":"swapExactETHForTokensSupportingFeeOnTransferTokens","stateMutability":"payable",
     "inputs":[
        {"name":"amountOutMin","type":"uint256"},
        {"name":"path","type":"address[]"},
        {"name":"to","type":"address"},
        {"name":"deadline","type":"uint256"}],
     "outputs":[]},
    {"type":"function","name":"swapExactTokensForETHSupportingFeeOnTransferTokens","stateMutability":"nonpayable",
     "inputs":[
        {"name":"amountIn","type":"uint256"},
        {"name":"amountOutMin","type":"uint256"},
        {"name":"path","type":"address[]"},
        {"name":"to","type":"address"},
        {"name":"deadline","type":"uint256"}],
     "outputs":[]},
    {"type":"function","name":"getAmountsOut","stateMutability":"view",
     "inputs":[{"name":"amountIn","type":"uint256"},{"name":"path","type":"address[]"}],
     "outputs":[{"name":"amounts","type":"uint256[]"}]},
]

UNISWAP_V3_ROUTER_ABI = [
    {"type":"function","name":"exactInputSingle","stateMutability":"payable",
     "inputs":[{"name":"params","type":"tuple","components":[
        {"name":"tokenIn","type":"address"},{"name":"tokenOut","type":"address"},
        {"name":"fee","type":"uint24"},{"name":"recipient","type":"address"},
        {"name":"deadline","type":"uint256"},{"name":"amountIn","type":"uint256"},
        {"name":"amountOutMinimum","type":"uint256"},{"name":"sqrtPriceLimitX96","type":"uint160"}]}],
     "outputs":[{"name":"amountOut","type":"uint256"}]},
    {"type":"function","name":"exactInput","stateMutability":"payable",
     "inputs":[{"name":"params","type":"tuple","components":[
        {"name":"path","type":"bytes"},{"name":"recipient","type":"address"},
        {"name":"deadline","type":"uint256"},{"name":"amountIn","type":"uint256"},
        {"name":"amountOutMinimum","type":"uint256"}]}],
     "outputs":[{"name":"amountOut","type":"uint256"}]},
]

QUOTER_V2_ABI = [
    {"type":"function","name":"quoteExactInputSingle","stateMutability":"nonpayable",
     "inputs":[
        {"name":"tokenIn","type":"address"},
        {"name":"tokenOut","type":"address"},
        {"name":"fee","type":"uint24"},
        {"name":"amountIn","type":"uint256"},
        {"name":"sqrtPriceLimitX96","type":"uint160"}],
     "outputs":[
        {"name":"amountOut","type":"uint256"},
        {"name":"sqrtPriceX96After","type":"uint160"},
        {"name":"initializedTicksCrossed","type":"uint32"},
        {"name":"gasEstimate","type":"uint256"}]},
]

ERC20_ABI = [
    {"type":"function","name":"decimals","stateMutability":"view","inputs":[],"outputs":[{"type":"uint8"}]},
    {"type":"function","name":"approve","stateMutability":"nonpayable",
     "inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"outputs":[{"type":"bool"}]},
    {"type":"function","name":"balanceOf","stateMutability":"view",
     "inputs":[{"name":"account","type":"address"}],"outputs":[{"type":"uint256"}]},
    {"type":"function","name":"allowance","stateMutability":"view",
     "inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"outputs":[{"type":"uint256"}]},
]

WETH9_ABI = [
    {"type":"function","name":"deposit","stateMutability":"payable","inputs":[],"outputs":[]},
    {"type":"function","name":"withdraw","stateMutability":"nonpayable","inputs":[{"type":"uint256"}],"outputs":[]},
    {"type":"function","name":"approve","stateMutability":"nonpayable",
     "inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"outputs":[{"type":"bool"}]},
]

ONEINCH_AGG_ABI = [{
    "type":"function","name":"swap","inputs":[
        {"name":"executor","type":"address"},
        {"name":"desc","type":"tuple","components":[
            {"name":"srcToken","type":"address"},
            {"name":"dstToken","type":"address"},
            {"name":"srcReceiver","type":"address"},
            {"name":"dstReceiver","type":"address"},
            {"name":"amount","type":"uint256"},
            {"name":"minReturnAmount","type":"uint256"},
            {"name":"flags","type":"uint256"},
            {"name":"permit","type":"bytes"}]},
        {"name":"data","type":"bytes"}],
    "outputs":[{"name":"returnAmount","type":"uint256"}]
}]

# --------- Logging helpers ---------
def short_addr(addr: Optional[str]) -> str:
    if not addr:
        return "None"
    try:
        a = Web3.to_checksum_address(addr)
    except Exception:
        return addr[:10] + "..."
    return a[:8] + "…" + a[-6:]

def get_router_name(address: Optional[str]) -> str:
    if not address:
        return "None"
    try:
        a = Web3.to_checksum_address(address)
    except Exception:
        return address
    return KNOWN_ROUTERS.get(a, f"Router {short_addr(a)}")

def sig4(tx_input) -> str:
    raw = tx_input.hex() if isinstance(tx_input, (bytes, bytearray)) else str(tx_input)
    raw = raw.lower()
    if raw.startswith("0x"):
        raw = raw[2:]
    return "0x" + raw[:8] if len(raw) >= 8 else "0x"

# --------- Swap intent ---------
@dataclass
class SwapIntent:
    token_in: Optional[str]
    token_out: Optional[str]
    amount_in_wei: Optional[int]  # None if unknown
    kind: str                     # 'v2','v3','1inch','universal','unknown'
    path_v2: Optional[List[str]] = None
    path_v3: Optional[List[str]] = None  # tokens in hop order
    fees_v3: Optional[List[int]] = None  # fee per hop

def _hex_input(tx) -> str:
    s = tx.input.hex() if isinstance(tx.input, (bytes, bytearray)) else str(tx.input)
    s = s.lower()
    return s[2:] if s.startswith("0x") else s

def _parse_v3_path(path_bytes: bytes) -> Tuple[List[str], List[int]]:
    b = path_bytes
    if isinstance(b, str) and b.startswith("0x"):
        b = bytes.fromhex(b[2:])
    tokens, fees = [], []
    i = 0
    while i + 20 <= len(b):
        tokens.append(Web3.to_checksum_address("0x" + b[i:i+20].hex()))
        i += 20
        # if another token follows, there must be a fee
        if i + 20 <= len(b):
            if i + 3 > len(b):
                break
            fees.append(int.from_bytes(b[i:i+3], "big"))
            i += 3
    return tokens, fees

def _scan_addresses_from_calldata(data_hex_no0x: str) -> List[str]:
    b = bytes.fromhex(data_hex_no0x)
    seen, out = set(), []
    # scan on 1-byte steps to be permissive
    for i in range(0, max(0, len(b) - 20 + 1)):
        addr = "0x" + b[i:i+20].hex()
        try:
            ca = Web3.to_checksum_address(addr)
        except Exception:
            continue
        if ca.endswith("0000000000000000000000000000000000000000"):
            continue
        if ca not in seen:
            seen.add(ca); out.append(ca)
    return out

def decode_swap_intent(w3: Web3, tx) -> Optional[SwapIntent]:
    if not tx.to or not tx.input or len(str(tx.input)) < 10:
        return None
    to = Web3.to_checksum_address(tx.to)
    data_hex = _hex_input(tx)
    s4 = "0x" + data_hex[:8]

    # v2
    if to in UNISWAP_V2_ROUTERS:
        router = w3.eth.contract(address=to, abi=UNISWAP_V2_ROUTER_ABI)
        try:
            fn, args = router.decode_function_input(tx.input)
            name = fn.fn_name
            path = list(map(Web3.to_checksum_address, args.get("path") or args.get(2) or []))
            amt_in = None
            if "amountIn" in args: amt_in = int(args["amountIn"])
            elif name.startswith("swapExactETHFor"): amt_in = int(tx.value or 0)
            return SwapIntent(
                token_in=path[0] if path else None,
                token_out=path[-1] if path else None,
                amount_in_wei=amt_in,
                kind="v2", path_v2=path
            )
        except Exception:
            pass

    # v3 (router or periphery)
    if to in UNISWAP_V3_ROUTERS:
        r = w3.eth.contract(address=to, abi=UNISWAP_V3_ROUTER_ABI)
        try:
            fn, args = r.decode_function_input(tx.input)
            name = fn.fn_name
            if name == "exactInputSingle":
                p = args["params"]
                t_in  = Web3.to_checksum_address(p["tokenIn"])
                t_out = Web3.to_checksum_address(p["tokenOut"])
                amt_in = int(p.get("amountIn") or tx.value or 0)
                return SwapIntent(
                    token_in=t_in, token_out=t_out, amount_in_wei=amt_in, kind="v3",
                    path_v3=[t_in, t_out], fees_v3=[int(p["fee"])]
                )
            if name == "exactInput":
                p = args["params"]
                tokens, fees = _parse_v3_path(p["path"])
                amt_in = int(p.get("amountIn") or tx.value or 0)
                return SwapIntent(
                    token_in=tokens[0] if tokens else None,
                    token_out=tokens[-1] if tokens else None,
                    amount_in_wei=amt_in,
                    kind="v3", path_v3=tokens, fees_v3=fees
                )
        except Exception:
            pass

    # 1inch
    if to in ONEINCH_ROUTERS and s4 == "0x12aa3caf":
        c = w3.eth.contract(address=to, abi=ONEINCH_AGG_ABI)
        try:
            fn, args = c.decode_function_input(tx.input)
            desc = args.get("desc") or {}
            src = Web3.to_checksum_address(desc.get("srcToken"))
            dst = Web3.to_checksum_address(desc.get("dstToken"))
            amt = int(desc.get("amount") or tx.value or 0)
            return SwapIntent(token_in=src, token_out=dst, amount_in_wei=amt, kind="1inch")
        except Exception:
            pass

    # Universal Router: try to decode commands (signature 0x3593564c)
    if to == UNIVERSAL_ROUTER and s4 == "0x3593564c":
        try:
            # Universal router has commands and inputs arrays
            # For ETH swaps, WETH is typically involved, look for common tokens
            if int(tx.value or 0) > 0:
                # This is an ETH->token swap, fallback to USDC for now
                return SwapIntent(
                    token_in=WETH9, 
                    token_out=USDC, 
                    amount_in_wei=int(tx.value), 
                    kind="universal"
                )
        except Exception:
            pass
    
    # V3 Periphery multicall (signature 0x5ae401dc)  
    if to == UNISWAP_V3_PERIPH and s4 == "0x5ae401dc":
        try:
            # Try to find actual tokens in the multicall data instead of defaulting to USDC
            addrs = _scan_addresses_from_calldata(data_hex)
            
            if int(tx.value or 0) > 0:
                # ETH->token swap - find the target token
                token_in = WETH9
                token_out = None
                
                # Look for a token that's not WETH
                for addr in addrs:
                    if (addr != WETH9 and addr != UNISWAP_V3_PERIPH and 
                        not addr.endswith("0000000000000000000000000000000000000000") and
                        len(addr) == 42 and addr.startswith("0x")):
                        token_out = addr
                        break
                        
                # Fallback to USDC if no other token found
                if not token_out:
                    token_out = USDC
                    
                return SwapIntent(
                    token_in=token_in,
                    token_out=token_out,
                    amount_in_wei=int(tx.value),
                    kind="universal"
                )
        except Exception:
            pass

    # Universal/unknown: enhanced heuristic with fallback
    addrs = _scan_addresses_from_calldata(data_hex)
    token_in, token_out = None, None
    if int(tx.value or 0) > 0:
        token_in = WETH9
        # Look for valid, non-zero addresses that are NOT WETH
        for a in addrs:
            if (a != WETH9 and 
                not a.endswith("0000000000000000000000000000000000000000") and
                len(a) == 42 and a.startswith("0x")):
                token_out = a
                break
    else:
        # For token->token swaps, find two different valid addresses
        valid_addrs = [a for a in addrs if (
            not a.endswith("0000000000000000000000000000000000000000") and
            len(a) == 42 and a.startswith("0x") and a != WETH9
        )]
        if len(valid_addrs) >= 2 and valid_addrs[0] != valid_addrs[1]:
            token_in, token_out = valid_addrs[0], valid_addrs[1]
    
    # If we still don't have token_out, try common patterns
    if not token_out and int(tx.value or 0) > 0:
        # For ETH swaps, try to find any token address that's not WETH
        common_tokens = [USDC, "0xdac17f958d2ee523a2206206994597c13d831ec7"]  # USDT
        for common in common_tokens:
            if common.lower() in data_hex:
                token_out = common
                break
        
        # Last resort: if we have ETH value but no token_out, assume USDC
        if not token_out:
            token_out = USDC
    
    # Final check: ensure token_in and token_out are different
    if token_in and token_out and token_in.lower() == token_out.lower():
        token_out = USDC
            
    amt_in = int(tx.value or 0) if token_in in (None, WETH9) else None
    kind = "universal" if token_out else "unknown"
    return SwapIntent(token_in, token_out, amt_in, kind=kind)

# --------- Quoters (V2/V3) ----------
def _try_v2_roundtrip(w3: Web3, router_addr: str, eth_in: int, token: str) -> Optional[int]:
    router = w3.eth.contract(address=router_addr, abi=UNISWAP_V2_ROUTER_ABI)
    try:
        out = int(router.functions.getAmountsOut(eth_in, [WETH9, token]).call()[-1])
        back = int(router.functions.getAmountsOut(out, [token, WETH9]).call()[-1])
        return back
    except Exception:
        return None

def _try_v2_roundtrip_twohop(w3: Web3, router_addr: str, eth_in: int, token: str) -> Optional[int]:
    router = w3.eth.contract(address=router_addr, abi=UNISWAP_V2_ROUTER_ABI)
    path1 = [WETH9, USDC, token]
    path2 = [token, USDC, WETH9]
    try:
        out = int(router.functions.getAmountsOut(eth_in, path1).call()[-1])
        back = int(router.functions.getAmountsOut(out, path2).call()[-1])
        return back
    except Exception:
        return None

def _try_v3_direct_roundtrip(w3: Web3, quoter, eth_in: int, token: str, fees=(500,3000,10000)) -> Optional[int]:
    best = None
    for fee in fees:
        try:
            out = int(quoter.functions.quoteExactInputSingle(WETH9, token, fee, eth_in, 0).call()[0])
            back = int(quoter.functions.quoteExactInputSingle(token, WETH9, fee, out, 0).call()[0])
            best = max(best or 0, back)
        except Exception:
            continue
    return best

def _try_v3_twohop_roundtrip(w3: Web3, quoter, eth_in: int, token: str) -> Optional[int]:
    best = None
    for f1 in (500,3000,10000):
        for f2 in (500,3000,10000):
            try:
                u = int(quoter.functions.quoteExactInputSingle(WETH9, USDC, f1, eth_in, 0).call()[0])
                t = int(quoter.functions.quoteExactInputSingle(USDC, token, f2, u, 0).call()[0])
                u2 = int(quoter.functions.quoteExactInputSingle(token, USDC, f2, t, 0).call()[0])
                b  = int(quoter.functions.quoteExactInputSingle(USDC, WETH9, f1, u2, 0).call()[0])
                best = max(best or 0, b)
            except Exception:
                continue
    return best

# --------- Gas helpers ----------
def _get_base_and_fees(w3: Web3, priority_gwei: int) -> Tuple[int, int]:
    base = w3.eth.gas_price  # simple approximation; for 1559 blocks you could sample baseFee
    max_priority = Web3.to_wei(priority_gwei, "gwei")
    max_fee = base + max_priority
    return max_fee, max_priority

# --------- Public: basic/legacy EV (kept) ----------
def estimate_ev_wei(
    w3: Web3, victim_tx, *, priority_fee_gwei: int = 1
) -> Optional[Tuple[int, int, int, int]]:
    """Legacy estimator that only handles a couple of happy paths.
    Returns (ev_wei, gas_wei, my_eth_in, est_eth_back) or None.
    """
    try:
        intent = decode_swap_intent(w3, victim_tx)
        if not intent or not intent.token_out:
            return None
        # Require ETH-in for legacy path
        if not intent.amount_in_wei and int(victim_tx.value or 0) == 0:
            return None

        # Use a very small probe proportional to victim
        victim_in = int(intent.amount_in_wei or victim_tx.value or 0)
        my_in = max(Web3.to_wei(0.02, "ether"), victim_in // 100)  # 1% of victim, min 0.02
        my_in = min(my_in, Web3.to_wei(1.2, "ether"))
        token = intent.token_out

        quoter = w3.eth.contract(address=UNISWAP_V3_QUOTERV2, abi=QUOTER_V2_ABI)
        best_back = 0
        v3 = _try_v3_direct_roundtrip(w3, quoter, my_in, token)
        if v3: best_back = max(best_back, v3)
        v2 = _try_v2_roundtrip(w3, UNISWAP_V2_ROUTER, my_in, token)
        if v2: best_back = max(best_back, v2)
        if best_back <= 0:
            return None

        max_fee, _ = _get_base_and_fees(w3, priority_fee_gwei)
        gas_bundle = 65_000 + 70_000 + 250_000 + 70_000 + 250_000
        gas_wei = gas_bundle * max_fee
        ev_wei = best_back - my_in - gas_wei
        return ev_wei, gas_wei, my_in, best_back
    except Exception:
        return None

# --------- Public: universal EV ----------
def estimate_ev_universal_wei(
    w3: Web3,
    victim_tx,
    *,
    buy_portion_bps: int = 300,  # 3% of victim amount (bounded)
    priority_fee_gwei: int = 1,
) -> Optional[Tuple[int, int, int, int]]:
    """Route-agnostic EV estimator. Returns (ev_wei, gas_wei, my_eth_in, est_back)."""
    try:
        if not victim_tx.to:
            return None

        max_fee, _ = _get_base_and_fees(w3, priority_fee_gwei)
        intent = decode_swap_intent(w3, victim_tx)
        if not intent or not intent.token_out:
            return None

        victim_eth_in = int(victim_tx.value or 0)
        victim_amount_in = int(intent.amount_in_wei or victim_eth_in or 0)
        if victim_amount_in <= 0:
            victim_amount_in = Web3.to_wei(0.1, "ether")
        my_eth_in = max(Web3.to_wei(0.02, "ether"), (victim_amount_in * buy_portion_bps) // 10_000)
        my_eth_in = min(my_eth_in, Web3.to_wei(1.2, "ether"))

        token = intent.token_out        
        best_back = 0

        quoter = w3.eth.contract(address=UNISWAP_V3_QUOTERV2, abi=QUOTER_V2_ABI)

        # Try V3 direct route
        v3_direct = _try_v3_direct_roundtrip(w3, quoter, my_eth_in, token)
        if v3_direct: 
            best_back = max(best_back, v3_direct)
        
        # Try V3 two-hop route
        v3_twohop = _try_v3_twohop_roundtrip(w3, quoter, my_eth_in, token)
        if v3_twohop: 
            best_back = max(best_back, v3_twohop)

        # Try V2 routes
        for v2r in UNISWAP_V2_ROUTERS:
            b = _try_v2_roundtrip(w3, v2r, my_eth_in, token)
            if b: 
                best_back = max(best_back, b)
            
            b2 = _try_v2_roundtrip_twohop(w3, v2r, my_eth_in, token)
            if b2: 
                best_back = max(best_back, b2)

        if best_back <= 0:
            return None

        gas_bundle = 65_000 + 70_000 + 250_000 + 70_000 + 250_000
        gas_wei = gas_bundle * max_fee
        ev_wei = best_back - my_eth_in - gas_wei
        
        # Don't return negative EV - it causes "value must be between" errors  
        if ev_wei <= 0:
            return None
            
        return ev_wei, gas_wei, my_eth_in, best_back
    except Exception:
        return None

# --------- Sandwich bundle builder (simple V3 single-hop) ----------
def build_sandwich_bundle(
    w3: Web3,
    searcher: Account,
    victim_tx_raw: bytes,
    victim_tx,
    token_out: str,
    my_eth_in: int,
    *, fee: int = 3000, priority_fee_gwei: int = 1
) -> Optional[List[bytes]]:
    """Build a (wrap -> approve -> buy -> approve -> victim -> sell) bundle.
    Returns a list of signed raw txs ready for Flashbots bundle submission.
    """
    try:
        chain_id = w3.eth.chain_id
        nonce = w3.eth.get_transaction_count(searcher.address)
        max_fee, max_priority = _get_base_and_fees(w3, priority_fee_gwei)

        weth = w3.eth.contract(address=WETH9, abi=WETH9_ABI)
        erc  = w3.eth.contract(address=token_out, abi=ERC20_ABI)
        router = w3.eth.contract(address=UNISWAP_V3_ROUTER, abi=UNISWAP_V3_ROUTER_ABI)

        # 1) Wrap ETH -> WETH
        wrap_tx = {
            "to": WETH9, "value": my_eth_in, "data": weth.encodeABI(fn_name="deposit"),
            "gas": 65_000, "maxFeePerGas": max_fee, "maxPriorityFeePerGas": max_priority,
            "nonce": nonce, "chainId": chain_id, "type": 2
        }
        signed_wrap = w3.eth.account.sign_transaction(wrap_tx, private_key=searcher.key)
        nonce += 1

        # 2) Approve WETH -> V3 Router
        approve_weth_tx = {
            "to": WETH9, "value": 0,
            "data": weth.encodeABI(fn_name="approve", args=[UNISWAP_V3_ROUTER, my_eth_in]),
            "gas": 70_000, "maxFeePerGas": max_fee, "maxPriorityFeePerGas": max_priority,
            "nonce": nonce, "chainId": chain_id, "type": 2
        }
        signed_approve_weth = w3.eth.account.sign_transaction(approve_weth_tx, private_key=searcher.key)
        nonce += 1

        # 3) Buy: exactInputSingle WETH -> token_out
        params_buy = (
            WETH9, token_out, fee, searcher.address, int(time.time()) + 600,
            my_eth_in, 0, 0
        )
        buy_tx = {
            "to": UNISWAP_V3_ROUTER, "value": 0,
            "data": router.encodeABI(fn_name="exactInputSingle", args=[{
                "tokenIn": params_buy[0], "tokenOut": params_buy[1], "fee": params_buy[2],
                "recipient": params_buy[3], "deadline": params_buy[4],
                "amountIn": params_buy[5], "amountOutMinimum": params_buy[6],
                "sqrtPriceLimitX96": params_buy[7]
            }]),
            "gas": 250_000, "maxFeePerGas": max_fee, "maxPriorityFeePerGas": max_priority,
            "nonce": nonce, "chainId": chain_id, "type": 2
        }
        signed_buy = w3.eth.account.sign_transaction(buy_tx, private_key=searcher.key)
        nonce += 1

        # 4) Approve token_out -> V3 Router (for selling back)
        approve_out_tx = {
            "to": token_out, "value": 0,
            "data": erc.encodeABI(fn_name="approve", args=[UNISWAP_V3_ROUTER, 2**256 - 1]),
            "gas": 70_000, "maxFeePerGas": max_fee, "maxPriorityFeePerGas": max_priority,
            "nonce": nonce, "chainId": chain_id, "type": 2
        }
        signed_approve_out = w3.eth.account.sign_transaction(approve_out_tx, private_key=searcher.key)
        nonce += 1

        victim_raw = victim_tx_raw  # already signed by victim

        # 5) Sell back token_out -> WETH (exactInputSingle)
        # For sell amount we trust the router to spend the balance; here we pass a large amountIn via allowance and set amountIn=balance via balanceOf read.
        # To keep it simple here, we'll set a big amountIn and rely on allowance & router to pull exact balance.
        balance = int(erc.functions.balanceOf(searcher.address).call())
        if balance == 0:
            # Fallback to a placeholder; MEV logic would normally simulate exact amount
            balance = 1
        params_sell = (
            token_out, WETH9, fee, searcher.address, int(time.time()) + 600,
            balance, 0, 0
        )
        sell_tx = {
            "to": UNISWAP_V3_ROUTER, "value": 0,
            "data": router.encodeABI(fn_name="exactInputSingle", args=[{
                "tokenIn": params_sell[0], "tokenOut": params_sell[1], "fee": params_sell[2],
                "recipient": params_sell[3], "deadline": params_sell[4],
                "amountIn": params_sell[5], "amountOutMinimum": params_sell[6],
                "sqrtPriceLimitX96": params_sell[7]
            }]),
            "gas": 250_000, "maxFeePerGas": max_fee, "maxPriorityFeePerGas": max_priority,
            "nonce": nonce, "chainId": chain_id, "type": 2
        }
        signed_sell = w3.eth.account.sign_transaction(sell_tx, private_key=searcher.key)

        return [
            signed_wrap.rawTransaction,
            signed_approve_weth.rawTransaction,
            signed_buy.rawTransaction,
            signed_approve_out.rawTransaction,
            victim_raw,
            signed_sell.rawTransaction,
        ]
    except Exception:
        return None

# --------- Detection helpers ----------
def is_uniswap_swap(tx) -> bool:
    if not tx.to or not tx.input or len(str(tx.input)) < 10:
        return False
    try:
        to = Web3.to_checksum_address(tx.to)
    except Exception:
        return False
    # Any of the known routers qualifies
    if to in KNOWN_ROUTERS:
        return True
    # If the call has ETH value and goes to a contract, we let the caller decide
    return False

def describe_tx(tx) -> str:
    to_name = get_router_name(tx.to)
    return f"To: {to_name} ({short_addr(tx.to)}), Value: {Web3.from_wei(int(tx.value or 0), 'ether')} ETH, Sig: {sig4(tx.input)}"

__all__ = [
    "UNISWAP_V2_ROUTER", "UNISWAP_V3_ROUTER", "UNISWAP_V3_QUOTERV2",
    "WETH9", "USDC",
    "KNOWN_ROUTERS", "get_router_name", "describe_tx",
    "UNISWAP_V2_ROUTER_ABI", "UNISWAP_V3_ROUTER_ABI", "QUOTER_V2_ABI", "ERC20_ABI", "WETH9_ABI",
    "is_uniswap_swap", "estimate_ev_wei", "estimate_ev_universal_wei",
    "decode_swap_intent", "build_sandwich_bundle", "sig4",
]
