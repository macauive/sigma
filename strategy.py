from __future__ import annotations

from decimal import Decimal

from config import BotConfig
from models import MarketSnapshot, TradeSignal


def classify_market_regime(indicators: dict[str, float]) -> str:
    rsi_14 = indicators.get("rsi_14", 50.0)
    trend_up = indicators.get("sma_20_above_50", 0.0) > 0
    change_24 = indicators.get("change_24_candles_pct", 0.0)
    drawdown_24 = indicators.get("drawdown_24_candles_pct", 0.0)
    atr_14 = indicators.get("atr_14_pct", 0.0)
    sma_20_slope = indicators.get("sma_20_slope_pct", 0.0)

    if change_24 <= -4.0 or drawdown_24 <= -5.0 or atr_14 >= 6.0:
        return "crash"
    if not trend_up and (change_24 < -1.0 or sma_20_slope < -0.30):
        return "bear"
    if trend_up and change_24 >= 4.0 and rsi_14 >= 72:
        return "euphoria"
    if trend_up and change_24 > 0.35 and sma_20_slope >= 0:
        return "bull"
    return "neutral"


class RuleBasedStrategy:
    """Regime-aware baseline strategy the AI advisor can veto or refine."""

    def __init__(self, config: BotConfig):
        self.config = config

    def generate(self, snapshot: MarketSnapshot) -> TradeSignal:
        indicators = snapshot.indicators
        rsi_14 = indicators.get("rsi_14", 50.0)
        trend_up = indicators.get("sma_20_above_50", 0.0) > 0
        change_12 = indicators.get("change_12_candles_pct", 0.0)
        change_24 = indicators.get("change_24_candles_pct", 0.0)
        volume_ratio = indicators.get("volume_ratio_20", 1.0)
        atr_14 = indicators.get("atr_14_pct", 0.0)
        regime = classify_market_regime(indicators)

        action = "HOLD"
        confidence = 0.50
        reason = f"No rule-based edge detected in {regime} regime."

        if regime in {"bull", "neutral"} and trend_up and 45 <= rsi_14 <= 68 and change_12 > 0.15 and volume_ratio >= 0.75 and atr_14 <= 4.0:
            action = "BUY"
            confidence = min(0.78, 0.58 + abs(change_12) / 20 + max(0, volume_ratio - 1) / 10)
            reason = f"{regime.title()} regime: trend is positive, RSI is not overbought, and momentum is constructive."
        elif regime in {"crash", "bear"} or rsi_14 > 76 or (not trend_up and change_12 < -0.50):
            action = "SELL"
            confidence = min(0.80, 0.58 + abs(min(change_12, change_24)) / 20)
            reason = f"{regime.title()} regime: momentum is weakening, volatility is elevated, or RSI is stretched."

        return TradeSignal(
            product_id=snapshot.product_id,
            action=action,
            confidence=confidence,
            quote_size=self.config.quote_trade_size_usd,
            base_size=self.config.sell_base_size,
            reason=reason,
            source="rules",
            metadata={
                "indicators": indicators,
                "regime": regime,
                "strategy": "regime_momentum_capital_preservation",
            },
        )
