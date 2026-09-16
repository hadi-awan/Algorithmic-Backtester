"""Tests for the data ingestion module. yfinance itself is mocked out so
these run fast, deterministically, and without live network access --
the retry/backoff and caching *logic* is what's under test, not Yahoo
Finance's actual API."""
from unittest.mock import patch

import pandas as pd
import pytest

from app.data import ingestion
from app.data.ingestion import DataIngestionError, clear_cache, fetch_ohlcv


def _make_raw_df(n=260):
    dates = pd.bdate_range("2023-01-01", periods=n)
    return pd.DataFrame(
        {
            "Open": range(n),
            "High": range(n),
            "Low": range(n),
            "Close": range(n),
            "Volume": [1_000_000] * n,
        },
        index=dates,
    )


@pytest.fixture(autouse=True)
def _reset_cache_and_sleep():
    clear_cache()
    # Don't actually wait through the exponential backoff in tests.
    with patch("app.data.ingestion.time.sleep", return_value=None):
        yield
    clear_cache()


def test_empty_ticker_raises_without_calling_yfinance():
    with patch("app.data.ingestion.yf.download") as mock_download:
        with pytest.raises(DataIngestionError):
            fetch_ohlcv("   ", "2023-01-01", "2024-01-01")
        mock_download.assert_not_called()


def test_successful_fetch_returns_expected_columns():
    with patch("app.data.ingestion.yf.download", return_value=_make_raw_df()):
        df = fetch_ohlcv("AAPL", "2023-01-01", "2024-01-01")
    assert list(df.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert len(df) == 260


def test_retries_on_empty_result_then_succeeds():
    """Simulates yfinance silently swallowing a rate-limit error and
    returning an empty frame on the first two calls, then succeeding."""
    empty = pd.DataFrame()
    good = _make_raw_df()
    with patch(
        "app.data.ingestion.yf.download", side_effect=[empty, empty, good]
    ) as mock_download:
        df = fetch_ohlcv("AAPL", "2023-01-01", "2024-01-01")
    assert len(df) == 260
    assert mock_download.call_count == 3


def test_raises_clear_error_after_exhausting_retries():
    empty = pd.DataFrame()
    with patch("app.data.ingestion.yf.download", return_value=empty) as mock_download:
        with pytest.raises(DataIngestionError, match="after 4 attempts"):
            fetch_ohlcv("AAPL", "2023-01-01", "2024-01-01")
    assert mock_download.call_count == ingestion._MAX_RETRIES + 1


def test_retries_on_raised_exception_then_succeeds():
    good = _make_raw_df()
    with patch(
        "app.data.ingestion.yf.download",
        side_effect=[ConnectionError("boom"), good],
    ) as mock_download:
        df = fetch_ohlcv("AAPL", "2023-01-01", "2024-01-01")
    assert len(df) == 260
    assert mock_download.call_count == 2


def test_exception_message_surfaced_after_all_retries_fail():
    with patch(
        "app.data.ingestion.yf.download",
        side_effect=ConnectionError("rate limited"),
    ):
        with pytest.raises(DataIngestionError, match="rate limited"):
            fetch_ohlcv("AAPL", "2023-01-01", "2024-01-01")


def test_rows_with_nan_close_are_dropped():
    """Yahoo occasionally returns a NaN Close for the most recent bar
    even though the row isn't entirely empty (Open/Volume etc. present).
    That row must be dropped rather than flowing into the backtest
    engine, where it would silently turn into a null deep in a metric."""
    df = _make_raw_df(n=260)
    # Corrupt only the Close value of the last row -- Open/High/Low/Volume
    # stay populated, so a naive dropna(how="all") would keep this row.
    df.loc[df.index[-1], "Close"] = float("nan")
    with patch("app.data.ingestion.yf.download", return_value=df):
        result = fetch_ohlcv("AAPL", "2023-01-01", "2024-01-01", min_trading_days=1)
    assert len(result) == 259
    assert not result["Close"].isna().any()


def test_insufficient_history_raises():
    with patch("app.data.ingestion.yf.download", return_value=_make_raw_df(n=50)):
        with pytest.raises(DataIngestionError, match="Only 50 trading days"):
            fetch_ohlcv("AAPL", "2023-01-01", "2023-03-01", min_trading_days=252)


def test_cache_avoids_second_network_call():
    with patch(
        "app.data.ingestion.yf.download", return_value=_make_raw_df()
    ) as mock_download:
        fetch_ohlcv("AAPL", "2023-01-01", "2024-01-01")
        fetch_ohlcv("AAPL", "2023-01-01", "2024-01-01")
    assert mock_download.call_count == 1


def test_cache_bypassed_when_use_cache_false():
    with patch(
        "app.data.ingestion.yf.download", return_value=_make_raw_df()
    ) as mock_download:
        fetch_ohlcv("AAPL", "2023-01-01", "2024-01-01")
        fetch_ohlcv("AAPL", "2023-01-01", "2024-01-01", use_cache=False)
    assert mock_download.call_count == 2


def test_different_date_ranges_are_cached_separately():
    with patch(
        "app.data.ingestion.yf.download", return_value=_make_raw_df()
    ) as mock_download:
        fetch_ohlcv("AAPL", "2023-01-01", "2024-01-01")
        fetch_ohlcv("AAPL", "2023-06-01", "2024-06-01")
    assert mock_download.call_count == 2
