from __future__ import annotations

import time
import uuid
from decimal import Decimal
from typing import Any

import requests

from config import BotConfig
from indicators import build_indicator_snapshot
from models import Candle, MarketSnapshot, OrderResult, TradeSignal

PUBLIC_API_BASE = "https://api.coinbase.com/api/v3/brokerage/market"


def _to_plain_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, dict):
        return value
    return {"raw": repr(value)}


class CoinbaseBroker:
    def __init__(self, config: BotConfig):
        self.config = config
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                from coinbase.rest import RESTClient
            except ImportError as exc:
                raise RuntimeError(
                    "coinbase-advanced-py is not installed. Run: pip install -r requirements.txt"
                ) from exc

            if self.config.has_coinbase_credentials:
                self._client = RESTClient(
                    api_key=self.config.coinbase_api_key,
                    api_secret=self.config.coinbase_api_secret,
                )
            else:
                self._client = RESTClient()
        return self._client

    def get_snapshot(self) -> MarketSnapshot:
        candles = self.get_candles(
            self.config.product_id,
            self.config.granularity,
            self.config.candle_limit,
        )
        if not candles:
            raise RuntimeError(f"No candles returned for {self.config.product_id}")

        indicators = build_indicator_snapshot(candles)
        return MarketSnapshot(
            product_id=self.config.product_id,
            candles=candles,
            current_price=candles[-1].close,
            indicators=indicators,
        )

    def get_candles(self, product_id: str, granularity: str, limit: int) -> list[Candle]:
        end = int(time.time())
        start = end - self._granularity_seconds(granularity) * limit

        try:
            response = self.client.get_public_candles(
                product_id=product_id,
                start=str(start),
                end=str(end),
                granularity=granularity,
                limit=limit,
            )
            raw = _to_plain_dict(response)
            candles = raw.get("candles", [])
        except Exception:
            candles = self._get_public_candles_http(product_id, granularity, start, end, limit)

        return sorted((Candle.from_mapping(c) for c in candles), key=lambda candle: candle.start)

    def submit_market_order(self, signal: TradeSignal) -> OrderResult:
        request = self._build_order_request(signal)
        if self.config.dry_run:
            return OrderResult(
                submitted=False,
                dry_run=True,
                request=request,
                reason="dry run",
            )

        if not self.config.has_coinbase_credentials:
            raise RuntimeError("Live trading requires COINBASE_API_KEY and COINBASE_API_SECRET")

        if signal.action == "BUY":
            response = self.client.market_order_buy(
                client_order_id=request["client_order_id"],
                product_id=signal.product_id,
                quote_size=str(signal.quote_size),
            )
        elif signal.action == "SELL":
            if signal.base_size is None:
                raise RuntimeError("SELL signals require base_size")
            response = self.client.market_order_sell(
                client_order_id=request["client_order_id"],
                product_id=signal.product_id,
                base_size=str(signal.base_size),
            )
        else:
            return OrderResult(
                submitted=False,
                dry_run=False,
                request=request,
                reason="hold",
            )

        return OrderResult(
            submitted=True,
            dry_run=False,
            request=request,
            response=_to_plain_dict(response),
        )

    def _build_order_request(self, signal: TradeSignal) -> dict[str, Any]:
        request = {
            "client_order_id": f"sigma-{uuid.uuid4()}",
            "product_id": signal.product_id,
            "side": signal.action,
            "confidence": signal.confidence,
            "reason": signal.reason,
        }
        if signal.action == "BUY":
            request["quote_size"] = str(signal.quote_size.quantize(Decimal("0.01")))
        if signal.action == "SELL" and signal.base_size is not None:
            request["base_size"] = str(signal.base_size)
        return request

    @staticmethod
    def _granularity_seconds(granularity: str) -> int:
        mapping = {
            "ONE_MINUTE": 60,
            "FIVE_MINUTE": 300,
            "FIFTEEN_MINUTE": 900,
            "THIRTY_MINUTE": 1800,
            "ONE_HOUR": 3600,
            "TWO_HOUR": 7200,
            "FOUR_HOUR": 14400,
            "SIX_HOUR": 21600,
            "ONE_DAY": 86400,
        }
        return mapping.get(granularity, 300)

    @staticmethod
    def _get_public_candles_http(
        product_id: str,
        granularity: str,
        start: int,
        end: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        response = requests.get(
            f"{PUBLIC_API_BASE}/products/{product_id}/candles",
            params={
                "start": str(start),
                "end": str(end),
                "granularity": granularity,
                "limit": limit,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json().get("candles", [])
