"""Signal generation for the rule-based (SMA crossover) strategy."""
from __future__ import annotations

import pandas as pd


def sma_crossover_signal(
    close: pd.Series, short_window: int = 20, long_window: int = 50
) -> pd.Series:
    """Return a 0/1 long-flat signal series aligned to `close`'s index.

    Signal is 1 (long) on any day where the short SMA is above the long
    SMA, and 0 (flat) otherwise. Days before the long SMA has enough
    history are forced to 0 (flat) rather than left NaN.
    """
    if short_window <= 0 or long_window <= 0:
        raise ValueError("SMA windows must be positive integers.")
    if short_window >= long_window:
        raise ValueError("short_window must be less than long_window.")

    short_sma = close.rolling(window=short_window, min_periods=short_window).mean()
    long_sma = close.rolling(window=long_window, min_periods=long_window).mean()

    signal = (short_sma > long_sma).astype(int)
    signal[long_sma.isna()] = 0
    signal.name = "signal"
    return signal
