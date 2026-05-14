# Sigma Coinbase Bot

Sigma is a Coinbase Advanced Trade bot. `main.py` starts the Coinbase trading
loop directly.

The bot is designed to be dry-run first:

- Fetch public Coinbase candle data.
- Generate a deterministic baseline signal.
- Optionally ask OpenAI for a risk-aware signal refinement.
- Apply local risk controls before any order can be submitted.
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

Run a compile check:

```bash
python -m py_compile main.py ai_advisor.py coinbase_client.py config.py indicators.py models.py risk.py strategy.py tests/test_sigma.py
```

## Safety Defaults

- `COINBASE_DRY_RUN=1` prevents live orders.
- `COINBASE_ALLOW_SELLS=0` blocks sells unless you explicitly enable them.
- `COINBASE_MAX_TRADE_SIZE_USD` caps order size.
- `COINBASE_MAX_TRADES_PER_DAY` caps daily order count.
- The OpenAI advisor is optional and never bypasses local risk checks.
