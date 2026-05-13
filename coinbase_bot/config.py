from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv


PLACEHOLDER_VALUES = {
    "",
    "replace-me",
    "your-openai-api-key",
    "your-coinbase-api-key",
    "your-coinbase-api-secret",
}


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _env_decimal(name: str, default: str) -> Decimal:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return Decimal(default)
    return Decimal(raw.strip())


def _clean_secret(value: str | None) -> str:
    if value is None:
        return ""
    cleaned = value.strip().strip('"').strip("'")
    return cleaned.replace("\\n", "\n")


def _read_secret_file(path: str) -> str:
    if not path:
        return ""
    secret_path = Path(path).expanduser()
    if not secret_path.exists():
        raise FileNotFoundError(f"Coinbase API secret file not found: {secret_path}")
    return secret_path.read_text().strip()


def has_real_secret(value: str | None) -> bool:
    cleaned = _clean_secret(value).strip()
    return cleaned.lower() not in PLACEHOLDER_VALUES


@dataclass(frozen=True)
class BotConfig:
    product_id: str
    granularity: str
    candle_limit: int
    loop_interval_seconds: int
    dry_run: bool
    coinbase_api_key: str
    coinbase_api_secret: str
    openai_api_key: str
    openai_model: str
    ai_enabled: bool
    quote_trade_size_usd: Decimal
    max_trade_size_usd: Decimal
    max_trades_per_day: int
    max_daily_loss_usd: Decimal
    min_confidence: float
    fee_bps: Decimal
    sell_base_size: Decimal | None
    allow_sells: bool

    @property
    def has_coinbase_credentials(self) -> bool:
        return has_real_secret(self.coinbase_api_key) and has_real_secret(self.coinbase_api_secret)

    @property
    def has_openai_credentials(self) -> bool:
        return has_real_secret(self.openai_api_key)


def load_config(env_path: str = "coinbase.env") -> BotConfig:
    load_dotenv(env_path)
    load_dotenv("private.env")

    secret = _clean_secret(os.getenv("COINBASE_API_SECRET"))
    secret_file = os.getenv("COINBASE_API_SECRET_FILE", "").strip()
    if not has_real_secret(secret) and secret_file:
        secret = _read_secret_file(secret_file)

    sell_size_raw = os.getenv("COINBASE_SELL_BASE_SIZE", "").strip()

    return BotConfig(
        product_id=os.getenv("COINBASE_PRODUCT_ID", "BTC-USD").strip().upper(),
        granularity=os.getenv("COINBASE_GRANULARITY", "FIVE_MINUTE").strip().upper(),
        candle_limit=_env_int("COINBASE_CANDLE_LIMIT", 150),
        loop_interval_seconds=_env_int("COINBASE_LOOP_INTERVAL_SECONDS", 60),
        dry_run=_env_bool("COINBASE_DRY_RUN", True),
        coinbase_api_key=_clean_secret(os.getenv("COINBASE_API_KEY")),
        coinbase_api_secret=secret,
        openai_api_key=_clean_secret(os.getenv("OPENAI_API_KEY")),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini").strip(),
        ai_enabled=_env_bool("ENABLE_AI_ADVISOR", True),
        quote_trade_size_usd=_env_decimal("COINBASE_QUOTE_TRADE_SIZE_USD", "10.00"),
        max_trade_size_usd=_env_decimal("COINBASE_MAX_TRADE_SIZE_USD", "25.00"),
        max_trades_per_day=_env_int("COINBASE_MAX_TRADES_PER_DAY", 6),
        max_daily_loss_usd=_env_decimal("COINBASE_MAX_DAILY_LOSS_USD", "25.00"),
        min_confidence=float(os.getenv("COINBASE_MIN_CONFIDENCE", "0.62")),
        fee_bps=_env_decimal("COINBASE_FEE_BPS", "80"),
        sell_base_size=Decimal(sell_size_raw) if sell_size_raw else None,
        allow_sells=_env_bool("COINBASE_ALLOW_SELLS", False),
    )
