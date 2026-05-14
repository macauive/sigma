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
    def __init__(self, balances: dict[str, Decimal], product_limits: dict[str, Decimal]):
        self.balances = balances
        self.product_limits = product_limits

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


def _split_product(product_id: str) -> tuple[str, str]:
    parts = product_id.upper().split("-", 1)
    if len(parts) != 2:
        return product_id.upper(), "USD"
    return parts[0], parts[1]
