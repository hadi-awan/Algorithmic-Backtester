"""ML-driven strategy: a RandomForestClassifier trained on in-sample
technical features, generating a long/flat signal on the out-of-sample
period only.

No lookahead: the model is fit exclusively on the in-sample (earlier)
rows produced by `app.features.split.chronological_split`, and every
prediction/signal is produced only for the out-of-sample (later) rows.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from app.features.engineering import FEATURE_COLUMNS, build_features
from app.features.split import chronological_split


@dataclass
class MLStrategyResult:
    signal: pd.Series                    # 0/1 signal, out-of-sample index only
    test_close: pd.Series                # close prices aligned to that same index
    feature_importances: dict[str, float]
    train_size: int
    test_size: int


def run_ml_strategy(
    ohlcv: pd.DataFrame,
    train_fraction: float = 0.7,
    probability_threshold: float = 0.5,
    n_estimators: int = 200,
    max_depth: int | None = 5,
    random_state: int = 42,
) -> MLStrategyResult:
    """Train on the in-sample split and return a long/flat signal for the
    out-of-sample split only.

    `ohlcv` is the raw OHLCV frame for the entire requested date range;
    this function performs the chronological train/test split itself,
    so callers never need to slice dates by hand (and can't accidentally
    leak test-period rows into training).
    """
    features = build_features(ohlcv)
    train_df, test_df = chronological_split(features, train_fraction)

    X_train = train_df[FEATURE_COLUMNS]
    y_train = train_df["label"]
    X_test = test_df[FEATURE_COLUMNS]

    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    classes = list(model.classes_)
    proba = model.predict_proba(X_test)
    if 1 in classes:
        proba_up = proba[:, classes.index(1)]
    else:
        # Training labels were all one class (e.g. a flat/degenerate
        # sample) -- the model never predicts "up", so stay flat.
        proba_up = np.zeros(len(X_test))

    signal = pd.Series(
        (proba_up >= probability_threshold).astype(int),
        index=X_test.index,
        name="signal",
    )

    importances = dict(zip(FEATURE_COLUMNS, model.feature_importances_.tolist()))

    # Close prices for the out-of-sample period, aligned to the raw OHLCV
    # frame (not the feature frame, whose index is shorter due to warm-up
    # rows being dropped).
    test_close = ohlcv.loc[test_df.index, "Close"]

    return MLStrategyResult(
        signal=signal,
        test_close=test_close,
        feature_importances=importances,
        train_size=len(train_df),
        test_size=len(test_df),
    )
