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

# Sushiswap
SUSHISWAP_V2_ROUTER = Web3.to_checksum_address("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F")
SUSHISWAP_V3_ROUTER = Web3.to_checksum_address("0x2E6cd2d30aa43f40aa81619ff4b6E0a41479B13f")  # SushiV3Router
SUSHISWAP_ROUTER_V2 = Web3.to_checksum_address("0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506")  # SushiRouterV2

# 0x Protocol
ZEROX_EX_V3         = Web3.to_checksum_address("0xDef1C0ded9bec7F1a1670819833240f027b25EfF")  # 0x Exchange Proxy v3
ZEROX_EX_V4         = Web3.to_checksum_address("0xDef1C0ded9bec7F1a1670819833240f027b25EfF")  # Same address for v4

# Curve
CURVE_ROUTER        = Web3.to_checksum_address("0xfA9a30350048B2BF66865ee20363067c66f67e58")  # Curve.fi Router v1.0
CURVE_TRICRYPTO     = Web3.to_checksum_address("0x80466c64868E1ab14a1Ddf27A676C3fcBE638Fe5")  # TriCrypto2 Pool

# Balancer
BALANCER_VAULT      = Web3.to_checksum_address("0xBA12222222228d8Ba445958a75a0704d566BF2C8")

# Aggregators and other DEXs
ONEINCH_V5          = Web3.to_checksum_address("0x1111111254EEB25477B68fb85Ed929f73A960582")
ONEINCH_V6          = Web3.to_checksum_address("0x111111125421cA6dc452d289314280a0f8842A65")  # 1inch v6
PARASWAP_V5         = Web3.to_checksum_address("0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57")
PARASWAP_V6         = Web3.to_checksum_address("0x216B4B4Ba9F3e719726886d34a177484278Bfcae")  # ParaSwap v6
COW_PROTOCOL        = Web3.to_checksum_address("0x9008D19f58AAbD9eD0D60971565AA8510560ab41")  # CoW Protocol Settlement
MATCHA              = Web3.to_checksum_address("0xDef1C0ded9bec7F1a1670819833240f027b25EfF")  # 0x-based

# Token addresses
WETH9               = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
USDC                = Web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606EB48")
USDT                = Web3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7")
DAI                 = Web3.to_checksum_address("0x6B175474E89094C44Da98b954EedeAC495271d0F")

KNOWN_ROUTERS: Dict[str, str] = {
    UNISWAP_V2_ROUTER: "Uniswap V2",
    UNISWAP_V3_ROUTER: "Uniswap V3",
    UNISWAP_V3_PERIPH: "Uniswap V3 Periphery",
    UNIVERSAL_ROUTER:  "Uniswap Universal Router",
    SUSHISWAP_V2_ROUTER: "Sushiswap V2",
    SUSHISWAP_V3_ROUTER: "Sushiswap V3",
    SUSHISWAP_ROUTER_V2: "Sushiswap Router V2", 
    ONEINCH_V5:        "1inch v5",
    ONEINCH_V6:        "1inch v6",
    ZEROX_EX_V3:       "0x Exchange v3",
    ZEROX_EX_V4:       "0x Exchange v4",
    PARASWAP_V5:       "ParaSwap v5",
    PARASWAP_V6:       "ParaSwap v6",
    CURVE_ROUTER:      "Curve Router",
    CURVE_TRICRYPTO:   "Curve TriCrypto",
    BALANCER_VAULT:    "Balancer Vault",
    COW_PROTOCOL:      "CoW Protocol",
    MATCHA:            "Matcha (0x)",
}

UNISWAP_V2_ROUTERS = {UNISWAP_V2_ROUTER}
UNISWAP_V3_ROUTERS = {UNISWAP_V3_ROUTER, UNISWAP_V3_PERIPH}
SUSHISWAP_V2_ROUTERS = {SUSHISWAP_V2_ROUTER, SUSHISWAP_ROUTER_V2}
SUSHISWAP_V3_ROUTERS = {SUSHISWAP_V3_ROUTER}
ONEINCH_ROUTERS    = {ONEINCH_V5, ONEINCH_V6}
ZEROX_ROUTERS      = {ZEROX_EX_V3, ZEROX_EX_V4, MATCHA}
PARASWAP_ROUTERS   = {PARASWAP_V5, PARASWAP_V6}
CURVE_ROUTERS      = {CURVE_ROUTER, CURVE_TRICRYPTO}
BALANCER_ROUTERS   = {BALANCER_VAULT}
COW_ROUTERS        = {COW_PROTOCOL}

