"""API-layer tests. `fetch_ohlcv` is mocked out everywhere so these run
fast and deterministically without hitting Yahoo Finance -- the HTTP
layer, validation, and error handling are what's under test here, not
network reliability."""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.data.ingestion import DataIngestionError
from tests.conftest import make_synthetic_ohlcv

client = TestClient(app)


def _valid_payload(**overrides):
    payload = {
        "ticker": "AAPL",
        "start_date": "2023-01-01",
        "end_date": "2024-06-01",
        "sma_short": 10,
        "sma_long": 30,
        "train_fraction": 0.7,
        "probability_threshold": 0.5,
    }
    payload.update(overrides)
    return payload


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_backtest_happy_path():
    ohlcv = make_synthetic_ohlcv(n=400, seed=1)
    with patch("app.api.main.fetch_ohlcv", return_value=ohlcv):
        response = client.post("/api/backtest", json=_valid_payload())

    assert response.status_code == 200
    body = response.json()

    assert body["ticker"] == "AAPL"
    for key in ("rule_based", "ml", "buy_and_hold", "buy_and_hold_out_of_sample"):
        assert key in body
        assert len(body[key]["equity_curve"]) > 0
        for metric in ("total_return", "cagr", "sharpe_ratio", "max_drawdown", "win_rate", "num_trades"):
            assert metric in body[key]["metrics"]

    # ML's equity curve must be strictly shorter than rule-based's (full
    # range) -- it only covers the out-of-sample tail.
    assert len(body["ml"]["equity_curve"]) < len(body["rule_based"]["equity_curve"])
    assert len(body["ml"]["equity_curve"]) == len(body["buy_and_hold_out_of_sample"]["equity_curve"])

    assert isinstance(body["feature_importances"], dict)
    assert len(body["feature_importances"]) == 8
    assert body["train_size"] > 0
    assert body["test_size"] > 0


def test_backtest_invalid_ticker_returns_400():
    with patch(
        "app.api.main.fetch_ohlcv",
        side_effect=DataIngestionError("No data found for ticker 'ZZZZZZ'."),
    ):
        response = client.post("/api/backtest", json=_valid_payload(ticker="ZZZZZZ"))
    assert response.status_code == 400
    assert "ZZZZZZ" in response.json()["detail"]


def test_backtest_end_before_start_returns_422():
    response = client.post(
        "/api/backtest",
        json=_valid_payload(start_date="2024-01-01", end_date="2023-01-01"),
    )
    assert response.status_code == 422  # pydantic model_validator failure


def test_backtest_sma_short_not_less_than_long_returns_422():
    response = client.post("/api/backtest", json=_valid_payload(sma_short=50, sma_long=50))
    assert response.status_code == 422


def test_backtest_empty_ticker_returns_422():
    response = client.post("/api/backtest", json=_valid_payload(ticker=""))
    assert response.status_code == 422


def test_backtest_probability_threshold_out_of_range_returns_422():
    response = client.post("/api/backtest", json=_valid_payload(probability_threshold=1.5))
    assert response.status_code == 422


def test_backtest_uses_request_sma_windows():
    ohlcv = make_synthetic_ohlcv(n=400, seed=2)
    with patch("app.api.main.fetch_ohlcv", return_value=ohlcv) as mock_fetch, \
         patch("app.api.main.run_full_backtest") as mock_runner:
        # We only need to confirm the request's parsed params are passed
        # through correctly; the runner's own correctness is covered by
        # tests/test_runner.py.
        from app.backtest.runner import run_full_backtest as real_runner
        mock_runner.side_effect = real_runner

        client.post("/api/backtest", json=_valid_payload(sma_short=15, sma_long=45))

        mock_fetch.assert_called_once()
        _, kwargs = mock_runner.call_args
        assert kwargs["sma_short"] == 15
        assert kwargs["sma_long"] == 45
