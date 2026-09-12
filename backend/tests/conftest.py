"""Shared test fixtures."""
import numpy as np
import pandas as pd
import pytest


def make_synthetic_ohlcv(n=300, seed=42, start="2023-01-01"):
    """A reproducible synthetic daily OHLCV series: a mild-upward random
    walk, enough rows to clear every indicator's warm-up window with
    plenty left over for both a train and a test split."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(start=start, periods=n)
    daily_returns = rng.normal(loc=0.0003, scale=0.012, size=n)
    close = 100 * np.cumprod(1 + daily_returns)

    high = close * (1 + rng.uniform(0, 0.01, size=n))
    low = close * (1 - rng.uniform(0, 0.01, size=n))
    open_ = close * (1 + rng.normal(0, 0.003, size=n))
    volume = rng.integers(1_000_000, 5_000_000, size=n).astype(float)

    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=dates,
    )


@pytest.fixture
def synthetic_ohlcv():
    return make_synthetic_ohlcv()
