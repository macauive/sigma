from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from .config import BotConfig
from .models import MarketSnapshot, TradeSignal


class AIAdvisor:
    def __init__(self, config: BotConfig):
        self.config = config

    @property
    def enabled(self) -> bool:
        return self.config.ai_enabled and self.config.has_openai_credentials

    def refine_signal(self, snapshot: MarketSnapshot, baseline: TradeSignal) -> TradeSignal:
        if not self.enabled:
            return baseline

        try:
            from openai import OpenAI
        except ImportError:
            return baseline

        client = OpenAI(api_key=self.config.openai_api_key)
        payload = self._build_payload(snapshot, baseline)

        try:
            response = client.responses.create(
                model=self.config.openai_model,
                instructions=(
                    "You are a cautious crypto trading risk analyst. "
                    "You may only return JSON. Never recommend leverage. "
                    "Prefer HOLD unless the edge is explicit after fees and risk."
                ),
                input=json.dumps(payload, separators=(",", ":")),
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "trade_signal",
                        "schema": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "action": {"type": "string", "enum": ["BUY", "SELL", "HOLD"]},
                                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                                "reason": {"type": "string", "maxLength": 300},
                            },
                            "required": ["action", "confidence", "reason"],
                        },
                    }
                },
                max_output_tokens=300,
            )
            data = json.loads(response.output_text)
            return self._merge(baseline, data)
        except Exception as exc:
            return TradeSignal(
                product_id=baseline.product_id,
                action=baseline.action,
                confidence=baseline.confidence,
                quote_size=baseline.quote_size,
                base_size=baseline.base_size,
                reason=f"{baseline.reason} AI advisor unavailable: {type(exc).__name__}.",
                source=baseline.source,
                metadata=baseline.metadata,
            )

    def _build_payload(self, snapshot: MarketSnapshot, baseline: TradeSignal) -> dict[str, Any]:
        candles_tail = snapshot.candles[-20:]
        return {
            "product_id": snapshot.product_id,
            "current_price": str(snapshot.current_price),
            "fee_bps_assumption": str(self.config.fee_bps),
            "risk_limits": {
                "quote_trade_size_usd": str(self.config.quote_trade_size_usd),
                "max_trade_size_usd": str(self.config.max_trade_size_usd),
                "max_trades_per_day": self.config.max_trades_per_day,
            },
            "indicators": snapshot.indicators,
            "baseline_signal": {
                "action": baseline.action,
                "confidence": baseline.confidence,
                "reason": baseline.reason,
            },
            "recent_candles": [
                {
                    "start": candle.start,
                    "open": str(candle.open),
                    "high": str(candle.high),
                    "low": str(candle.low),
                    "close": str(candle.close),
                    "volume": str(candle.volume),
                }
                for candle in candles_tail
            ],
        }

    def _merge(self, baseline: TradeSignal, ai_data: dict[str, Any]) -> TradeSignal:
        action = ai_data.get("action", baseline.action)
        confidence = float(ai_data.get("confidence", baseline.confidence))

        if action not in {"BUY", "SELL", "HOLD"}:
            action = "HOLD"
        confidence = max(0.0, min(1.0, confidence))

        quote_size = baseline.quote_size
        if action == "HOLD":
            quote_size = Decimal("0")

        return TradeSignal(
            product_id=baseline.product_id,
            action=action,
            confidence=confidence,
            quote_size=quote_size,
            base_size=baseline.base_size,
            reason=str(ai_data.get("reason", baseline.reason))[:300],
            source="ai",
            metadata=baseline.metadata,
        )
