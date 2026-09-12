import pandas as pd

from app.features.engineering import FEATURE_COLUMNS, build_features
from tests.conftest import make_synthetic_ohlcv


def test_build_features_has_expected_columns(synthetic_ohlcv):
    features = build_features(synthetic_ohlcv)
    for col in FEATURE_COLUMNS:
        assert col in features.columns
    assert "label" in features.columns


def test_build_features_no_nans_after_warmup(synthetic_ohlcv):
    features = build_features(synthetic_ohlcv)
    assert not features.isna().any().any()


def test_rsi_bounded_0_100(synthetic_ohlcv):
    features = build_features(synthetic_ohlcv)
    assert features["rsi_14"].between(0, 100).all()


def test_bollinger_position_bounded_0_1(synthetic_ohlcv):
    features = build_features(synthetic_ohlcv)
    assert features["bollinger_position"].between(0, 1).all()


def test_label_reflects_next_day_direction(synthetic_ohlcv):
    """Property check: the label at every surviving row must equal
    whether *that row's own* close was followed by a higher close the
    next day, taken directly from the original (pre-feature-engineering)
    close series -- not just re-deriving the same shift(-1) expression
    the implementation uses."""
    features = build_features(synthetic_ohlcv)
    close = synthetic_ohlcv["Close"]
    next_day_up = (close.shift(-1) > close).astype(int)
    expected = next_day_up.loc[features.index]
    assert (features["label"] == expected).all()


def test_label_excludes_final_row_with_no_next_day(synthetic_ohlcv):
    """The final row has no next-day close to compute a label from, so
    it must be dropped rather than silently mislabeled."""
    features = build_features(synthetic_ohlcv)
    assert synthetic_ohlcv.index[-1] not in features.index


def test_features_unaffected_by_changing_future_prices():
    """No-lookahead check: a feature value at row t must depend only on
    data up to and including row t. Changing a *future* close price
    (beyond t) should not change the feature computed at row t, even
    though it will change the label at row t-1."""
    n = 60
    base = make_synthetic_ohlcv(n=n, seed=1)
    modified = base.copy()
    # Perturb only the final day's close -- far beyond any feature's
    # rolling window for the row we're checking below.
    modified.iloc[-1, modified.columns.get_loc("Close")] *= 1.5

    features_base = build_features(base)
    features_modified = build_features(modified)

    check_idx = features_base.index[-5]  # well before the perturbed day
    for col in FEATURE_COLUMNS:
        assert features_base.loc[check_idx, col] == features_modified.loc[check_idx, col], (
            f"feature '{col}' at {check_idx} changed when a later price changed"
        )
