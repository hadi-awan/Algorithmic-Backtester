# Quant Signal Backtester

A full-stack backtesting tool that compares a rule-based technical strategy, a machine-learning strategy, and a buy-and-hold benchmark on real historical price data — built to demonstrate correct backtesting methodology (no lookahead bias) as much as the strategies themselves.

**Live demo:** [algorithmic-backtester.vercel.app](https://algorithmic-backtester.vercel.app/)
**API:** [quant-backtester-api-6eei.onrender.com](https://quant-backtester-api-6eei.onrender.com) (health check at `/api/health`)

> The backend is deployed on Render's free tier, which spins down after inactivity. The first request after idling can take 30–50 seconds to wake up — that's expected, not a bug.

> This is an educational/portfolio project, not investment advice. It does not model transaction costs, slippage, or taxes, and no result here should be read as a recommendation to trade any security.

## What it does

Given a ticker and a date range, the app runs three approaches over the exact same price data and shows them side by side:

- **Rule-based (SMA crossover)** — a classic trend-following signal: long when the short simple moving average is above the long one (defaults: 20-day / 50-day), flat otherwise.
- **Machine learning (Random Forest)** — a `RandomForestClassifier` trained on technical indicator features to predict next-day up/down moves, trained only on an in-sample (earlier) slice of the data and evaluated only on the later, out-of-sample slice it never saw during training.
- **Buy and hold** — the passive benchmark both strategies have to beat.

All three run through one shared backtest engine, so returns, Sharpe ratio, max drawdown, win rate, and trade logs are computed identically for each and are directly comparable.

## Why this exists

This project was built as a portfolio piece for quant/finance-adjacent roles, and it's deliberately structured around the mistake that makes most hobby backtests worthless: **lookahead bias**. It's easy to accidentally let a model "see the future" — training on data that includes the test period, or applying today's signal to today's return instead of tomorrow's. This project's core design decisions all exist to prevent that:

- The ML model is trained **only** on the chronologically earlier portion of the data (`chronological_split`), and every prediction it makes is for the later, out-of-sample portion only.
- Every feature is computed from data up to and including the current day only (rolling/EWM windows, never a forward-looking shift) — the only forward-looking column (`label`) is the training target and is never used as a model input.
- A strategy's signal for day *T* is only known at *T*'s close, so it's shifted forward one day before being applied to that day's return — you can't trade on information you wouldn't have had yet.
- The buy-and-hold benchmark is reported over both the full requested range and the same out-of-sample window as the ML strategy, so the three-way comparison is apples to apples rather than comparing different time periods.

## Architecture

```
backend/   FastAPI service — data ingestion, feature engineering, the three
           strategies, the shared backtest engine, and the HTTP API
frontend/  React (Vite + TypeScript) app — form, equity chart, metrics
           table, feature importance chart, and trade logs (Recharts)
```

The two are deployed independently (Render for the API, Vercel for the frontend) and talk to each other over HTTP; see [`DEPLOYMENT.md`](./DEPLOYMENT.md) for the full deploy walkthrough.

## Tech stack

**Backend:** Python, FastAPI, pandas, NumPy, scikit-learn, yfinance, pytest
**Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Recharts
**Deployment:** Render (backend, native Python runtime via `render.yaml`), Vercel (frontend)

## API

### `GET /api/health`

Returns `{"status": "ok"}`. Used for deployment health checks.

### `POST /api/backtest`

Request body:

```json
{
  "ticker": "AAPL",
  "start_date": "2018-01-01",
  "end_date": "2024-01-01",
  "sma_short": 20,
  "sma_long": 50,
  "train_fraction": 0.7,
  "probability_threshold": 0.5
}
```

`sma_short`, `sma_long`, `train_fraction`, and `probability_threshold` are all optional and default to the values above. The response includes, for each of the rule-based, ML, and buy-and-hold strategies: an equity curve, performance metrics (total return, CAGR, annualized Sharpe ratio, max drawdown, win rate, trade count), and a trade log — plus the ML model's feature importances and the train/test split sizes actually used. A buy-and-hold result is returned both for the full requested range and for the ML strategy's out-of-sample window specifically, so the frontend can show a fair three-way comparison.

Full request/response schemas: [`backend/app/api/schemas.py`](./backend/app/api/schemas.py).

## Backtesting engine details

- **Metrics** (`backend/app/backtest/metrics.py`): total return, CAGR (252 trading days/year), annualized Sharpe ratio, max drawdown, win rate, and trade count — one implementation shared by all three strategies.
- **Feature set** for the ML strategy (`backend/app/features/engineering.py`): 1-day and 5-day returns, 14-period RSI, MACD line and signal line, Bollinger Band position, 10-day rolling volatility, and volume change.
- **Model**: `RandomForestClassifier` (200 trees, max depth 5), predicting next-day up/down; a probability threshold (default 0.5) controls how confident the model needs to be before going long.
- **Data ingestion** (`backend/app/data/ingestion.py`): pulls daily OHLCV data from Yahoo Finance via `yfinance`, with retry-with-backoff for transient rate-limit failures, a 6-hour in-memory cache, and defensive handling of the occasional NaN closing price Yahoo returns for a not-yet-fully-settled recent bar.

## Running locally

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.api.main:app --reload
```

The API serves at `http://localhost:8000` (interactive docs at `/docs`).

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # set VITE_API_URL if the backend isn't on localhost:8000
npm run dev
```

The app serves at `http://localhost:5173`.

## Testing

```bash
cd backend
python3 -m pytest
```

60 tests covering metrics, signal generation, the backtest engine (including a dedicated regression test asserting a NaN price raises rather than silently corrupting a trade), feature engineering, the chronological split, the ML strategy, the end-to-end runner, and the API layer.

## Deployment

See [`DEPLOYMENT.md`](./DEPLOYMENT.md) for the full guide. Short version: Render deploys the backend from `render.yaml` (no Docker needed), Vercel deploys `frontend/` directly from this repo, and both redeploy automatically on every push to `main`.

## Limitations & future work

This is a v1, and it's intentionally simplified in ways worth being upfront about:

- **No transaction costs, slippage, or taxes are modeled.** Every backtest here assumes frictionless trading, which flatters both active strategies relative to how they'd perform with real execution costs.
- **A single chronological train/test split**, not walk-forward validation. One split is enough to demonstrate the no-lookahead methodology cleanly, but a more rigorous evaluation would retrain across multiple rolling windows to check whether the ML strategy's edge (if any) holds up across different market regimes.
- **No portfolio-level or multi-asset support** — one ticker at a time, no position sizing beyond fully-in/fully-out, no risk controls like max drawdown limits.
- **Free historical data only** (Yahoo Finance via `yfinance`), which is sufficient for daily-bar backtesting but not for anything intraday or for live trading.

Natural next steps: walk-forward validation, a configurable transaction-cost model, and a strategy-selection or ensembling layer that combines the rule-based and ML signals rather than only ever showing them side by side.
