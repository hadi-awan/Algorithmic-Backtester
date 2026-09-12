"""Orchestrates running all three approaches -- rule-based, ML, and
buy-and-hold -- through the single shared backtest engine, so the API
layer (Phase 3) has one function to call per backtest request.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.backtest.engine import BacktestResult, run_backtest, run_buy_and_hold
from app.backtest.signals import sma_crossover_signal
from app.models.classifier import MLStrategyResult, run_ml_strategy


@dataclass
class FullBacktestResult:
    rule_based: BacktestResult          # full requested date range
    ml: BacktestResult                  # out-of-sample period only
    ml_meta: MLStrategyResult           # feature importances, split sizes
    buy_and_hold: BacktestResult        # restricted to the ML out-of-sample period
    buy_and_hold_full: BacktestResult   # full requested date range


def run_full_backtest(
    ohlcv: pd.DataFrame,
    sma_short: int = 20,
    sma_long: int = 50,
    train_fraction: float = 0.7,
    probability_threshold: float = 0.5,
) -> FullBacktestResult:
    """Run the rule-based, ML, and buy-and-hold approaches on the same
    OHLCV data, all through `app.backtest.engine.run_backtest` so the
    three sets of metrics are always computed identically.

    Two buy-and-hold results are returned: `buy_and_hold_full` spans the
    entire requested range (for reference), and `buy_and_hold` is
    restricted to the same out-of-sample window as the ML strategy so
    the three-way comparison the frontend renders is apples to apples.
    """
    close = ohlcv["Close"]

    rule_signal = sma_crossover_signal(close, sma_short, sma_long)
    rule_result = run_backtest(close, rule_signal)
    buy_and_hold_full = run_buy_and_hold(close)

    ml_meta = run_ml_strategy(
        ohlcv,
        train_fraction=train_fraction,
        probability_threshold=probability_threshold,
    )
    ml_result = run_backtest(ml_meta.test_close, ml_meta.signal)
    buy_and_hold_oos = run_buy_and_hold(ml_meta.test_close)

    return FullBacktestResult(
        rule_based=rule_result,
        ml=ml_result,
        ml_meta=ml_meta,
        buy_and_hold=buy_and_hold_oos,
        buy_and_hold_full=buy_and_hold_full,
    )
