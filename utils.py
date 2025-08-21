import time
from typing import List, Optional, Tuple

from eth_account import Account
from web3 import Web3

# --------- Addresses (Ethereum mainnet) ---------
UNISWAP_V2_ROUTER   = Web3.to_checksum_address("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")
UNISWAP_V3_ROUTER   = Web3.to_checksum_address("0xE592427A0AEce92De3Edee1F18E0157C05861564")
UNISWAP_V3_QUOTERV2 = Web3.to_checksum_address("0x61fFE014bA17989E743c5F6cB21bF9697530B21e")
WETH9               = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")

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
    {"type":"function","name":"quoteExactInputSingle","stateMutability":"view",
     "inputs":[
        {"name":"tokenIn","type":"address"},{"name":"tokenOut","type":"address"},
        {"name":"fee","type":"uint24"},{"name":"amountIn","type":"uint256"},
        {"name":"sqrtPriceLimitX96","type":"uint160"}],
     "outputs":[
        {"name":"amountOut","type":"uint256"},
        {"name":"sqrtPriceX96After","type":"uint160"},
        {"name":"initializedTicksCrossed","type":"uint32"},
        {"name":"gasEstimate","type":"uint256"}]},
]

ERC20_MIN_ABI = [
    {"type":"function","name":"approve","stateMutability":"nonpayable",
     "inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],
     "outputs":[{"name":"","type":"bool"}]},
    {"type":"function","name":"balanceOf","stateMutability":"view",
     "inputs":[{"name":"owner","type":"address"}],
     "outputs":[{"name":"","type":"uint256"}]},
    {"type":"function","name":"decimals","stateMutability":"view","inputs":[],"outputs":[{"name":"","type":"uint8"}]},
]

WETH9_MIN_ABI = [
    {"type":"function","name":"deposit","stateMutability":"payable","inputs":[],"outputs":[]},
    {"type":"function","name":"withdraw","stateMutability":"nonpayable","inputs":[{"name":"wad","type":"uint256"}],"outputs":[]},
] + ERC20_MIN_ABI

# --------- Method selectors ---------
SIG_SWAP_EXACT_TOKENS_FOR_TOKENS = "0x38ed1739"
SIG_SWAP_EXACT_ETH_FOR_TOKENS     = "0x7ff36ab5"
SIG_SWAP_EXACT_TOKENS_FOR_ETH     = "0x18cbafe5"
SIG_V3_EXACT_INPUT_SINGLE         = "0x04e45aaf"
SIG_V3_EXACT_INPUT                = "0xb858183f"

MAX_UINT256 = (1 << 256) - 1

# --------- Helpers ---------
def _get_base_and_fees(w3: Web3, priority_fee_gwei: int) -> Tuple[int, int]:
    """Return (maxFeePerGas, maxPriorityFeePerGas) in wei."""
    # v5/v6 getBlock compatibility
    get_block = getattr(w3.eth, "get_block", None) or w3.eth.getBlock
    latest = get_block("latest")
    base = latest.get("baseFeePerGas") or Web3.to_wei(15, "gwei")
    tip  = Web3.to_wei(priority_fee_gwei, "gwei")
    return base + tip * 2, tip

def _get_raw_tx_bytes(w3: Web3, tx_hash_hex: str) -> Optional[bytes]:
    """Fetch raw signed tx bytes from your node (works on many full nodes)."""
    try:
        return w3.eth.get_raw_transaction(tx_hash_hex)  # web3.py v6
    except Exception:
        try:
            return w3.eth.getRawTransaction(tx_hash_hex)  # web3.py v5
        except Exception:
            return None

def _decode_v2(router, victim_tx):
    try:
        fn, args = router.decode_function_input(victim_tx.input)
        return fn.fn_name, args
    except Exception:
        return None, None

def _decode_v3(router_v3, victim_tx):
    try:
        fn, args = router_v3.decode_function_input(victim_tx.input)
        return fn.fn_name, args
    except Exception:
        return None, None

def is_uniswap_swap(tx) -> bool:
    """Quick filter for candidate swaps on V2 or V3 routers."""
    if not tx.to or not tx.input or len(tx.input) < 10:
        return False
    to = Web3.to_checksum_address(tx.to)
    sig = tx.input[:10].lower()
    if to == UNISWAP_V2_ROUTER and sig in {
        SIG_SWAP_EXACT_ETH_FOR_TOKENS, SIG_SWAP_EXACT_TOKENS_FOR_ETH, SIG_SWAP_EXACT_TOKENS_FOR_TOKENS
    }:
        return True
    if to == UNISWAP_V3_ROUTER and sig in {
        SIG_V3_EXACT_INPUT_SINGLE, SIG_V3_EXACT_INPUT
    }:
        return True
    return False

