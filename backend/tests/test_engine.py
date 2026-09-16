import pandas as pd
import pytest

from app.backtest.engine import run_backtest, run_buy_and_hold


def _dates(n):
    return pd.date_range("2024-01-01", periods=n, freq="D")


def test_buy_and_hold_matches_raw_return():
    close = pd.Series([100, 105, 110, 108, 120], index=_dates(5))
    result = run_buy_and_hold(close)
    expected_total_return = 120 / 100 - 1
    assert result.total_return == pytest.approx(expected_total_return)


def test_signal_is_shifted_no_lookahead():
    # Signal flips to "long" on day index 1; because of the 1-day shift,
    # the strategy must NOT capture day 1's own return (it only learns
    # about the signal at day 1's close), only day 2 onward.
    close = pd.Series([100, 110, 121, 133.1], index=_dates(4))
    signal = pd.Series([0, 1, 1, 1], index=_dates(4))
    result = run_backtest(close, signal)
    day1_return = result.strategy_returns.iloc[1]
    assert day1_return == pytest.approx(0.0)
    day2_return = result.strategy_returns.iloc[2]
    assert day2_return == pytest.approx(0.10)


def test_nan_in_close_raises():
    close = pd.Series([100, 105, float("nan"), 110], index=_dates(4))
    signal = pd.Series([1, 1, 1, 1], index=_dates(4))
    with pytest.raises(ValueError, match="missing values"):
        run_backtest(close, signal)


def test_mismatched_index_raises():
    # Same length, but a shifted (different) index -> engine must reject
    # rather than silently aligning/misaligning dates.
    close = pd.Series([1, 2, 3], index=_dates(3))
    signal = pd.Series([1, 1, 1], index=_dates(3) + pd.Timedelta(days=1))
    with pytest.raises(ValueError):
        run_backtest(close, signal)


def test_trade_extraction_counts_and_dates():
    close = pd.Series([100, 105, 110, 108, 115, 120], index=_dates(6))
    signal = pd.Series([0, 1, 1, 0, 1, 1], index=_dates(6))
    result = run_backtest(close, signal)
    assert len(result.trades) == 2
    assert result.num_trades == 2


def test_flat_signal_produces_no_trades_and_zero_return():
    close = pd.Series([100, 101, 99, 102], index=_dates(4))
    signal = pd.Series([0, 0, 0, 0], index=_dates(4))
    result = run_backtest(close, signal)
    assert result.num_trades == 0
    assert result.total_return == pytest.approx(0.0)
