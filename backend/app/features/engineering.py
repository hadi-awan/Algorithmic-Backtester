"""Technical indicator feature engineering for the ML strategy.

Every feature at row t is computed using data up to and including row t
only (rolling/ewm windows, never a forward-looking shift), so the
feature computation itself introduces no lookahead. The only
forward-looking column is `label`, which is the training target and
must never be used as a model input.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "return_1d",
    "return_5d",
    "rsi_14",
    "macd",
    "macd_signal",
    "bollinger_position",
    "volatility_10d",
    "volume_change",
]


def _rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)  # neutral RSI where undefined (e.g. no losses seen yet)


def _macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line


def _bollinger_position(close: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.Series:
    """Where price sits within its Bollinger Band, clipped to [0, 1]
    (0 = at/below the lower band, 1 = at/above the upper band)."""
    sma = close.rolling(window=window, min_periods=window).mean()
    std = close.rolling(window=window, min_periods=window).std()
    upper = sma + num_std * std
    lower = sma - num_std * std
    band_width = (upper - lower).replace(0, np.nan)
    position = (close - lower) / band_width
    return position.clip(lower=0, upper=1)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build the model feature matrix + next-day up/down label from an
    OHLCV DataFrame (as returned by `app.data.ingestion.fetch_ohlcv`).

    Returns a DataFrame with `FEATURE_COLUMNS` plus a `label` column (1
    if next day's close is higher than today's, else 0), indexed the
    same as `df`. Rows without enough warm-up history for every
    indicator, and the final row (which has no next-day label yet), are
    dropped.
    """
    close = df["Close"]
    volume = df["Volume"]

    features = pd.DataFrame(index=df.index)
    features["return_1d"] = close.pct_change(1, fill_method=None)
    features["return_5d"] = close.pct_change(5, fill_method=None)
    features["rsi_14"] = _rsi(close, window=14)

    macd_line, signal_line = _macd(close)
    features["macd"] = macd_line
    features["macd_signal"] = signal_line

    features["bollinger_position"] = _bollinger_position(close)
    features["volatility_10d"] = close.pct_change(fill_method=None).rolling(window=10).std()
    features["volume_change"] = volume.pct_change(fill_method=None)

    # Target label only -- built with a forward shift, so it must never
    # be treated as a feature. The final row has no next-day close to
    # compare against; that must produce a real NaN (not a silent
    # False/0) so dropna() removes it rather than training on a bogus
    # label.
    next_close = close.shift(-1)
    features["label"] = np.where(
        next_close.notna(), (next_close > close).astype(float), np.nan
    )

    features = features.dropna()
    features["label"] = features["label"].astype(int)
    return features
