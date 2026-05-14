from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from models import RiskDecision, TradeSignal


@dataclass(frozen=True)
class PortfolioDecision:
    allowed: bool
    reason: str
    signal: TradeSignal


class PortfolioGuard:
    def __init__(
        self,
        balances: dict[str, Decimal],
        product_limits: dict[str, Decimal],
        mark_price: Decimal,
        max_position_exposure_pct: Decimal,
    ):
        self.balances = balances
        self.product_limits = product_limits
        self.mark_price = mark_price
        self.max_position_exposure_pct = max_position_exposure_pct

    def evaluate(self, decision: RiskDecision) -> PortfolioDecision:
        if not decision.allowed:
            return PortfolioDecision(False, decision.reason, decision.signal)

        signal = decision.signal
        base_currency, quote_currency = _split_product(signal.product_id)
        if signal.action == "BUY":
            return self._evaluate_buy(signal, quote_currency)
        if signal.action == "SELL":
            return self._evaluate_sell(signal, base_currency)
        return PortfolioDecision(False, "Signal is HOLD.", signal)

    def _evaluate_buy(self, signal: TradeSignal, quote_currency: str) -> PortfolioDecision:
        available_quote = self.balances.get(quote_currency, Decimal("0"))
        quote_min_size = self.product_limits.get("quote_min_size", Decimal("0"))
        if quote_min_size > 0 and signal.quote_size < quote_min_size:
            return PortfolioDecision(False, f"BUY below product quote minimum {quote_min_size}.", signal)
        if signal.quote_size > available_quote:
            return PortfolioDecision(False, f"Insufficient {quote_currency} balance.", signal)
        exposure_decision = self._evaluate_position_exposure(signal, quote_currency)
        if not exposure_decision.allowed:
            return exposure_decision
        return PortfolioDecision(True, "Allowed by portfolio guard.", signal)

    def _evaluate_sell(self, signal: TradeSignal, base_currency: str) -> PortfolioDecision:
        base_size = signal.base_size or Decimal("0")
        available_base = self.balances.get(base_currency, Decimal("0"))
        base_min_size = self.product_limits.get("base_min_size", Decimal("0"))
        if base_min_size > 0 and base_size < base_min_size:
            return PortfolioDecision(False, f"SELL below product base minimum {base_min_size}.", signal)
        if base_size > available_base:
            return PortfolioDecision(False, f"Insufficient {base_currency} balance.", signal)
        return PortfolioDecision(True, "Allowed by portfolio guard.", signal)

    def _evaluate_position_exposure(self, signal: TradeSignal, quote_currency: str) -> PortfolioDecision:
        if self.max_position_exposure_pct <= 0:
            return PortfolioDecision(True, "Position exposure check disabled.", signal)

        base_currency, _ = _split_product(signal.product_id)
        base_value = self.balances.get(base_currency, Decimal("0")) * self.mark_price
        quote_value = self.balances.get(quote_currency, Decimal("0"))
        total_value = base_value + quote_value
        if total_value <= 0:
            return PortfolioDecision(True, "No portfolio value available for exposure check.", signal)

        projected_base_value = base_value + signal.quote_size
        projected_exposure_pct = (projected_base_value / total_value) * Decimal("100")
        if projected_exposure_pct > self.max_position_exposure_pct:
            return PortfolioDecision(
                False,
                f"BUY would raise position exposure to {projected_exposure_pct:.2f}%.",
                signal,
            )
        return PortfolioDecision(True, "Allowed by position exposure guard.", signal)


def _split_product(product_id: str) -> tuple[str, str]:
    parts = product_id.upper().split("-", 1)
    if len(parts) != 2:
        return product_id.upper(), "USD"
    return parts[0], parts[1]
