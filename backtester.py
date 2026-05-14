from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from coinbase_client import CoinbaseBroker
from config import BotConfig, load_config
from indicators import build_indicator_snapshot
from models import Candle, MarketSnapshot, TradeSignal
from paper_trading import PaperTradingLedger
from strategy import RuleBasedStrategy


@dataclass(frozen=True)
class BacktestTrade:
    ts: datetime
    action: str
    price: Decimal
    execution_price: Decimal
    quote_size: Decimal
    base_size: Decimal
    fee_usd: Decimal
    realized_pnl_usd: Decimal
    equity_usd: Decimal
    reason: str


@dataclass(frozen=True)
class BacktestReport:
    product_id: str
    candle_count: int
    start: datetime | None
    end: datetime | None
    initial_equity_usd: Decimal
    final_equity_usd: Decimal
    total_return_pct: float
    realized_pnl_usd: Decimal
    unrealized_pnl_usd: Decimal
    max_drawdown_pct: float
    trade_count: int
    win_rate_pct: float
    sharpe_like: float
    fee_bps: Decimal
    slippage_bps: Decimal
    trades: list[BacktestTrade]


class CoinbaseBacktester:
    def __init__(
        self,
        config: BotConfig,
        initial_usd: Decimal | None = None,
        initial_base: Decimal | None = None,
        min_history: int = 60,
    ):
        self.config = config
        self.initial_usd = initial_usd if initial_usd is not None else config.paper_starting_usd
        self.initial_base = initial_base if initial_base is not None else config.paper_starting_base
        self.min_history = min_history
        self.strategy = RuleBasedStrategy(config)

    def run(self, candles: list[Candle]) -> BacktestReport:
        ordered = sorted(candles, key=lambda candle: candle.start)
        if len(ordered) < self.min_history:
            raise ValueError(f"Backtest needs at least {self.min_history} candles.")

        ledger = PaperTradingLedger(
            path=None,
            starting_usd=self.initial_usd,
            starting_base=self.initial_base,
            fee_bps=self.config.fee_bps,
            slippage_bps=self.config.slippage_bps,
        )
        initial_equity = ledger.portfolio.equity_usd(ordered[self.min_history - 1].close)
        equity_curve: list[Decimal] = [initial_equity]
        trades: list[BacktestTrade] = []

        for index in range(self.min_history, len(ordered)):
            window = ordered[: index + 1]
            candle = ordered[index]
            snapshot = MarketSnapshot(
                product_id=self.config.product_id,
                candles=window,
                current_price=candle.close,
                indicators=build_indicator_snapshot(window),
            )
            signal = self._prepare_signal(self.strategy.generate(snapshot), ledger.portfolio.base_asset)
            if signal.action != "HOLD":
                result = ledger.apply_signal(signal, candle.close)
                if result.filled:
                    trades.append(
                        BacktestTrade(
                            ts=datetime.fromtimestamp(candle.start, timezone.utc),
                            action=result.action,
                            price=result.price,
                            execution_price=result.execution_price,
                            quote_size=result.quote_size,
                            base_size=result.base_size,
                            fee_usd=result.fee_usd,
                            realized_pnl_usd=result.realized_pnl_usd,
                            equity_usd=result.equity_usd,
                            reason=signal.reason,
                        )
                    )
            equity_curve.append(ledger.portfolio.equity_usd(candle.close))

        final_price = ordered[-1].close
        final_equity = ledger.portfolio.equity_usd(final_price)
        unrealized = (ledger.portfolio.base_asset * final_price) - ledger.portfolio.cost_basis_usd
        return BacktestReport(
            product_id=self.config.product_id,
            candle_count=len(ordered),
            start=datetime.fromtimestamp(ordered[0].start, timezone.utc),
            end=datetime.fromtimestamp(ordered[-1].start, timezone.utc),
            initial_equity_usd=initial_equity,
            final_equity_usd=final_equity,
            total_return_pct=_pct_change(initial_equity, final_equity),
            realized_pnl_usd=ledger.portfolio.realized_pnl_usd,
            unrealized_pnl_usd=unrealized,
            max_drawdown_pct=_max_drawdown_pct(equity_curve),
            trade_count=len(trades),
            win_rate_pct=_win_rate_pct(trades),
            sharpe_like=_sharpe_like(equity_curve),
            fee_bps=self.config.fee_bps,
            slippage_bps=self.config.slippage_bps,
            trades=trades,
        )

    def _prepare_signal(self, signal: TradeSignal, available_base: Decimal) -> TradeSignal:
        if signal.confidence < self.config.min_confidence:
            return _hold(signal, "Backtest confidence gate.")

        if signal.action == "BUY":
            quote_size = min(signal.quote_size, self.config.max_trade_size_usd)
            return _replace_signal(signal, quote_size=quote_size)

        if signal.action == "SELL":
            base_size = signal.base_size or available_base
            if base_size <= 0:
                return _hold(signal, "Backtest has no base asset to sell.")
            return _replace_signal(signal, quote_size=Decimal("0"), base_size=base_size)

        return signal


