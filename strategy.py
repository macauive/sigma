from __future__ import annotations

from decimal import Decimal

from config import BotConfig
from models import MarketSnapshot, TradeSignal


class RuleBasedStrategy:
    """A conservative baseline strategy the AI advisor can veto or refine."""

    def __init__(self, config: BotConfig):
        self.config = config

    def generate(self, snapshot: MarketSnapshot) -> TradeSignal:
        indicators = snapshot.indicators
        rsi_14 = indicators.get("rsi_14", 50.0)
        trend_up = indicators.get("sma_20_above_50", 0.0) > 0
        change_12 = indicators.get("change_12_candles_pct", 0.0)
        volume_ratio = indicators.get("volume_ratio_20", 1.0)

        action = "HOLD"
        confidence = 0.50
        reason = "No rule-based edge detected."

        if trend_up and 45 <= rsi_14 <= 68 and change_12 > 0.15 and volume_ratio >= 0.75:
            action = "BUY"
            confidence = min(0.78, 0.58 + abs(change_12) / 20 + max(0, volume_ratio - 1) / 10)
            reason = "Trend is positive, RSI is not overbought, and momentum is constructive."
        elif rsi_14 > 76 or (not trend_up and change_12 < -0.50):
            action = "SELL"
            confidence = min(0.75, 0.56 + abs(change_12) / 20)
            reason = "Momentum is weakening or RSI is stretched."

        return TradeSignal(
            product_id=snapshot.product_id,
            action=action,
            confidence=confidence,
            quote_size=self.config.quote_trade_size_usd,
            base_size=self.config.sell_base_size,
            reason=reason,
            source="rules",
            metadata={"indicators": indicators},
        )
