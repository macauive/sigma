# Coinbase Bot

This repository runs a Coinbase Advanced Trade bot. It is dry-run first: the bot
can fetch public candle data, build a deterministic baseline signal, optionally
ask OpenAI for a risk-aware refinement, pass the result through local risk
controls, and print the order it would place.

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Create a local `coinbase.env` from `.env.example` and fill in placeholders:

   ```bash
   cp .env.example coinbase.env
   ```

3. Run one dry-run cycle:

   ```bash
   COINBASE_LOOP_INTERVAL_SECONDS=0 python main.py
   ```

4. Run the focused safety tests:

   ```bash
   python -m unittest tests/test_coinbase_bot.py
   ```

## Safety Defaults

- `COINBASE_DRY_RUN=1` prevents live Coinbase orders.
- Live trading also requires valid `COINBASE_API_KEY` and `COINBASE_API_SECRET`.
- SELL signals are blocked until `COINBASE_ALLOW_SELLS=1`.
- Order sizes are clipped by `COINBASE_MAX_TRADE_SIZE_USD`.
- AI is advisory only. The deterministic risk manager gets the final say.

## Strategy Shape

The first strategy is intentionally boring:

- BUY only when short-term trend, RSI, momentum, and volume are constructive.
- SELL only when momentum weakens or RSI looks stretched.
- HOLD otherwise.

That gives us a baseline we can backtest and improve instead of letting an LLM
invent trades in the hot path.
