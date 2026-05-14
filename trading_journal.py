from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _plain(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


class TradingJournal:
    def __init__(self, path: str):
        self.path = Path(path) if path else None

    def append(self, event: dict[str, Any]) -> None:
        if self.path is None:
            return

        data = _plain(event)
        signal = data.get("signal", {})
        baseline = data.get("baseline", {})
        risk = data.get("risk", {})
        paper = data.get("paper") or {}
        order = data.get("order") or {}
        indicators = data.get("indicators", {})
        regime = signal.get("metadata", {}).get("regime", "unknown")

        entry = [
            f"\n## {datetime.now(timezone.utc).isoformat()}",
            "",
            f"- Product: {data.get('product_id')}",
            f"- Price: {data.get('price')}",
            f"- Regime: {regime}",
            f"- Baseline: {baseline.get('action')} ({baseline.get('confidence')})",
            f"- Final signal: {signal.get('action')} ({signal.get('confidence')})",
            f"- Risk: {'allowed' if risk.get('allowed') else 'blocked'} - {risk.get('reason')}",
            f"- Order: {order.get('reason') or ('submitted' if order.get('submitted') else 'none')}",
            f"- Paper: {paper.get('reason', 'none')}",
            f"- RSI 14: {indicators.get('rsi_14')}",
            f"- 24-candle change %: {indicators.get('change_24_candles_pct')}",
            f"- 24-candle drawdown %: {indicators.get('drawdown_24_candles_pct')}",
            f"- Reason: {signal.get('reason')}",
            "",
        ]

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(entry))
