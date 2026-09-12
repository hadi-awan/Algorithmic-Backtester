import numpy as np
import pandas as pd
import pytest

from app.backtest import metrics as m


def test_total_return_simple():
    equity = pd.Series([1.0, 1.1, 1.21])
    assert m.total_return(equity) == pytest.approx(0.21)


def test_total_return_flat():
    equity = pd.Series([1.0, 1.0, 1.0])
    assert m.total_return(equity) == pytest.approx(0.0)


def test_cagr_matches_known_example():
    # Doubling over exactly 252 periods (1 trading year) => CAGR of 100%
    equity = pd.Series([1.0] * 252 + [2.0])
    result = m.cagr(equity, periods_per_year=252)
    assert result == pytest.approx(1.0, abs=1e-6)


def test_cagr_zero_when_flat():
    equity = pd.Series([1.0] * 10)
    assert m.cagr(equity) == pytest.approx(0.0)


def test_sharpe_ratio_zero_for_zero_volatility():
    returns = pd.Series([0.0] * 10)
    assert m.sharpe_ratio(returns) == 0.0


def test_sharpe_ratio_known_example():
    returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015])
    sharpe = m.sharpe_ratio(returns, periods_per_year=252)
    manual_mean = returns.mean()
    manual_std = returns.std(ddof=1)
    expected = manual_mean / manual_std * np.sqrt(252)
    assert sharpe == pytest.approx(expected)
    assert sharpe > 0  # positive mean returns -> positive Sharpe


def test_max_drawdown_simple():
    equity = pd.Series([1.0, 1.2, 0.9, 1.1])
    assert m.max_drawdown(equity) == pytest.approx(-0.25)


def test_max_drawdown_no_drawdown():
    equity = pd.Series([1.0, 1.1, 1.2, 1.3])
    assert m.max_drawdown(equity) == pytest.approx(0.0)


def test_win_rate():
    trade_returns = pd.Series([0.05, -0.02, 0.01, -0.01])
    assert m.win_rate(trade_returns) == pytest.approx(0.5)


def test_win_rate_no_trades():
    assert m.win_rate(pd.Series([], dtype=float)) == 0.0


def test_num_trades_counts_entries_only():
    signal = pd.Series([0, 1, 1, 0, 1, 0, 1, 1, 1])
    assert m.num_trades(signal) == 3
