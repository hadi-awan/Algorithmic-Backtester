"""Shared performance metrics used for every strategy (rule-based, ML,
and buy-and-hold) so results are always computed through one consistent
set of formulas rather than three separate implementations.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252


def total_return(equity_curve: pd.Series) -> float:
    """Cumulative return over the full period, e.g. 0.25 == +25%."""
    if len(equity_curve) < 2:
        return 0.0
    return float(equity_curve.iloc[-1] / equity_curve.iloc[0] - 1)


def cagr(equity_curve: pd.Series, periods_per_year: int = TRADING_DAYS_PER_YEAR) -> float:
    """Compound annual growth rate implied by the equity curve's length."""
    if len(equity_curve) < 2:
        return 0.0
    n_periods = len(equity_curve) - 1
    years = n_periods / periods_per_year
    if years <= 0:
        return 0.0
    ratio = equity_curve.iloc[-1] / equity_curve.iloc[0]
    if ratio <= 0:
        return -1.0
    return float(ratio ** (1 / years) - 1)


def sharpe_ratio(
    returns: pd.Series,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
    risk_free_rate: float = 0.0,
) -> float:
    """Annualized Sharpe ratio of a periodic (e.g. daily) returns series."""
    returns = returns.dropna()
    if len(returns) < 2:
        return 0.0
    period_rf = risk_free_rate / periods_per_year
    excess = returns - period_rf
    std = excess.std(ddof=1)
    if std == 0 or np.isnan(std):
        return 0.0
    return float(excess.mean() / std * np.sqrt(periods_per_year))


def max_drawdown(equity_curve: pd.Series) -> float:
    """Largest peak-to-trough decline, returned as a negative fraction."""
    if len(equity_curve) < 2:
        return 0.0
    running_max = equity_curve.cummax()
    drawdown = equity_curve / running_max - 1
    return float(drawdown.min())


def win_rate(trade_returns: pd.Series) -> float:
    """Fraction of closed trades with a positive return. 0.0 if no trades."""
    if len(trade_returns) == 0:
        return 0.0
    return float((trade_returns > 0).sum() / len(trade_returns))


def num_trades(signal: pd.Series) -> int:
    """Count of position entries (0->1 transitions) in a long/flat signal."""
    changes = signal.diff().fillna(0)
    return int((changes == 1).sum())
