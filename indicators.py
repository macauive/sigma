from __future__ import annotations

from decimal import Decimal

from models import Candle


def simple_moving_average(values: list[Decimal], period: int) -> float | None:
    if len(values) < period or period <= 0:
        return None
    window = values[-period:]
    return float(sum(window) / Decimal(period))


def percentage_change(first: Decimal, last: Decimal) -> float:
    if first == 0:
        return 0.0
    return float(((last - first) / first) * Decimal(100))


def max_drawdown_pct(values: list[Decimal]) -> float:
    if not values:
        return 0.0
    peak = values[0]
    max_drawdown = Decimal("0")
    for value in values:
        peak = max(peak, value)
        if peak > 0:
            max_drawdown = min(max_drawdown, (value - peak) / peak)
    return float(max_drawdown * Decimal(100))


def average_true_range_pct(candles: list[Candle], period: int = 14) -> float | None:
    if len(candles) <= period:
        return None

    ranges: list[Decimal] = []
    for previous, current in zip(candles[-period - 1 : -1], candles[-period:]):
        high_low = current.high - current.low
        high_close = abs(current.high - previous.close)
        low_close = abs(current.low - previous.close)
        ranges.append(max(high_low, high_close, low_close))

    last_close = candles[-1].close
    if last_close <= 0:
        return 0.0
    atr = sum(ranges) / Decimal(period)
    return float((atr / last_close) * Decimal(100))


def rsi(values: list[Decimal], period: int = 14) -> float | None:
    if len(values) <= period:
        return None

    gains: list[Decimal] = []
    losses: list[Decimal] = []
    for previous, current in zip(values[-period - 1 : -1], values[-period:]):
        delta = current - previous
        if delta >= 0:
            gains.append(delta)
            losses.append(Decimal("0"))
        else:
            gains.append(Decimal("0"))
            losses.append(abs(delta))

    avg_gain = sum(gains) / Decimal(period)
    avg_loss = sum(losses) / Decimal(period)
    if avg_loss == 0:
        return 100.0

    relative_strength = avg_gain / avg_loss
    return float(100 - (100 / (1 + relative_strength)))


def build_indicator_snapshot(candles: list[Candle]) -> dict[str, float]:
    closes = [c.close for c in candles]
    volumes = [c.volume for c in candles]
    if not closes:
        return {}

    last = closes[-1]
    prior_12 = closes[-13] if len(closes) >= 13 else closes[0]
    prior_24 = closes[-25] if len(closes) >= 25 else closes[0]

    sma_20 = simple_moving_average(closes, 20)
    sma_50 = simple_moving_average(closes, 50)
    sma_20_previous = simple_moving_average(closes[:-5], 20) if len(closes) >= 25 else None
    avg_volume_20 = simple_moving_average(volumes, 20)
    recent_closes_24 = closes[-24:] if len(closes) >= 24 else closes

    indicators = {
        "price": float(last),
        "change_12_candles_pct": percentage_change(prior_12, last),
        "change_24_candles_pct": percentage_change(prior_24, last),
        "drawdown_24_candles_pct": max_drawdown_pct(recent_closes_24),
        "atr_14_pct": average_true_range_pct(candles, 14) or 0.0,
        "rsi_14": rsi(closes, 14) or 50.0,
        "sma_20": sma_20 or float(last),
        "sma_50": sma_50 or float(last),
        "sma_20_slope_pct": percentage_change(
            Decimal(str(sma_20_previous)),
            Decimal(str(sma_20)),
        )
        if sma_20 is not None and sma_20_previous is not None
        else 0.0,
        "volume": float(volumes[-1]),
        "avg_volume_20": avg_volume_20 or float(volumes[-1]),
    }
    indicators["sma_20_above_50"] = 1.0 if indicators["sma_20"] > indicators["sma_50"] else 0.0
    indicators["volume_ratio_20"] = (
        indicators["volume"] / indicators["avg_volume_20"] if indicators["avg_volume_20"] else 1.0
    )
    return indicators
