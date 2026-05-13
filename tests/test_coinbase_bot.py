from decimal import Decimal
from unittest import TestCase, main

from coinbase_bot.config import BotConfig, has_real_secret
from coinbase_bot.models import TradeSignal
from coinbase_bot.risk import RiskManager


def _config(**overrides):
    values = {
        "product_id": "BTC-USD",
        "granularity": "FIVE_MINUTE",
        "candle_limit": 150,
        "loop_interval_seconds": 0,
        "dry_run": True,
        "coinbase_api_key": "",
        "coinbase_api_secret": "",
        "openai_api_key": "",
        "openai_model": "gpt-5.4-mini",
        "ai_enabled": True,
        "quote_trade_size_usd": Decimal("10.00"),
        "max_trade_size_usd": Decimal("25.00"),
        "max_trades_per_day": 2,
        "max_daily_loss_usd": Decimal("25.00"),
        "min_confidence": 0.62,
        "fee_bps": Decimal("80"),
        "sell_base_size": None,
        "allow_sells": False,
    }
    values.update(overrides)
    return BotConfig(**values)


class ConfigTests(TestCase):
    def test_placeholders_are_not_real_secrets(self):
        self.assertFalse(has_real_secret("replace-me"))
        self.assertFalse(has_real_secret(""))
        self.assertTrue(has_real_secret("organizations/example/apiKeys/example"))


class RiskManagerTests(TestCase):
    def test_blocks_low_confidence_signal(self):
        risk = RiskManager(_config())
        signal = TradeSignal(
            product_id="BTC-USD",
            action="BUY",
            confidence=0.50,
            quote_size=Decimal("10.00"),
            reason="test",
            source="test",
        )

        decision = risk.evaluate(signal)

        self.assertFalse(decision.allowed)
        self.assertIn("below minimum", decision.reason)

    def test_clips_buy_size_to_configured_max(self):
        risk = RiskManager(_config(max_trade_size_usd=Decimal("15.00")))
        signal = TradeSignal(
            product_id="BTC-USD",
            action="BUY",
            confidence=0.90,
            quote_size=Decimal("50.00"),
            reason="test",
            source="test",
        )

        decision = risk.evaluate(signal)

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.signal.quote_size, Decimal("15.00"))

    def test_blocks_sell_until_enabled(self):
        risk = RiskManager(_config())
        signal = TradeSignal(
            product_id="BTC-USD",
            action="SELL",
            confidence=0.90,
            quote_size=Decimal("0"),
            base_size=Decimal("0.001"),
            reason="test",
            source="test",
        )

        decision = risk.evaluate(signal)

        self.assertFalse(decision.allowed)
        self.assertIn("SELL blocked", decision.reason)


if __name__ == "__main__":
    main()
