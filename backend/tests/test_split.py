import pandas as pd
import pytest

from app.features.split import chronological_split


def _df(n):
    return pd.DataFrame({"x": range(n)}, index=pd.bdate_range("2023-01-01", periods=n))


def test_split_respects_fraction_roughly():
    data = _df(100)
    train, test = chronological_split(data, train_fraction=0.7)
    assert len(train) == 70
    assert len(test) == 30


def test_split_preserves_chronological_order_and_no_overlap():
    data = _df(50)
    train, test = chronological_split(data, train_fraction=0.6)
    assert train.index.max() < test.index.min()
    assert set(train.index).isdisjoint(set(test.index))
    assert len(train) + len(test) == len(data)


def test_split_invalid_fraction_raises():
    data = _df(10)
    with pytest.raises(ValueError):
        chronological_split(data, train_fraction=0.0)
    with pytest.raises(ValueError):
        chronological_split(data, train_fraction=1.0)
    with pytest.raises(ValueError):
        chronological_split(data, train_fraction=-0.2)


def test_split_unsorted_index_raises():
    data = _df(10)
    shuffled = data.iloc[::-1]
    with pytest.raises(ValueError):
        chronological_split(shuffled, train_fraction=0.5)


def test_split_too_small_for_fraction_raises():
    data = _df(2)
    with pytest.raises(ValueError):
        chronological_split(data, train_fraction=0.01)
