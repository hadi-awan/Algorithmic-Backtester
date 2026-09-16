"""Data ingestion module: fetches OHLCV data from yfinance with a simple
in-memory cache, retry-with-backoff for transient failures (Yahoo
Finance rate-limits aggressively), and defensive error handling so
callers (the API layer) never see raw yfinance/requests exceptions.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass

import pandas as pd
import yfinance as yf


class DataIngestionError(Exception):
    """Raised when ticker data cannot be fetched or is insufficient."""


@dataclass
class _CacheEntry:
    data: pd.DataFrame
    fetched_at: float


_CACHE: dict[str, _CacheEntry] = {}
# Daily OHLCV history for a completed date range essentially never
# changes (only "today", if included, is still moving) -- a long TTL
# means repeat requests for the same ticker/range are served from cache
# instead of hitting Yahoo Finance again, which both speeds things up
# and reduces the odds of getting rate-limited on a live demo.
_CACHE_TTL_SECONDS = 6 * 60 * 60  # 6 hours

_MAX_RETRIES = 3
_INITIAL_BACKOFF_SECONDS = 2.0


def _cache_key(ticker: str, start: str, end: str) -> str:
    return f"{ticker.upper()}|{start}|{end}"


def clear_cache() -> None:
    """Used by tests to reset module-level cache state between runs."""
    _CACHE.clear()


def _download_with_retry(ticker: str, start_date: str, end_date: str):
    """Attempt the yfinance download up to `_MAX_RETRIES` extra times
    with exponential backoff (plus jitter) between attempts.

    yfinance often swallows a rate-limit error internally and just
    returns an empty DataFrame (rather than raising), so both an empty
    result and a raised exception are treated as retryable. Returns
    (raw_dataframe_or_None, last_exception_or_None) from the final
    attempt.
    """
    last_exc: Exception | None = None
    raw = None

    for attempt in range(_MAX_RETRIES + 1):
        last_exc = None
        try:
            raw = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                progress=False,
                auto_adjust=True,
            )
        except Exception as exc:  # yfinance/requests can raise many types
            last_exc = exc
            raw = None

        if raw is not None and not raw.empty:
            return raw, None

        if attempt < _MAX_RETRIES:
            backoff = _INITIAL_BACKOFF_SECONDS * (2 ** attempt) + random.uniform(0, 0.5)
            time.sleep(backoff)

    return raw, last_exc


def fetch_ohlcv(
    ticker: str,
    start_date: str,
    end_date: str,
    min_trading_days: int = 252,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Fetch daily OHLCV data for `ticker` between start_date and end_date.

    Returns a DataFrame indexed by date with columns:
    Open, High, Low, Close, Volume.

    Raises DataIngestionError with a clear, user-facing message on any
    failure (missing ticker, invalid ticker, no data, insufficient
    history, or a rate limit that persisted across all retries) rather
    than letting the raw yfinance/requests exception propagate up to the
    API layer.
    """
    if not ticker or not ticker.strip():
        raise DataIngestionError("Ticker symbol is required.")

    ticker = ticker.strip().upper()
    key = _cache_key(ticker, start_date, end_date)

    if use_cache and key in _CACHE:
        entry = _CACHE[key]
        if time.time() - entry.fetched_at < _CACHE_TTL_SECONDS:
            return entry.data.copy()

    raw, last_exc = _download_with_retry(ticker, start_date, end_date)

    if raw is None or raw.empty:
        if last_exc is not None:
            raise DataIngestionError(
                f"Failed to fetch data for '{ticker}' after "
                f"{_MAX_RETRIES + 1} attempts: {last_exc}"
            ) from last_exc
        raise DataIngestionError(
            f"No data found for ticker '{ticker}' in the given date range "
            f"after {_MAX_RETRIES + 1} attempts. This can mean the symbol is "
            "invalid, the range contains no trading days, or Yahoo Finance "
            "is temporarily rate-limiting requests -- try again in a moment."
        )

    # yfinance can return a MultiIndex column frame even for a single ticker
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    missing_cols = {"Open", "High", "Low", "Close", "Volume"} - set(raw.columns)
    if missing_cols:
        raise DataIngestionError(
            f"Unexpected data format for '{ticker}': missing columns {missing_cols}."
        )

    raw = raw[["Open", "High", "Low", "Close", "Volume"]].dropna(how="all")

    # Yahoo Finance occasionally returns a NaN Close for the most recent
    # bar (e.g. a session that hasn't fully settled/adjusted yet) even
    # though the row isn't entirely empty. The whole pipeline is keyed
    # on Close, so a single NaN here can silently turn into a null deep
    # in a downstream metric (e.g. a trade's exit price) rather than a
    # clear error -- drop any such row up front instead.
    raw = raw.dropna(subset=["Close"])

    if len(raw) < min_trading_days:
        raise DataIngestionError(
            f"Only {len(raw)} trading days found for '{ticker}' between "
            f"{start_date} and {end_date}; at least {min_trading_days} are "
            "required for a reliable backtest. Widen the date range."
        )

    _CACHE[key] = _CacheEntry(data=raw.copy(), fetched_at=time.time())
    return raw
