import pandas as pd
import pytest

from app.backtest.signals import sma_crossover_signal


def test_signal_flat_before_enough_history():
    close = pd.Series(range(1, 11), dtype=float)  # 10 points
    signal = sma_crossover_signal(close, short_window=2, long_window=5)
    assert (signal.iloc[:4] == 0).all()  # long SMA needs 5 points to be defined


def test_signal_goes_long_on_upward_trend():
    close = pd.Series(range(1, 21), dtype=float)
    signal = sma_crossover_signal(close, short_window=3, long_window=5)
    assert signal.iloc[-1] == 1


def test_signal_flat_on_downward_trend():
    close = pd.Series(range(20, 0, -1), dtype=float)
    signal = sma_crossover_signal(close, short_window=3, long_window=5)
    assert signal.iloc[-1] == 0


def test_signal_crossover_transition():
    prices = [10, 9, 8, 7, 6, 5, 6, 8, 11, 15, 20]
    close = pd.Series(prices, dtype=float)
    signal = sma_crossover_signal(close, short_window=2, long_window=4)
    assert signal.iloc[-1] == 1   # rallied hard -> should be long by the end
    assert signal.iloc[4] == 0    # still declining at this point -> flat


def test_invalid_windows_raise():
    close = pd.Series(range(1, 11), dtype=float)
    with pytest.raises(ValueError):
        sma_crossover_signal(close, short_window=5, long_window=5)
    with pytest.raises(ValueError):
        sma_crossover_signal(close, short_window=0, long_window=5)
