from decimal import Decimal
from unittest import TestCase, main

from config import BotConfig, has_real_secret
from backtester import CoinbaseBacktester
from models import Candle, MarketSnapshot, TradeSignal
from paper_trading import PaperTradingLedger
from portfolio import PortfolioGuard
from risk import RiskManager
from strategy import RuleBasedStrategy, classify_market_regime


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
        "max_position_exposure_pct": Decimal("35"),
        "max_trades_per_day": 2,
        "max_daily_loss_usd": Decimal("25.00"),
        "min_confidence": 0.62,
        "blocked_buy_regimes": ("crash", "bear", "euphoria"),
        "fee_bps": Decimal("80"),
        "slippage_bps": Decimal("10"),
        "sell_base_size": None,
        "allow_sells": False,
        "paper_trading_enabled": True,
        "paper_ledger_path": "paper_trades.jsonl",
        "paper_starting_usd": Decimal("1000.00"),
        "paper_starting_base": Decimal("0"),
        "journal_path": "",
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

    def test_blocks_buy_in_hostile_regime(self):
        risk = RiskManager(_config())
        signal = TradeSignal(
            product_id="BTC-USD",
            action="BUY",
            confidence=0.90,
            quote_size=Decimal("10.00"),
            reason="test",
            source="test",
            metadata={"regime": "crash"},
        )

        decision = risk.evaluate(signal)

        self.assertFalse(decision.allowed)
        self.assertIn("BUY blocked", decision.reason)


class StrategyTests(TestCase):
    def test_classifies_crash_regime(self):
        regime = classify_market_regime(
            {
                "rsi_14": 38.0,
                "sma_20_above_50": 0.0,
                "change_24_candles_pct": -4.5,
                "drawdown_24_candles_pct": -6.0,
                "atr_14_pct": 2.0,
                "sma_20_slope_pct": -0.5,
            }
        )

        self.assertEqual(regime, "crash")

    def test_generates_buy_only_in_constructive_regime(self):
        strategy = RuleBasedStrategy(_config(min_confidence=0.50))
        candles = [
            Candle(
                start=1_700_000_000 + index * 300,
                low=Decimal(100 + index),
                high=Decimal(101 + index),
                open=Decimal(100 + index),
                close=Decimal(100 + index),
                volume=Decimal("10"),
            )
            for index in range(70)
        ]
        snapshot = MarketSnapshot(
            product_id="BTC-USD",
            candles=candles,
            current_price=candles[-1].close,
            indicators={
                "rsi_14": 55.0,
                "sma_20_above_50": 1.0,
                "change_12_candles_pct": 1.0,
                "change_24_candles_pct": 2.0,
                "drawdown_24_candles_pct": 0.0,
                "atr_14_pct": 1.0,
                "sma_20_slope_pct": 0.2,
                "volume_ratio_20": 1.0,
            },
        )

        signal = strategy.generate(snapshot)

        self.assertEqual(signal.action, "BUY")
        self.assertEqual(signal.metadata["regime"], "bull")


class PaperTradingTests(TestCase):
    def test_paper_ledger_tracks_fake_balances(self):
        ledger = PaperTradingLedger(
            path=None,
            starting_usd=Decimal("100.00"),
            starting_base=Decimal("0"),
            fee_bps=Decimal("100"),
            slippage_bps=Decimal("0"),
        )
        signal = TradeSignal(
            product_id="BTC-USD",
            action="BUY",
            confidence=0.90,
            quote_size=Decimal("10.00"),
            reason="test",
            source="test",
        )

        result = ledger.apply_signal(signal, Decimal("1000"))

        self.assertTrue(result.filled)
        self.assertEqual(result.cash_usd, Decimal("90.00"))
        self.assertEqual(result.base_size, Decimal("0.0099"))


class PortfolioGuardTests(TestCase):
    def test_blocks_buy_that_would_exceed_position_exposure(self):
        signal = TradeSignal(
            product_id="BTC-USD",
            action="BUY",
            confidence=0.90,
            quote_size=Decimal("200.00"),
            reason="test",
            source="test",
        )
        risk = RiskManager(_config(max_trade_size_usd=Decimal("250.00"))).evaluate(signal)
        guard = PortfolioGuard(
            balances={"USD": Decimal("1000.00"), "BTC": Decimal("0.01")},
            product_limits={"quote_min_size": Decimal("1.00")},
            mark_price=Decimal("50000.00"),
            max_position_exposure_pct=Decimal("40"),
        )

        decision = guard.evaluate(risk)

        self.assertFalse(decision.allowed)
        self.assertIn("position exposure", decision.reason)


class BacktesterTests(TestCase):
    def test_backtester_reports_scoreboard_metrics(self):
        candles = [
            Candle(
                start=1_700_000_000 + index * 300,
                low=Decimal(100 + index),
                high=Decimal(101 + index),
                open=Decimal(100 + index),
                close=Decimal(100 + index),
                volume=Decimal("10"),
            )
            for index in range(70)
        ]

        report = CoinbaseBacktester(
            _config(min_confidence=0.50, fee_bps=Decimal("0"), slippage_bps=Decimal("0")),
            initial_usd=Decimal("1000"),
            min_history=60,
        ).run(candles)

        self.assertEqual(report.product_id, "BTC-USD")
        self.assertEqual(report.candle_count, 70)
        self.assertGreaterEqual(report.trade_count, 0)
        self.assertIsInstance(report.total_return_pct, float)


if __name__ == "__main__":
    main()