def fetch_coinbase_candles(config: BotConfig, start: datetime, end: datetime) -> list[Candle]:
    broker = CoinbaseBroker(config)
    return broker.get_historical_candles(config.product_id, config.granularity, start, end)


def report_to_dict(report: BacktestReport) -> dict[str, Any]:
    return asdict(report)


def _replace_signal(
    signal: TradeSignal,
    quote_size: Decimal,
    base_size: Decimal | None = None,
) -> TradeSignal:
    return TradeSignal(
        product_id=signal.product_id,
        action=signal.action,
        confidence=signal.confidence,
        quote_size=quote_size,
        base_size=base_size if base_size is not None else signal.base_size,
        reason=signal.reason,
        source=signal.source,
        metadata=signal.metadata,
        created_at=signal.created_at,
    )


def _hold(signal: TradeSignal, reason: str) -> TradeSignal:
    return TradeSignal(
        product_id=signal.product_id,
        action="HOLD",
        confidence=signal.confidence,
        quote_size=Decimal("0"),
        base_size=None,
        reason=f"{signal.reason} {reason}",
        source=signal.source,
        metadata=signal.metadata,
        created_at=signal.created_at,
    )


def _pct_change(start: Decimal, end: Decimal) -> float:
    if start == 0:
        return 0.0
    return float(((end - start) / start) * Decimal("100"))


def _max_drawdown_pct(equity_curve: list[Decimal]) -> float:
    peak = equity_curve[0]
    max_drawdown = Decimal("0")
    for equity in equity_curve:
        peak = max(peak, equity)
        if peak > 0:
            max_drawdown = min(max_drawdown, (equity - peak) / peak)
    return float(max_drawdown * Decimal("100"))


def _win_rate_pct(trades: list[BacktestTrade]) -> float:
    closing_trades = [trade for trade in trades if trade.action == "SELL"]
    if not closing_trades:
        return 0.0
    winners = [trade for trade in closing_trades if trade.realized_pnl_usd > 0]
    return (len(winners) / len(closing_trades)) * 100


def _sharpe_like(equity_curve: list[Decimal]) -> float:
    returns: list[float] = []
    for previous, current in zip(equity_curve[:-1], equity_curve[1:]):
        if previous > 0:
            returns.append(float((current - previous) / previous))
    if len(returns) < 2:
        return 0.0
    average = sum(returns) / len(returns)
    variance = sum((value - average) ** 2 for value in returns) / (len(returns) - 1)
    stddev = math.sqrt(variance)
    if stddev == 0:
        return 0.0
    return (average / stddev) * math.sqrt(len(returns))


def _json_default(value: Any) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest the Sigma Coinbase strategy.")
    parser.add_argument("--start", required=True, help="ISO timestamp, e.g. 2026-01-01T00:00:00Z")
    parser.add_argument("--end", required=True, help="ISO timestamp, e.g. 2026-02-01T00:00:00Z")
    parser.add_argument("--initial-usd", default=None, help="Starting paper USD balance.")
    parser.add_argument("--initial-base", default=None, help="Starting BTC balance.")
    args = parser.parse_args()

    config = load_config()
    candles = fetch_coinbase_candles(config, _parse_datetime(args.start), _parse_datetime(args.end))
    report = CoinbaseBacktester(
        config=config,
        initial_usd=Decimal(args.initial_usd) if args.initial_usd else None,
        initial_base=Decimal(args.initial_base) if args.initial_base else None,
    ).run(candles)
    print(json.dumps(report_to_dict(report), default=_json_default, indent=2))


if __name__ == "__main__":
    main()
