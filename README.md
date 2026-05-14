# Sigma Coinbase Bot

Sigma is a Coinbase Advanced Trade bot. `main.py` starts the Coinbase trading
loop directly.

The bot is designed to be dry-run first:

- Fetch public Coinbase candle data.
- Generate a deterministic baseline signal.
- Optionally ask OpenAI for a risk-aware signal refinement.
- Apply local risk controls before any order can be submitted.
- Append a markdown trading journal entry for each cycle.
- Place live orders only when dry-run is explicitly disabled and Coinbase
  credentials are configured.

## Setup

```bash
pip install -r requirements.txt
cp .env.example coinbase.env
```

Fill in `coinbase.env`, then run one dry-run cycle:

```bash
COINBASE_LOOP_INTERVAL_SECONDS=0 python main.py
```

Run tests:

```bash
python -m unittest tests/test_sigma.py
```

Run a historical backtest:

```bash
python backtester.py --start 2026-01-01T00:00:00Z --end 2026-02-01T00:00:00Z
```

The backtester fetches Coinbase candles, replays the deterministic strategy,
applies the configured fee and slippage assumptions, and reports PnL, max
drawdown, win rate, trade count, and a Sharpe-like score.

## Strategy

Sigma uses a Coinbase-native version of the video template's guardrail-first
approach:

- Classify the market as `crash`, `bear`, `neutral`, `bull`, or `euphoria`.
- Buy only when trend, RSI, momentum, volume, and volatility are constructive.
- Sell or hold during hostile regimes instead of averaging into sharp weakness.
- Let the AI advisor veto or reduce a deterministic signal, but not create a new
  BUY path from a HOLD baseline.
- Enforce local risk gates after any AI refinement.
- Write each cycle to `journal.md` by default so scheduled runs have persistent
  memory outside the model context.

Run a compile check:

```bash
python -m py_compile main.py ai_advisor.py backtester.py coinbase_client.py config.py indicators.py models.py paper_trading.py portfolio.py risk.py strategy.py trading_journal.py tests/test_sigma.py
```

## Safety Defaults

- `COINBASE_DRY_RUN=1` prevents live orders.
- `COINBASE_ALLOW_SELLS=0` blocks sells unless you explicitly enable them.
- `COINBASE_MAX_TRADE_SIZE_USD` caps order size.
- `COINBASE_MAX_POSITION_EXPOSURE_PCT` caps projected live base-asset exposure.
- `COINBASE_BLOCKED_BUY_REGIMES` blocks BUY signals in risky market regimes.
- `COINBASE_MAX_TRADES_PER_DAY` caps daily order count.
- The OpenAI advisor is optional and never bypasses local risk checks.
- Dry-run mode can write a paper-trading ledger to `paper_trades.jsonl`.
