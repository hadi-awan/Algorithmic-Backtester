import pandas as pd
import pytest

from app.models.classifier import run_ml_strategy
from tests.conftest import make_synthetic_ohlcv


def test_signal_index_is_out_of_sample_only(synthetic_ohlcv):
    result = run_ml_strategy(synthetic_ohlcv, train_fraction=0.7)
    from app.features.engineering import build_features
    from app.features.split import chronological_split

    features = build_features(synthetic_ohlcv)
    train_df, test_df = chronological_split(features, 0.7)

    assert list(result.signal.index) == list(test_df.index)
    assert result.train_size == len(train_df)
    assert result.test_size == len(test_df)


def test_signal_is_binary():
    ohlcv = make_synthetic_ohlcv(n=200, seed=7)
    result = run_ml_strategy(ohlcv)
    assert set(result.signal.unique()).issubset({0, 1})


def test_feature_importances_cover_all_features():
    from app.features.engineering import FEATURE_COLUMNS

    ohlcv = make_synthetic_ohlcv(n=200, seed=7)
    result = run_ml_strategy(ohlcv)
    assert set(result.feature_importances.keys()) == set(FEATURE_COLUMNS)
    total = sum(result.feature_importances.values())
    assert 0.99 <= total <= 1.01  # RandomForest importances sum to ~1


def test_training_is_unaffected_by_out_of_sample_prices():
    """No-lookahead check on the model itself: perturbing only the
    out-of-sample tail of the price series must not change the trained
    model's feature importances, since those rows are never used for
    training."""
    base = make_synthetic_ohlcv(n=250, seed=3)
    perturbed = base.copy()
    # Corrupt the last 20% of closes -- squarely inside the OOS window
    # for the default 0.7 train fraction.
    tail_start = int(len(base) * 0.85)
    perturbed.iloc[tail_start:, perturbed.columns.get_loc("Close")] *= 3.0

    result_base = run_ml_strategy(base, train_fraction=0.7)
    result_perturbed = run_ml_strategy(perturbed, train_fraction=0.7)

    assert result_base.train_size == result_perturbed.train_size
    for feature in result_base.feature_importances:
        assert result_base.feature_importances[feature] == pytest.approx(
            result_perturbed.feature_importances[feature], abs=1e-9
        )


def test_probability_threshold_is_monotonic_in_strictness():
    """A higher probability threshold should never produce *more* long
    signals than a lower one (it's a stricter bar to go long)."""
    ohlcv = make_synthetic_ohlcv(n=250, seed=11)
    loose = run_ml_strategy(ohlcv, probability_threshold=0.4)
    strict = run_ml_strategy(ohlcv, probability_threshold=0.6)
    assert strict.signal.sum() <= loose.signal.sum()
