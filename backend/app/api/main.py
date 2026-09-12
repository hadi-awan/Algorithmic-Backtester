"""FastAPI application: wraps the data ingestion + backtest engine built
in Phases 1-2 into two HTTP endpoints.

  GET  /api/health    -- basic health check for deployment monitoring
  POST /api/backtest  -- run rule-based, ML, and buy-and-hold, return
                         equity curves, metrics, feature importances,
                         and trade logs

No transaction costs/slippage are modeled anywhere in this pipeline
(v1 simplifying assumption -- see the README).
"""
from __future__ import annotations

import os

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.backtest.engine import BacktestResult
from app.backtest.runner import FullBacktestResult, run_full_backtest
from app.data.ingestion import DataIngestionError, fetch_ohlcv

from .schemas import (
    BacktestRequest,
    BacktestResponse,
    EquityPoint,
    HealthResponse,
    MetricsOut,
    StrategyResult,
    TradeOut,
)

app = FastAPI(
    title="Quant Signal Backtester API",
    description=(
        "Backtests a rule-based SMA-crossover strategy and an ML-driven "
        "strategy against a buy-and-hold benchmark. Educational/portfolio "
        "project -- not investment advice; does not model transaction "
        "costs, slippage, or taxes."
    ),
    version="0.1.0",
)

# CORS_ALLOWED_ORIGINS is a comma-separated list of allowed frontend
# origins (e.g. "https://your-app.vercel.app,http://localhost:5173").
# Unset (local dev default) falls back to "*" so the Vite dev server
# works out of the box; set it explicitly in production (Phase 5) so
# the deployed API isn't wide open to any origin.
_raw_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "*")
_allowed_origins = (
    ["*"] if _raw_origins.strip() == "*" else [o.strip() for o in _raw_origins.split(",") if o.strip()]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


def _serialize(result: BacktestResult) -> StrategyResult:
    equity_curve = [
        EquityPoint(date=str(idx.date() if hasattr(idx, "date") else idx), value=float(v))
        for idx, v in result.equity_curve.items()
    ]
    trades = [
        TradeOut(
            entry_date=t.entry_date,
            exit_date=t.exit_date,
            entry_price=t.entry_price,
            exit_price=t.exit_price,
            return_pct=t.return_pct,
        )
        for t in result.trades
    ]
    metrics = MetricsOut(
        total_return=result.total_return,
        cagr=result.cagr,
        sharpe_ratio=result.sharpe_ratio,
        max_drawdown=result.max_drawdown,
        win_rate=result.win_rate,
        num_trades=result.num_trades,
    )
    return StrategyResult(equity_curve=equity_curve, metrics=metrics, trades=trades)


def _build_response(request: BacktestRequest, result: FullBacktestResult) -> BacktestResponse:
    oos_start = result.ml.equity_curve.index.min()
    oos_start_str = str(oos_start.date() if hasattr(oos_start, "date") else oos_start)

    return BacktestResponse(
        ticker=request.ticker.strip().upper(),
        start_date=str(request.start_date),
        end_date=str(request.end_date),
        out_of_sample_start_date=oos_start_str,
        rule_based=_serialize(result.rule_based),
        ml=_serialize(result.ml),
        buy_and_hold=_serialize(result.buy_and_hold_full),
        buy_and_hold_out_of_sample=_serialize(result.buy_and_hold),
        feature_importances=result.ml_meta.feature_importances,
        train_size=result.ml_meta.train_size,
        test_size=result.ml_meta.test_size,
    )


@app.post("/api/backtest", response_model=BacktestResponse)
def backtest(request: BacktestRequest) -> BacktestResponse:
    try:
        ohlcv: pd.DataFrame = fetch_ohlcv(
            request.ticker, str(request.start_date), str(request.end_date)
        )
    except DataIngestionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        result = run_full_backtest(
            ohlcv,
            sma_short=request.sma_short,
            sma_long=request.sma_long,
            train_fraction=request.train_fraction,
            probability_threshold=request.probability_threshold,
        )
    except ValueError as exc:
        # e.g. an ML train/test split that ends up empty for a very
        # short date range -- a bad-input problem, not a server error.
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _build_response(request, result)
