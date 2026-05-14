from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
from pathlib import Path
from typing import Any

from models import TradeSignal


@dataclass
class PaperPortfolio:
    cash_usd: Decimal
    base_asset: Decimal
    cost_basis_usd: Decimal = Decimal("0")
    realized_pnl_usd: Decimal = Decimal("0")

    def equity_usd(self, mark_price: Decimal) -> Decimal:
        return self.cash_usd + (self.base_asset * mark_price)


@dataclass(frozen=True)
class PaperTradeResult:
    filled: bool
    reason: str
    action: str
    price: Decimal
    execution_price: Decimal
    quote_size: Decimal
    base_size: Decimal
    fee_usd: Decimal
    realized_pnl_usd: Decimal
    cash_usd: Decimal
    base_asset: Decimal
    cost_basis_usd: Decimal
    equity_usd: Decimal


def _fee_rate(fee_bps: Decimal) -> Decimal:
    return fee_bps / Decimal("10000")


def _json_default(value: Any) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


class PaperTradingLedger:
    def __init__(
        self,
        path: str | None,
        starting_usd: Decimal,
        starting_base: Decimal,
        fee_bps: Decimal,
        slippage_bps: Decimal,
    ):
        self.path = Path(path) if path else None
        self.fee_bps = fee_bps
        self.slippage_bps = slippage_bps
        self.portfolio = PaperPortfolio(
            cash_usd=starting_usd,
            base_asset=starting_base,
            cost_basis_usd=Decimal("0"),
            realized_pnl_usd=Decimal("0"),
        )
        self._load_existing_fills()

    def apply_signal(self, signal: TradeSignal, mark_price: Decimal) -> PaperTradeResult:
        if signal.action == "BUY":
            result = self._buy(signal, mark_price)
        elif signal.action == "SELL":
            result = self._sell(signal, mark_price)
        else:
            result = self._rejected(signal, mark_price, "Signal is HOLD.")

        self._append_event(signal, result)
        return result

    def _buy(self, signal: TradeSignal, mark_price: Decimal) -> PaperTradeResult:
        quote_size = min(signal.quote_size, self.portfolio.cash_usd)
        if quote_size <= 0:
            return self._rejected(signal, mark_price, "Insufficient paper USD balance.")

        execution_price = self._execution_price(mark_price, "BUY")
        fee_usd = quote_size * _fee_rate(self.fee_bps)
        spend_after_fee = quote_size - fee_usd
        if spend_after_fee <= 0:
            return self._rejected(signal, mark_price, "Trade size is consumed by fees.")

        base_size = spend_after_fee / execution_price
        self.portfolio.cash_usd -= quote_size
        self.portfolio.base_asset += base_size
        self.portfolio.cost_basis_usd += quote_size
        return self._filled(
            action="BUY",
            mark_price=mark_price,
            execution_price=execution_price,
            quote_size=quote_size,
            base_size=base_size,
            fee_usd=fee_usd,
            realized_pnl=Decimal("0"),
        )

    def _sell(self, signal: TradeSignal, mark_price: Decimal) -> PaperTradeResult:
        requested_base = signal.base_size or self.portfolio.base_asset
        base_size = min(requested_base, self.portfolio.base_asset)
        if base_size <= 0:
            return self._rejected(signal, mark_price, "Insufficient paper base balance.")

        execution_price = self._execution_price(mark_price, "SELL")
        gross_proceeds = base_size * execution_price
        fee_usd = gross_proceeds * _fee_rate(self.fee_bps)
        net_proceeds = gross_proceeds - fee_usd

        base_before = self.portfolio.base_asset
        cost_reduction = Decimal("0")
        if base_before > 0 and self.portfolio.cost_basis_usd > 0:
            cost_reduction = self.portfolio.cost_basis_usd * (base_size / base_before)
        realized_pnl = net_proceeds - cost_reduction

        self.portfolio.cash_usd += net_proceeds
        self.portfolio.base_asset -= base_size
        self.portfolio.cost_basis_usd = max(Decimal("0"), self.portfolio.cost_basis_usd - cost_reduction)
        self.portfolio.realized_pnl_usd += realized_pnl
        return self._filled(
            action="SELL",
            mark_price=mark_price,
            execution_price=execution_price,
            quote_size=net_proceeds,
            base_size=base_size,
            fee_usd=fee_usd,
            realized_pnl=realized_pnl,
        )

    def _rejected(self, signal: TradeSignal, mark_price: Decimal, reason: str) -> PaperTradeResult:
        return PaperTradeResult(
            filled=False,
            reason=reason,
            action=signal.action,
            price=mark_price,
            execution_price=mark_price,
            quote_size=signal.quote_size,
            base_size=signal.base_size or Decimal("0"),
            fee_usd=Decimal("0"),
            realized_pnl_usd=Decimal("0"),
            cash_usd=self.portfolio.cash_usd,
            base_asset=self.portfolio.base_asset,
            cost_basis_usd=self.portfolio.cost_basis_usd,
            equity_usd=self.portfolio.equity_usd(mark_price),
        )

    def _filled(
        self,
        action: str,
        mark_price: Decimal,
        execution_price: Decimal,
        quote_size: Decimal,
        base_size: Decimal,
        fee_usd: Decimal,
        realized_pnl: Decimal,
    ) -> PaperTradeResult:
        return PaperTradeResult(
            filled=True,
            reason="Filled in paper ledger.",
            action=action,
            price=mark_price,
            execution_price=execution_price,
            quote_size=quote_size,
            base_size=base_size,
            fee_usd=fee_usd,
            realized_pnl_usd=realized_pnl,
            cash_usd=self.portfolio.cash_usd,
            base_asset=self.portfolio.base_asset,
            cost_basis_usd=self.portfolio.cost_basis_usd,
            equity_usd=self.portfolio.equity_usd(mark_price),
        )

    def _execution_price(self, mark_price: Decimal, action: str) -> Decimal:
        slippage = self.slippage_bps / Decimal("10000")
        if action == "BUY":
            return mark_price * (Decimal("1") + slippage)
        return mark_price * (Decimal("1") - slippage)

    def _append_event(self, signal: TradeSignal, result: PaperTradeResult) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "product_id": signal.product_id,
            "signal": {
                "action": signal.action,
                "confidence": signal.confidence,
                "reason": signal.reason,
                "source": signal.source,
            },
            "result": asdict(result),
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, default=_json_default, separators=(",", ":")) + "\n")

    def _load_existing_fills(self) -> None:
        if self.path is None:
            return
        if not self.path.exists():
            return

        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                event = json.loads(line)
                result = event.get("result", {})
                if not result.get("filled"):
                    continue
                self.portfolio.cash_usd = Decimal(str(result["cash_usd"]))
                self.portfolio.base_asset = Decimal(str(result["base_asset"]))
                self.portfolio.cost_basis_usd = Decimal(str(result.get("cost_basis_usd", "0")))
                self.portfolio.realized_pnl_usd += Decimal(str(result.get("realized_pnl_usd", "0")))


def quantize_usd(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
