"""Chronological train/test split for the ML strategy.

The split is always time-ordered (never shuffled): the model is trained
only on the earlier (in-sample) portion, and the later (out-of-sample)
portion is reserved for generating predictions/signals and for the
backtest and equity curve shown to the user -- this is what prevents
lookahead bias in the ML strategy.
"""
from __future__ import annotations

import pandas as pd


def chronological_split(data: pd.DataFrame, train_fraction: float = 0.7):
    """Split a time-indexed DataFrame into (train, test), preserving
    chronological order. Raises ValueError if train_fraction is not in
    (0, 1), if the index isn't sorted, or if either split would be
    empty.
    """
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between 0 and 1 (exclusive).")
    if not data.index.is_monotonic_increasing:
        raise ValueError("data must be sorted chronologically before splitting.")

    split_idx = int(len(data) * train_fraction)
    train = data.iloc[:split_idx]
    test = data.iloc[split_idx:]

    if len(train) == 0 or len(test) == 0:
        raise ValueError("train_fraction produced an empty train or test split.")

    return train, test
