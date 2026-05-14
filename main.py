from __future__ import annotations

import json
import time
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal

from ai_advisor import AIAdvisor
from coinbase_client import CoinbaseBroker
from config import load_config
from paper_trading import PaperTradingLedger
from portfolio import PortfolioGuard
from risk import RiskManager
from strategy import RuleBasedStrategy


def _json_default(value):
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


class TradingBot:
    def __init__(self):
        self.config = load_config()
        self.broker = CoinbaseBroker(self.config)
        self.strategy = RuleBasedStrategy(self.config)
        self.advisor = AIAdvisor(self.config)
        self.risk = RiskManager(self.config)
        self.paper_ledger = (
            PaperTradingLedger(
                path=self.config.paper_ledger_path,
                starting_usd=self.config.paper_starting_usd,
                starting_base=self.config.paper_starting_base,
                fee_bps=self.config.fee_bps,
                slippage_bps=self.config.slippage_bps,
            )
            if self.config.paper_trading_enabled
            else None
        )

    def run_once(self) -> dict:
        snapshot = self.broker.get_snapshot()
        baseline = self.strategy.generate(snapshot)
        signal = self.advisor.refine_signal(snapshot, baseline)
        decision = self.risk.evaluate(signal)

        result = None
        paper_result = None
        portfolio_decision = None
        if decision.allowed:
            if self.config.dry_run:
                result = self.broker.submit_market_order(decision.signal)
                if self.paper_ledger is not None:
                    paper_result = self.paper_ledger.apply_signal(decision.signal, snapshot.current_price)
            else:
                portfolio_decision = PortfolioGuard(
                    balances=self.broker.get_balances(),
                    product_limits=self.broker.get_product_limits(decision.signal.product_id),
                ).evaluate(decision)
                if portfolio_decision.allowed:
                    result = self.broker.submit_market_order(portfolio_decision.signal)
            if result.submitted or result.dry_run:
                self.risk.record_submitted_trade()

        event = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "product_id": snapshot.product_id,
            "price": snapshot.current_price,
            "indicators": snapshot.indicators,
            "baseline": baseline,
            "signal": signal,
            "risk": decision,
            "portfolio": portfolio_decision,
            "order": result,
            "paper": paper_result,
            "dry_run": self.config.dry_run,
            "ai_enabled": self.advisor.enabled,
        }
        print(json.dumps(event, default=_json_default, indent=2))
        return event


def run_once() -> dict:
    return TradingBot().run_once()


def main() -> None:
    bot = TradingBot()
    while True:
        bot.run_once()
        if bot.config.loop_interval_seconds <= 0:
            break
        time.sleep(bot.config.loop_interval_seconds)


if __name__ == "__main__":
    main()
