from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from config import BotConfig
from models import RiskDecision, TradeSignal


@dataclass
class DailyRiskState:
    day: date
    trades: int = 0
    realized_pnl_usd: Decimal = Decimal("0")


class RiskManager:
    def __init__(self, config: BotConfig):
        self.config = config
        self.state = DailyRiskState(day=date.today())

    def evaluate(self, signal: TradeSignal) -> RiskDecision:
        self._roll_day_if_needed()

        if signal.action == "HOLD":
            return RiskDecision(False, "Signal is HOLD.", signal)

        if signal.confidence < self.config.min_confidence:
            return RiskDecision(
                False,
                f"Confidence {signal.confidence:.2f} is below minimum {self.config.min_confidence:.2f}.",
                signal,
            )

        if signal.quote_size > self.config.max_trade_size_usd:
            adjusted = TradeSignal(
                product_id=signal.product_id,
                action=signal.action,
                confidence=signal.confidence,
                quote_size=self.config.max_trade_size_usd,
                base_size=signal.base_size,
                reason=f"{signal.reason} Trade size clipped by risk manager.",
                source=signal.source,
                metadata=signal.metadata,
            )
            signal = adjusted

        if self.state.trades >= self.config.max_trades_per_day:
            return RiskDecision(False, "Daily trade limit reached.", signal)

        if self.state.realized_pnl_usd <= -self.config.max_daily_loss_usd:
            return RiskDecision(False, "Daily loss limit reached.", signal)

        if signal.action == "SELL":
            if not self.config.allow_sells:
                return RiskDecision(False, "SELL blocked until COINBASE_ALLOW_SELLS=1.", signal)
            if signal.base_size is None or signal.base_size <= 0:
                return RiskDecision(False, "SELL blocked because no base size is configured.", signal)

        return RiskDecision(True, "Allowed by risk manager.", signal)

    def record_submitted_trade(self) -> None:
        self._roll_day_if_needed()
        self.state.trades += 1

    def _roll_day_if_needed(self) -> None:
        today = date.today()
        if self.state.day != today:
            self.state = DailyRiskState(day=today)