# All V2-like routers that use the same ABI
ALL_V2_ROUTERS = UNISWAP_V2_ROUTERS | SUSHISWAP_V2_ROUTERS

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

# Curve Pool ABI (simplified for common functions)
CURVE_POOL_ABI = [
    {"type":"function","name":"exchange","stateMutability":"payable",
     "inputs":[
        {"name":"i","type":"int128"},
        {"name":"j","type":"int128"},
        {"name":"dx","type":"uint256"},
        {"name":"min_dy","type":"uint256"}],
     "outputs":[{"name":"","type":"uint256"}]},
    {"type":"function","name":"exchange_underlying","stateMutability":"payable",
     "inputs":[
        {"name":"i","type":"int128"},
        {"name":"j","type":"int128"},
        {"name":"dx","type":"uint256"},
        {"name":"min_dy","type":"uint256"}],
     "outputs":[{"name":"","type":"uint256"}]},
    {"type":"function","name":"get_dy","stateMutability":"view",
     "inputs":[
        {"name":"i","type":"int128"},
        {"name":"j","type":"int128"},
        {"name":"dx","type":"uint256"}],
     "outputs":[{"name":"","type":"uint256"}]},
    {"type":"function","name":"get_dy_underlying","stateMutability":"view",
     "inputs":[
        {"name":"i","type":"int128"},
        {"name":"j","type":"int128"},
        {"name":"dx","type":"uint256"}],
     "outputs":[{"name":"","type":"uint256"}]},
    {"type":"function","name":"coins","stateMutability":"view",
     "inputs":[{"name":"arg0","type":"uint256"}],
     "outputs":[{"name":"","type":"address"}]},
    {"type":"function","name":"underlying_coins","stateMutability":"view",
     "inputs":[{"name":"arg0","type":"uint256"}],
     "outputs":[{"name":"","type":"address"}]},
]

# Curve Router ABI
CURVE_ROUTER_ABI = [
    {"type":"function","name":"exchange","stateMutability":"payable",
     "inputs":[
        {"name":"_route","type":"address[9]"},
        {"name":"_swap_params","type":"uint256[3][4]"},
        {"name":"_amount","type":"uint256"},
        {"name":"_expected","type":"uint256"}],
     "outputs":[{"name":"","type":"uint256"}]},
    {"type":"function","name":"get_exchange_amount","stateMutability":"view",
     "inputs":[
        {"name":"_pool","type":"address"},
        {"name":"_from","type":"address"},
        {"name":"_to","type":"address"},
        {"name":"_amount","type":"uint256"}],
     "outputs":[{"name":"","type":"uint256"}]},
]

