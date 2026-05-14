from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Literal

Action = Literal["BUY", "SELL", "HOLD"]


@dataclass(frozen=True)
class Candle:
    start: int
    low: Decimal
    high: Decimal
    open: Decimal
    close: Decimal
    volume: Decimal

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> "Candle":
        return cls(
            start=int(raw["start"]),
            low=Decimal(str(raw["low"])),
            high=Decimal(str(raw["high"])),
            open=Decimal(str(raw["open"])),
            close=Decimal(str(raw["close"])),
            volume=Decimal(str(raw["volume"])),
        )


@dataclass(frozen=True)
class MarketSnapshot:
    product_id: str
    candles: list[Candle]
    current_price: Decimal
    indicators: dict[str, float]


@dataclass(frozen=True)
class TradeSignal:
    product_id: str
    action: Action
    confidence: float
    quote_size: Decimal
    reason: str
    source: str
    base_size: Decimal | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    reason: str
    signal: TradeSignal


@dataclass(frozen=True)
class OrderResult:
    submitted: bool
    dry_run: bool
    request: dict[str, Any]
    response: dict[str, Any] | None = None
    reason: str = ""