# --------- EV Estimator (pre-victim, conservative) ---------
def estimate_ev_wei(
    w3: Web3,
    victim_tx,
    *,
    buy_portion_bps: int = 300,
    priority_fee_gwei: int = 1,
) -> Optional[Tuple[int, int, int, int]]:
    """
    Returns conservative EV tuple (ev_wei, gas_wei, spent_wei, recv_wei), or None if unsupported.
    We quote our buy & sell *before* the victim; this underestimates profit (safer gate).
    """
    to = Web3.to_checksum_address(victim_tx.to) if victim_tx.to else None
    if not to:
        return None

    max_fee, _ = _get_base_and_fees(w3, priority_fee_gwei)

    if to == UNISWAP_V2_ROUTER:
        router = w3.eth.contract(address=UNISWAP_V2_ROUTER, abi=UNISWAP_V2_ROUTER_ABI)
        fn_name, args = _decode_v2(router, victim_tx)
        if fn_name != "swapExactETHForTokens":
            return None

        victim_path = args.get("path") or args.get(1)
        if not victim_path or len(victim_path) < 2:
            return None

        token_in  = Web3.to_checksum_address(victim_path[0])
        token_out = Web3.to_checksum_address(victim_path[-1])
        if token_in != WETH9:
            return None

        victim_eth_in = int(victim_tx.value)
        if victim_eth_in <= 0:
            return None

        my_eth_in = max(Web3.to_wei(0.02, "ether"), (victim_eth_in * buy_portion_bps) // 10_000)
        my_eth_in = min(my_eth_in, Web3.to_wei(1.2, "ether"))

        try:
            tokens_out = int(router.functions.getAmountsOut(my_eth_in, victim_path).call()[-1])
            est_eth_back = int(router.functions.getAmountsOut(tokens_out, [token_out, WETH9]).call()[-1])
        except Exception:
            return None

        gas_bundle = 250_000 + 70_000 + 250_000  # buy + approve + sell
        gas_wei = gas_bundle * max_fee
        ev_wei = est_eth_back - my_eth_in - gas_wei
        return ev_wei, gas_wei, my_eth_in, est_eth_back

    if to == UNISWAP_V3_ROUTER:
        router_v3 = w3.eth.contract(address=UNISWAP_V3_ROUTER, abi=UNISWAP_V3_ROUTER_ABI)
        quoter = w3.eth.contract(address=UNISWAP_V3_QUOTERV2, abi=QUOTER_V2_ABI)
        fn_name, args = _decode_v3(router_v3, victim_tx)
        if fn_name != "exactInputSingle":
            return None

        params = args.get("params")
        if not params:
            return None

        token_in  = Web3.to_checksum_address(params.get("tokenIn"))
        token_out = Web3.to_checksum_address(params.get("tokenOut"))
        fee       = int(params.get("fee"))
        if token_in != WETH9:
            return None

        victim_amount_in = int(params.get("amountIn", 0)) or int(victim_tx.value or 0)
        if victim_amount_in <= 0:
            return None

        my_eth_in = max(Web3.to_wei(0.02, "ether"), (victim_amount_in * buy_portion_bps) // 10_000)
        my_eth_in = min(my_eth_in, Web3.to_wei(1.2, "ether"))

        try:
            tokens_out = int(quoter.functions.quoteExactInputSingle(WETH9, token_out, fee, my_eth_in, 0).call()[0])
            est_eth_back = int(quoter.functions.quoteExactInputSingle(token_out, WETH9, fee, tokens_out, 0).call()[0])
        except Exception:
            return None

        gas_bundle = 65_000 + 70_000 + 250_000 + 70_000 + 250_000  # wrap + approveWETH + buy + approveOut + sell
        gas_wei = gas_bundle * max_fee
        ev_wei = est_eth_back - my_eth_in - gas_wei
        return ev_wei, gas_wei, my_eth_in, est_eth_back

    return None

# --------- Bundle builder ---------
def build_sandwich_bundle(
    w3: Web3,
    victim_tx,
    searcher: Account,
    *,
    buy_portion_bps: int = 300,
    max_slippage_bps: int = 80,
    sell_min_out_bps: int = 0,
    gas_limit_buy: int = 250_000,
    gas_limit_approve: int = 70_000,
    gas_limit_wrap: int = 65_000,
    gas_limit_sell: int = 250_000,
    priority_fee_gwei: int = 1,
    ttl_seconds: int = 30,
) -> Optional[List[bytes]]:
    """
    Build bundle [our pre-tx(s)..., victim_raw, our post-tx].
    Supports:
      • V2: victim swapExactETHForTokens (ETH->Token)
      • V3: victim exactInputSingle with tokenIn=WETH9 (WETH->Token)
    """
    if not victim_tx.to:
        return None

    to = Web3.to_checksum_address(victim_tx.to)
    sender = searcher.address
    chain_id = w3.eth.chain_id
    get_nonce = getattr(w3.eth, "get_transaction_count", None) or w3.eth.getTransactionCount
    nonce0 = get_nonce(sender)
    deadline = int(time.time()) + ttl_seconds
    max_fee, max_priority = _get_base_and_fees(w3, priority_fee_gwei)

    if to == UNISWAP_V2_ROUTER:
        router = w3.eth.contract(address=UNISWAP_V2_ROUTER, abi=UNISWAP_V2_ROUTER_ABI)
        fn_name, args = _decode_v2(router, victim_tx)
        if fn_name != "swapExactETHForTokens":
            return None

        victim_path = args.get("path") or args.get(1)
        if not victim_path or len(victim_path) < 2:
            return None

        token_in  = Web3.to_checksum_address(victim_path[0])
        token_out = Web3.to_checksum_address(victim_path[-1])
        if token_in != WETH9:
            return None

        victim_eth_in = int(victim_tx.value)
        if victim_eth_in <= 0:
            return None

        my_eth_in = max(Web3.to_wei(0.02, "ether"), (victim_eth_in * buy_portion_bps) // 10_000)
        my_eth_in = min(my_eth_in, Web3.to_wei(1.2, "ether"))

        try:
            amounts_out_buy = router.functions.getAmountsOut(my_eth_in, victim_path).call()
            tokens_expected_from_buy = int(amounts_out_buy[-1])
        except Exception:
            return None
        if tokens_expected_from_buy <= 0:
            return None

        amount_out_min_buy = (tokens_expected_from_buy * (10_000 - max_slippage_bps)) // 10_000
        buy_tx = router.functions.swapExactETHForTokens(
            amount_out_min_buy, victim_path, sender, deadline
        ).build_transaction({
            "from": sender, "value": my_eth_in, "nonce": nonce0, "gas": gas_limit_buy,
            "maxFeePerGas": max_fee, "maxPriorityFeePerGas": max_priority, "chainId": chain_id
        })
        signed_buy = w3.eth.account.sign_transaction(buy_tx, private_key=searcher.key)

        token_out_contract = w3.eth.contract(address=token_out, abi=ERC20_MIN_ABI)
        approve_tx = token_out_contract.functions.approve(
            UNISWAP_V2_ROUTER, MAX_UINT256
        ).build_transaction({
            "from": sender, "nonce": nonce0 + 1, "gas": gas_limit_approve,
            "maxFeePerGas": max_fee, "maxPriorityFeePerGas": max_priority, "chainId": chain_id
        })
        signed_approve = w3.eth.account.sign_transaction(approve_tx, private_key=searcher.key)

        victim_raw = _get_raw_tx_bytes(w3, victim_tx.hash.hex())
        if victim_raw is None:
            return None

        sell_path = [token_out, WETH9]
        if sell_min_out_bps > 0:
            try:
                est_eth_out = router.functions.getAmountsOut(tokens_expected_from_buy, sell_path).call()[-1]
                amount_out_min_sell = int((est_eth_out * sell_min_out_bps) // 10_000)
            except Exception:
                amount_out_min_sell = 0
        else:
            amount_out_min_sell = 0

        sell_tx = router.functions.swapExactTokensForETH(
            tokens_expected_from_buy, amount_out_min_sell, sell_path, sender, deadline
        ).build_transaction({
            "from": sender, "nonce": nonce0 + 2, "gas": gas_limit_sell,
            "maxFeePerGas": max_fee, "maxPriorityFeePerGas": max_priority, "chainId": chain_id
        })
        signed_sell = w3.eth.account.sign_transaction(sell_tx, private_key=searcher.key)

        return [
            signed_buy.rawTransaction,
            signed_approve.rawTransaction,
            victim_raw,
            signed_sell.rawTransaction,
        ]

    if to == UNISWAP_V3_ROUTER:
        router_v3 = w3.eth.contract(address=UNISWAP_V3_ROUTER, abi=UNISWAP_V3_ROUTER_ABI)
        fn_name, args = _decode_v3(router_v3, victim_tx)
        if fn_name != "exactInputSingle":
            return None

        params = args.get("params")
        if not params:
            return None

        token_in  = Web3.to_checksum_address(params.get("tokenIn"))
        token_out = Web3.to_checksum_address(params.get("tokenOut"))
        fee       = int(params.get("fee"))
        if token_in != WETH9:
            return None

        victim_amount_in = int(params.get("amountIn", 0)) or int(victim_tx.value or 0)
        if victim_amount_in <= 0:
            return None

        my_eth_in = max(Web3.to_wei(0.02, "ether"), (victim_amount_in * buy_portion_bps) // 10_000)
        my_eth_in = min(my_eth_in, Web3.to_wei(1.2, "ether"))

        weth = w3.eth.contract(address=WETH9, abi=WETH9_MIN_ABI)
        token_out_contract = w3.eth.contract(address=token_out, abi=ERC20_MIN_ABI)
        quoter = w3.eth.contract(address=UNISWAP_V3_QUOTERV2, abi=QUOTER_V2_ABI)

        try:
            quote = quoter.functions.quoteExactInputSingle(WETH9, token_out, fee, my_eth_in, 0).call()
            tokens_expected_from_buy = int(quote[0])
        except Exception:
            return None
        if tokens_expected_from_buy <= 0:
            return None

        wrap_tx = weth.functions.deposit().build_transaction({
            "from": sender, "value": my_eth_in, "nonce": nonce0, "gas": gas_limit_wrap,
            "maxFeePerGas": max_fee, "maxPriorityFeePerGas": max_priority, "chainId": chain_id
        })
        signed_wrap = w3.eth.account.sign_transaction(wrap_tx, private_key=searcher.key)

        approve_weth_tx = weth.functions.approve(UNISWAP_V3_ROUTER, MAX_UINT256).build_transaction({
            "from": sender, "nonce": nonce0 + 1, "gas": gas_limit_approve,
            "maxFeePerGas": max_fee, "maxPriorityFeePerGas": max_priority, "chainId": chain_id
        })
        signed_approve_weth = w3.eth.account.sign_transaction(approve_weth_tx, private_key=searcher.key)

        amount_out_min_buy = (tokens_expected_from_buy * (10_000 - max_slippage_bps)) // 10_000
        buy_params = {
            "tokenIn": WETH9, "tokenOut": token_out, "fee": fee, "recipient": sender,
            "deadline": deadline, "amountIn": my_eth_in,
            "amountOutMinimum": amount_out_min_buy, "sqrtPriceLimitX96": 0
        }
        buy_tx = router_v3.functions.exactInputSingle(buy_params).build_transaction({
            "from": sender, "nonce": nonce0 + 2, "gas": gas_limit_buy,
            "maxFeePerGas": max_fee, "maxPriorityFeePerGas": max_priority, "chainId": chain_id
        })
        signed_buy = w3.eth.account.sign_transaction(buy_tx, private_key=searcher.key)

        approve_out_tx = token_out_contract.functions.approve(UNISWAP_V3_ROUTER, MAX_UINT256).build_transaction({
            "from": sender, "nonce": nonce0 + 3, "gas": gas_limit_approve,
            "maxFeePerGas": max_fee, "maxPriorityFeePerGas": max_priority, "chainId": chain_id
        })
        signed_approve_out = w3.eth.account.sign_transaction(approve_out_tx, private_key=searcher.key)

        victim_raw = _get_raw_tx_bytes(w3, victim_tx.hash.hex())
        if victim_raw is None:
            return None

        if sell_min_out_bps > 0:
            try:
                sell_quote = quoter.functions.quoteExactInputSingle(token_out, WETH9, fee, tokens_expected_from_buy, 0).call()
                min_out_sell = int((int(sell_quote[0]) * sell_min_out_bps) // 10_000)
            except Exception:
                min_out_sell = 0
        else:
            min_out_sell = 0

        sell_params = {
            "tokenIn": token_out, "tokenOut": WETH9, "fee": fee, "recipient": sender,
            "deadline": deadline, "amountIn": tokens_expected_from_buy,
            "amountOutMinimum": min_out_sell, "sqrtPriceLimitX96": 0
        }
        sell_tx = router_v3.functions.exactInputSingle(sell_params).build_transaction({
            "from": sender, "nonce": nonce0 + 4, "gas": gas_limit_sell,
            "maxFeePerGas": max_fee, "maxPriorityFeePerGas": max_priority, "chainId": chain_id
        })
        signed_sell = w3.eth.account.sign_transaction(sell_tx, private_key=searcher.key)

        return [
            signed_wrap.rawTransaction,
            signed_approve_weth.rawTransaction,
            signed_buy.rawTransaction,
            signed_approve_out.rawTransaction,
            victim_raw,
            signed_sell.rawTransaction,
        ]

    return None