# 0x v4 Exchange ABI (updated)
ZEROX_V4_ABI = [
    {"type":"function","name":"transformERC20","stateMutability":"payable",
     "inputs":[
        {"name":"inputToken","type":"address"},
        {"name":"outputToken","type":"address"},
        {"name":"inputTokenAmount","type":"uint256"},
        {"name":"minOutputTokenAmount","type":"uint256"},
        {"name":"transformations","type":"tuple[]","components":[
            {"name":"deploymentNonce","type":"uint32"},
            {"name":"data","type":"bytes"}]}],
     "outputs":[{"name":"outputTokenAmount","type":"uint256"}]},
    {"type":"function","name":"sellToUniswap","stateMutability":"payable",
     "inputs":[
        {"name":"tokens","type":"address[]"},
        {"name":"sellAmount","type":"uint256"},
        {"name":"minBuyAmount","type":"uint256"},
        {"name":"isSushi","type":"bool"}],
     "outputs":[{"name":"buyAmount","type":"uint256"}]},
    {"type":"function","name":"sellToPancakeSwap","stateMutability":"payable",
     "inputs":[
        {"name":"tokens","type":"address[]"},
        {"name":"sellAmount","type":"uint256"},
        {"name":"minBuyAmount","type":"uint256"}],
     "outputs":[{"name":"buyAmount","type":"uint256"}]},
]

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

    # v2 (Uniswap and Sushiswap use same ABI)
    if to in ALL_V2_ROUTERS:
        router = w3.eth.contract(address=to, abi=UNISWAP_V2_ROUTER_ABI)
        try:
            fn, args = router.decode_function_input(tx.input)
            name = fn.fn_name
            path = list(map(Web3.to_checksum_address, args.get("path") or args.get(2) or []))
            amt_in = None
            if "amountIn" in args: amt_in = int(args["amountIn"])
            elif name.startswith("swapExactETHFor"): amt_in = int(tx.value or 0)
            
            # Determine DEX type
            dex_kind = "v2"
            if to in SUSHISWAP_V2_ROUTERS:
                dex_kind = "sushiswap_v2"
                
            return SwapIntent(
                token_in=path[0] if path else None,
                token_out=path[-1] if path else None,
                amount_in_wei=amt_in,
                kind=dex_kind, path_v2=path
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

    # 0x v4 protocol detection
    zerox_intent = detect_0x_v4_swap(w3, tx)
    if zerox_intent:
        return zerox_intent

    # Universal Router: try to decode commands (signature 0x3593564c)
    if to == UNIVERSAL_ROUTER and s4 == "0x3593564c":
        try:
            # Parse Universal Router execute function
            # execute(bytes commands, bytes[] inputs, uint256 deadline)
            data_bytes = bytes.fromhex(data_hex)
            
            # Skip function selector (first 4 bytes)
            params_data = data_bytes[4:]
            
            # Try to extract token addresses from the inputs
            token_addresses = []
            
            # Scan for token addresses in the calldata
            for i in range(0, len(params_data) - 20):
                potential_addr = "0x" + params_data[i:i+20].hex()
                try:
                    addr = Web3.to_checksum_address(potential_addr)
                    # Filter for likely token addresses (not zero, not router itself)
                    if (not addr.endswith("0000000000000000000000000000000000000000") and 
                        addr != UNIVERSAL_ROUTER and addr != WETH9 and 
                        len(addr) == 42):
                        token_addresses.append(addr)
                except Exception:
                    continue
            
            # Remove duplicates while preserving order
            seen = set()
            unique_tokens = []
            for addr in token_addresses:
                if addr not in seen:
                    seen.add(addr)
                    unique_tokens.append(addr)
            
            if int(tx.value or 0) > 0:
                # ETH->token swap
                token_in = WETH9
                token_out = None
                
                # Find the most likely output token
                # Priority: first non-WETH token found
                for addr in unique_tokens:
                    if addr != WETH9:
                        token_out = addr
                        break
                
                # If no token found, check for common tokens in hex data
                if not token_out:
                    common_tokens = [
                        USDC,
                        "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
                        "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
                        "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",  # WBTC
                    ]
                    for token in common_tokens:
                        if token.lower().replace("0x", "") in data_hex:
                            token_out = token
                            break
                
                # Last resort fallback
                if not token_out:
                    token_out = USDC
                    
                return SwapIntent(
                    token_in=token_in,
                    token_out=token_out,
                    amount_in_wei=int(tx.value),
                    kind="universal"
                )
            else:
                # Token->token or token->ETH swap
                if len(unique_tokens) >= 2:
                    # Take first two distinct tokens
                    token_in = unique_tokens[0]
                    token_out = unique_tokens[1] if unique_tokens[1] != token_in else (unique_tokens[2] if len(unique_tokens) > 2 else WETH9)
                    
                    return SwapIntent(
                        token_in=token_in,
                        token_out=token_out,
                        amount_in_wei=None,  # Can't determine from Universal Router easily
                        kind="universal"
                    )
                    
        except Exception:
            pass
    
    # V3 Periphery multicall (signature 0x5ae401dc)  
    if to == UNISWAP_V3_PERIPH and s4 == "0x5ae401dc":
        try:
            # Enhanced multicall parsing for V3 Periphery
            data_bytes = bytes.fromhex(data_hex)
            
            # Try to decode multicall structure
            # multicall(bytes[] data) or multicall(uint256 deadline, bytes[] data)
            
            # Scan for token addresses with improved filtering
            potential_tokens = []
            
            # Look for exactInputSingle function calls (0x414bf389)
            exact_input_single_sig = "414bf389"
            if exact_input_single_sig in data_hex:
                # Find positions of exactInputSingle calls
                pos = 0
                while True:
                    pos = data_hex.find(exact_input_single_sig, pos)
                    if pos == -1:
                        break
                    
                    # Extract tokens from exactInputSingle parameters
                    # Parameters: tokenIn, tokenOut, fee, recipient, deadline, amountIn, amountOutMinimum, sqrtPriceLimitX96
                    try:
                        param_start = pos + 8  # Skip function signature
                        if param_start + 128 <= len(data_hex):  # Ensure we have enough data for 2 addresses (64 chars each)
                            token_in_hex = data_hex[param_start:param_start+64]
                            token_out_hex = data_hex[param_start+64:param_start+128]
                            
                            # Extract addresses (last 40 chars of each 64-char parameter)
                            token_in_addr = "0x" + token_in_hex[-40:]
                            token_out_addr = "0x" + token_out_hex[-40:]
                            
                            for addr_hex in [token_in_addr, token_out_addr]:
                                try:
                                    addr = Web3.to_checksum_address(addr_hex)
                                    if not addr.endswith("0000000000000000000000000000000000000000"):
                                        potential_tokens.append(addr)
                                except Exception:
                                    continue
                    except Exception:
                        pass
                    
                    pos += 8
            
            # Also scan generally for addresses
            general_addrs = _scan_addresses_from_calldata(data_hex)
            
            # Filter addresses to likely tokens
            likely_tokens = []
            excluded_addrs = {UNISWAP_V3_PERIPH, UNISWAP_V3_ROUTER, UNIVERSAL_ROUTER}
            
            for addr in potential_tokens + general_addrs:
                if (addr not in excluded_addrs and 
                    not addr.endswith("0000000000000000000000000000000000000000") and
                    len(addr) == 42 and addr.startswith("0x")):
                    if addr not in likely_tokens:  # Avoid duplicates
                        likely_tokens.append(addr)
            
            if int(tx.value or 0) > 0:
                # ETH->token swap
                token_in = WETH9
                token_out = None
                
                # Priority: tokens found in exactInputSingle calls first
                for addr in likely_tokens:
                    if addr != WETH9:
                        token_out = addr
                        break
                
                # Check for common tokens if nothing found
                if not token_out:
                    common_tokens = [
                        USDC,
                        "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
                        "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
                        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC (duplicate check)
                    ]
                    for token in common_tokens:
                        if token.lower().replace("0x", "") in data_hex:
                            token_out = token
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
            else:
                # Token->token or token->ETH swap
                if len(likely_tokens) >= 2:
                    # For non-ETH swaps, try to identify input/output tokens
                    token_in = likely_tokens[0]
                    token_out = likely_tokens[1]
                    
                    # If one of them is WETH, it's likely the output for a token->ETH swap
                    if WETH9 in likely_tokens:
                        weth_index = likely_tokens.index(WETH9)
                        non_weth_tokens = [t for t in likely_tokens if t != WETH9]
                        if non_weth_tokens:
                            token_in = non_weth_tokens[0]
                            token_out = WETH9
                    
                    return SwapIntent(
                        token_in=token_in,
                        token_out=token_out,
                        amount_in_wei=None,  # Can't easily determine from multicall
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

# --------- Curve stablecoin arbitrage helpers ----------
def get_curve_stablecoin_pools() -> Dict[str, Dict]:
    """
    Map of major Curve stablecoin pools with their addresses and token indices.
    Returns dict mapping pool names to pool info.
    """
    return {
        "3pool": {
            "address": "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7",
            "tokens": {
                DAI: 0,
                USDC: 1, 
                USDT: 2
            }
        },
        "tricrypto2": {
            "address": CURVE_TRICRYPTO,
            "tokens": {
                USDT: 0,
                WETH9: 2  # Note: WBTC is index 1, we focus on ETH-relevant pairs
            }
        }
    }

def _try_curve_stablecoin_arbitrage(w3: Web3, eth_in: int, token: str) -> Optional[int]:
    """
    Try Curve stablecoin arbitrage routes for better pricing on stable swaps.
    Particularly effective for USDC, USDT, DAI swaps.
    """
    if token not in {USDC, USDT, DAI}:
        return None
        
    try:
        pools = get_curve_stablecoin_pools()
        best_back = 0
        
        # Try 3pool for stablecoin swaps via USDC
        if "3pool" in pools and token in pools["3pool"]["tokens"]:
            pool_info = pools["3pool"]
            pool = w3.eth.contract(address=pool_info["address"], abi=CURVE_POOL_ABI)
            
            try:
                # ETH -> WETH -> USDC via Uniswap, then USDC -> target token via Curve
                quoter = w3.eth.contract(address=UNISWAP_V3_QUOTERV2, abi=QUOTER_V2_ABI)
                
                # Step 1: ETH -> USDC via Uniswap V3
                usdc_out = int(quoter.functions.quoteExactInputSingle(WETH9, USDC, 500, eth_in, 0).call()[0])
                
                if token == USDC:
                    # Direct USDC, just return the amount
                    token_out = usdc_out
                else:
                    # Step 2: USDC -> target token via Curve
                    usdc_idx = pool_info["tokens"][USDC]  # 1
                    token_idx = pool_info["tokens"][token]  # 0 for DAI, 2 for USDT
                    
                    token_out = int(pool.functions.get_dy(usdc_idx, token_idx, usdc_out).call())
                
                if token_out > 0:
                    # Step 3: target token -> USDC -> ETH (reverse path)
                    if token == USDC:
                        usdc_back = token_out
                    else:
                        usdc_back = int(pool.functions.get_dy(pool_info["tokens"][token], pool_info["tokens"][USDC], token_out).call())
                    
                    # Step 4: USDC -> ETH via Uniswap
                    eth_back = int(quoter.functions.quoteExactInputSingle(USDC, WETH9, 500, usdc_back, 0).call()[0])
                    
                    best_back = max(best_back, eth_back)
                    
            except Exception:
                pass
                
        # Try TriCrypto2 for ETH-based swaps
        if "tricrypto2" in pools and token == USDT:
            pool_info = pools["tricrypto2"]
            pool = w3.eth.contract(address=pool_info["address"], abi=CURVE_POOL_ABI)
            
            try:
                # Direct ETH -> USDT and back via TriCrypto2
                eth_idx = pool_info["tokens"][WETH9]  # 2
                usdt_idx = pool_info["tokens"][USDT]  # 0
                
                # Step 1: ETH -> USDT via Curve
                usdt_out = int(pool.functions.get_dy(eth_idx, usdt_idx, eth_in).call())
                
                # Step 2: USDT -> ETH via Curve
                if usdt_out > 0:
                    eth_back = int(pool.functions.get_dy(usdt_idx, eth_idx, usdt_out).call())
                    best_back = max(best_back, eth_back)
                    
            except Exception:
                pass
        
        return best_back if best_back > 0 else None
        
    except Exception:
        return None

def detect_0x_v4_swap(w3: Web3, tx) -> Optional[SwapIntent]:
    """
    Detect 0x v4 protocol swaps with enhanced function signatures.
    """
    to = Web3.to_checksum_address(tx.to)
    data_hex = _hex_input(tx)
    s4 = "0x" + data_hex[:8]
    
    if to in ZEROX_ROUTERS:
        try:
            # transformERC20 signature: 0x415565b0
            if s4 == "0x415565b0":
                contract = w3.eth.contract(address=to, abi=ZEROX_V4_ABI)
                fn, args = contract.decode_function_input(tx.input)
                
                input_token = Web3.to_checksum_address(args.get("inputToken"))
                output_token = Web3.to_checksum_address(args.get("outputToken"))
                input_amount = int(args.get("inputTokenAmount", tx.value or 0))
                
                return SwapIntent(
                    token_in=input_token,
                    token_out=output_token,
                    amount_in_wei=input_amount,
                    kind="0x_v4"
                )
            
            # sellToUniswap signature: 0xd9627aa4
            elif s4 == "0xd9627aa4":
                contract = w3.eth.contract(address=to, abi=ZEROX_V4_ABI)
                fn, args = contract.decode_function_input(tx.input)
                
                tokens = args.get("tokens", [])
                sell_amount = int(args.get("sellAmount", tx.value or 0))
                
                if len(tokens) >= 2:
                    return SwapIntent(
                        token_in=Web3.to_checksum_address(tokens[0]),
                        token_out=Web3.to_checksum_address(tokens[-1]),
                        amount_in_wei=sell_amount,
                        kind="0x_v4"
                    )
            
        except Exception:
            pass
    
    return None

# --------- Token validation helpers ----------
def validate_token_liquidity(w3: Web3, token: str, min_liquidity_wei: int = None) -> bool:
    """
    Validate if a token has sufficient liquidity for sandwich attacks.
    Returns True if token passes validation, False otherwise.
    """
    if min_liquidity_wei is None:
        min_liquidity_wei = Web3.to_wei(5, "ether")  # Default minimum 5 ETH liquidity
        
    try:
        # Check if token has valid contract code
        code = w3.eth.get_code(token)
        if len(code) <= 2:  # No contract code (just "0x")
            return False
            
        # Check V3 pool liquidity for common fee tiers
        quoter = w3.eth.contract(address=UNISWAP_V3_QUOTERV2, abi=QUOTER_V2_ABI)
        
        test_amount = Web3.to_wei(0.1, "ether")  # Test with 0.1 ETH
        max_liquidity = 0
        
        for fee in [500, 3000, 10000]:
            try:
                # Try to get quote for WETH -> token
                result = quoter.functions.quoteExactInputSingle(
                    WETH9, token, fee, test_amount, 0
                ).call()
                if result[0] > 0:  # If we get a valid quote
                    # Try reverse quote to check both directions
                    reverse_result = quoter.functions.quoteExactInputSingle(
                        token, WETH9, fee, result[0], 0
                    ).call()
                    if reverse_result[0] > 0:
                        max_liquidity = max(max_liquidity, reverse_result[0])
            except Exception:
                continue
                
        # Also check V2 liquidity
        try:
            router = w3.eth.contract(address=UNISWAP_V2_ROUTER, abi=UNISWAP_V2_ROUTER_ABI)
            amounts = router.functions.getAmountsOut(test_amount, [WETH9, token]).call()
            if len(amounts) >= 2 and amounts[-1] > 0:
                # Try reverse to check liquidity depth
                reverse_amounts = router.functions.getAmountsOut(amounts[-1], [token, WETH9]).call()
                if len(reverse_amounts) >= 2 and reverse_amounts[-1] > 0:
                    max_liquidity = max(max_liquidity, reverse_amounts[-1])
        except Exception:
            pass
            
        # Token passes if it has sufficient liquidity in at least one pool
        return max_liquidity >= min_liquidity_wei
        
    except Exception:
        return False

def is_token_blacklisted(token: str) -> bool:
    """
    Check if token is in blacklist of known problematic tokens.
    Add tokens here that are known to cause issues (rebasing, fee-on-transfer, etc.)
    """
    token = token.lower()
    
    # Known problematic tokens (add addresses as needed)
    blacklisted_tokens = {
        # Add problematic token addresses here
        # Example: "0x..." for tokens with transfer fees, rebasing mechanics, etc.
    }
    
    return token in blacklisted_tokens

# --------- Pool liquidity and sizing helpers ----------
def get_pool_liquidity_depth(w3: Web3, token_a: str, token_b: str) -> Dict[str, int]:
    """
    Get liquidity depth across different DEX pools for optimal sizing.
    Returns dict with pool info: {'v2_liquidity': int, 'v3_500': int, 'v3_3000': int, 'v3_10000': int}
    """
    liquidity_info = {
        'v2_liquidity': 0,
        'v3_500': 0,
        'v3_3000': 0,  
        'v3_10000': 0,
        'total_liquidity': 0
    }
    
    try:
        # Check V2 liquidity
        router = w3.eth.contract(address=UNISWAP_V2_ROUTER, abi=UNISWAP_V2_ROUTER_ABI)
        test_amount = Web3.to_wei(1, "ether")  # Test with 1 ETH
        try:
            amounts = router.functions.getAmountsOut(test_amount, [token_a, token_b]).call()
            if len(amounts) >= 2 and amounts[-1] > 0:
                # Estimate liquidity depth by testing progressively larger amounts
                for multiplier in [1, 5, 10]:
                    test_larger = test_amount * multiplier
                    try:
                        larger_amounts = router.functions.getAmountsOut(test_larger, [token_a, token_b]).call()
                        if len(larger_amounts) >= 2:
                            # If we can still get reasonable output, pool has depth
                            expected_output = amounts[-1] * multiplier
                            actual_output = larger_amounts[-1]
                            # If actual output is > 80% of expected, good liquidity
                            if actual_output > (expected_output * 8) // 10:
                                liquidity_info['v2_liquidity'] = test_larger
                            else:
                                break
                    except Exception:
                        break
        except Exception:
            pass
        
        # Check V3 liquidity for different fee tiers
        quoter = w3.eth.contract(address=UNISWAP_V3_QUOTERV2, abi=QUOTER_V2_ABI)
        for fee in [500, 3000, 10000]:
            try:
                test_amount = Web3.to_wei(1, "ether")
                result = quoter.functions.quoteExactInputSingle(token_a, token_b, fee, test_amount, 0).call()
                if result[0] > 0:
                    # Test deeper liquidity
                    for multiplier in [1, 3, 5, 10]:
                        test_larger = test_amount * multiplier
                        try:
                            larger_result = quoter.functions.quoteExactInputSingle(token_a, token_b, fee, test_larger, 0).call()
                            if larger_result[0] > 0:
                                expected_output = result[0] * multiplier
                                actual_output = larger_result[0]
                                # Check for reasonable price impact (< 20%)
                                if actual_output > (expected_output * 8) // 10:
                                    liquidity_info[f'v3_{fee}'] = test_larger
                                else:
                                    break
                        except Exception:
                            break
            except Exception:
                continue
        
        # Calculate total available liquidity
        liquidity_info['total_liquidity'] = max(
            liquidity_info['v2_liquidity'],
            liquidity_info['v3_500'], 
            liquidity_info['v3_3000'],
            liquidity_info['v3_10000']
        )
        
    except Exception:
        pass
        
    return liquidity_info

def calculate_optimal_position_size(
    w3: Web3, 
    victim_tx, 
    intent: SwapIntent,
    liquidity_info: Dict[str, int]
) -> int:
    """
    Calculate optimal sandwich position size based on:
    1. Victim transaction size
    2. Pool liquidity depth  
    3. Price impact analysis
    4. Risk management limits
    """
    try:
        victim_eth_in = int(victim_tx.value or 0)
        victim_amount_in = int(intent.amount_in_wei or victim_eth_in or 0)
        
        if victim_amount_in <= 0:
            victim_amount_in = Web3.to_wei(0.1, "ether")
            
        # Base sizing: start with percentage of victim amount
        base_size = victim_amount_in // 20  # 5% of victim
        
        # Adjust based on victim transaction size
        if victim_amount_in >= Web3.to_wei(10, "ether"):
            # Large victim -> smaller relative size to avoid excessive price impact
            base_size = victim_amount_in // 50  # 2% of large victims
        elif victim_amount_in <= Web3.to_wei(0.1, "ether"):
            # Small victim -> larger relative size for better profit margins  
            base_size = max(base_size, Web3.to_wei(0.05, "ether"))  # Min 0.05 ETH
        
        # Adjust based on pool liquidity
        total_liquidity = liquidity_info.get('total_liquidity', 0)
        if total_liquidity > 0:
            # Size as percentage of available liquidity (max 5% of pool liquidity)
            liquidity_based_size = total_liquidity // 20
            
            # Take the smaller of victim-based and liquidity-based sizing
            base_size = min(base_size, liquidity_based_size)
            
            # For very deep liquidity, can be more aggressive
            if total_liquidity >= Web3.to_wei(100, "ether"):
                base_size = min(base_size * 2, Web3.to_wei(2, "ether"))
        
        # Apply absolute limits
        min_size = Web3.to_wei(0.02, "ether")  # Minimum viable size
        max_size = Web3.to_wei(3, "ether")     # Maximum risk limit
        
        # Ensure we don't exceed victim size (would be obvious)
        max_size = min(max_size, victim_amount_in)
        
        optimal_size = max(min_size, min(base_size, max_size))
        
        return int(optimal_size)
        
    except Exception:
        # Fallback to conservative sizing
        return Web3.to_wei(0.05, "ether")

def estimate_price_impact(w3: Web3, token_in: str, token_out: str, amount_in: int) -> float:
    """
    Estimate price impact of a swap to optimize position sizing.
    Returns price impact as a decimal (0.01 = 1%)
    """
    try:
        quoter = w3.eth.contract(address=UNISWAP_V3_QUOTERV2, abi=QUOTER_V2_ABI)
        
        # Get quote for small amount (baseline price)
        small_amount = amount_in // 100  # 1% of actual amount
        if small_amount == 0:
            small_amount = Web3.to_wei(0.01, "ether")
            
        best_baseline_rate = 0
        best_actual_rate = 0
        
        # Check across fee tiers for best rates
        for fee in [500, 3000, 10000]:
            try:
                # Baseline rate
                small_result = quoter.functions.quoteExactInputSingle(token_in, token_out, fee, small_amount, 0).call()
                if small_result[0] > 0:
                    baseline_rate = small_result[0] / small_amount
                    best_baseline_rate = max(best_baseline_rate, baseline_rate)
                
                # Actual rate
                actual_result = quoter.functions.quoteExactInputSingle(token_in, token_out, fee, amount_in, 0).call()
                if actual_result[0] > 0:
                    actual_rate = actual_result[0] / amount_in
                    best_actual_rate = max(best_actual_rate, actual_rate)
                    
            except Exception:
                continue
        
        if best_baseline_rate > 0 and best_actual_rate > 0:
            price_impact = (best_baseline_rate - best_actual_rate) / best_baseline_rate
            return max(0, price_impact)  # Ensure non-negative
            
    except Exception:
        pass
    
    return 0.0  # Default to no impact if calculation fails

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
        
        # Try Curve stablecoin arbitrage for better stable token pricing
        curve_back = _try_curve_stablecoin_arbitrage(w3, my_in, token)
        if curve_back: best_back = max(best_back, curve_back)
        
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

        # Try V2 routes (Uniswap and Sushiswap)
        for v2r in ALL_V2_ROUTERS:
            b = _try_v2_roundtrip(w3, v2r, my_eth_in, token)
            if b: 
                best_back = max(best_back, b)
            
            b2 = _try_v2_roundtrip_twohop(w3, v2r, my_eth_in, token)
            if b2: 
                best_back = max(best_back, b2)
                
        # Try Curve stablecoin arbitrage for better stable token pricing
        curve_back = _try_curve_stablecoin_arbitrage(w3, my_eth_in, token)
        if curve_back:
            best_back = max(best_back, curve_back)

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

# --------- Dynamic EV estimator with optimal sizing ----------
def estimate_ev_dynamic_wei(
    w3: Web3,
    victim_tx,
    *,
    priority_fee_gwei: int = 1,
) -> Optional[Tuple[int, int, int, int]]:
    """
    Advanced EV estimator with dynamic position sizing based on pool liquidity and price impact.
    Returns (ev_wei, gas_wei, my_eth_in, est_back) or None.
    """
    try:
        if not victim_tx.to:
            return None

        max_fee, _ = _get_base_and_fees(w3, priority_fee_gwei)
        intent = decode_swap_intent(w3, victim_tx)
        if not intent or not intent.token_out:
            return None

        token_in = intent.token_in or WETH9
        token_out = intent.token_out

        # Get pool liquidity information for optimal sizing
        liquidity_info = get_pool_liquidity_depth(w3, token_in, token_out)
        
        # Calculate optimal position size
        optimal_size = calculate_optimal_position_size(w3, victim_tx, intent, liquidity_info)
        
        # Estimate price impact for the optimal size
        price_impact = estimate_price_impact(w3, token_in, token_out, optimal_size)
        
        # If price impact is too high (>15%), reduce position size
        if price_impact > 0.15:
            optimal_size = int(optimal_size * 0.7)  # Reduce by 30%
            
        # Re-check with reduced size if needed
        if optimal_size < Web3.to_wei(0.02, "ether"):
            return None  # Too small to be profitable
            
        my_eth_in = optimal_size
        token = token_out        
        best_back = 0

        quoter = w3.eth.contract(address=UNISWAP_V3_QUOTERV2, abi=QUOTER_V2_ABI)

        # Try V3 routes with dynamic fee selection based on liquidity
        fee_priority = []
        if liquidity_info.get('v3_3000', 0) > liquidity_info.get('v3_500', 0):
            fee_priority = [3000, 500, 10000]
        elif liquidity_info.get('v3_500', 0) > 0:
            fee_priority = [500, 3000, 10000]
        else:
            fee_priority = [3000, 10000, 500]

        # Try V3 direct route with prioritized fees
        for fee in fee_priority:
            try:
                out = quoter.functions.quoteExactInputSingle(token_in, token_out, fee, my_eth_in, 0).call()[0]
                back = quoter.functions.quoteExactInputSingle(token_out, token_in, fee, out, 0).call()[0]
                if back > best_back:
                    best_back = back
            except Exception:
                continue
        
        # Try V3 two-hop route if direct route isn't great
        if best_back < my_eth_in * 1.01:  # Less than 1% profit
            v3_twohop = _try_v3_twohop_roundtrip(w3, quoter, my_eth_in, token)
            if v3_twohop:
                best_back = max(best_back, v3_twohop)

        # Try V2 routes if V2 liquidity is better
        if liquidity_info.get('v2_liquidity', 0) > liquidity_info.get('total_liquidity', 0) * 0.3:
            for v2r in UNISWAP_V2_ROUTERS:
                b = _try_v2_roundtrip(w3, v2r, my_eth_in, token)
                if b:
                    best_back = max(best_back, b)
                
                b2 = _try_v2_roundtrip_twohop(w3, v2r, my_eth_in, token)
                if b2:
                    best_back = max(best_back, b2)
                    
        # Try Curve stablecoin arbitrage for superior stable token pricing
        curve_back = _try_curve_stablecoin_arbitrage(w3, my_eth_in, token)
        if curve_back:
            best_back = max(best_back, curve_back)

        if best_back <= 0:
            return None

        gas_bundle = 65_000 + 70_000 + 250_000 + 70_000 + 250_000
        gas_wei = gas_bundle * max_fee
        ev_wei = best_back - my_eth_in - gas_wei
        
        # Higher profit threshold for dynamic sizing (should be more profitable)
        min_profit_threshold = Web3.to_wei(0.005, "ether")  # Min 0.005 ETH profit
        if ev_wei <= min_profit_threshold:
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
    "is_uniswap_swap", "estimate_ev_wei", "estimate_ev_universal_wei", "estimate_ev_dynamic_wei",
    "decode_swap_intent", "build_sandwich_bundle", "sig4",
    "validate_token_liquidity", "is_token_blacklisted",
    "get_pool_liquidity_depth", "calculate_optimal_position_size", "estimate_price_impact",
]
