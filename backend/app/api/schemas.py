"""Pydantic request/response models for the /api/backtest endpoint."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, model_validator


class BacktestRequest(BaseModel):
    ticker: str = Field(..., min_length=1, description="e.g. 'AAPL'")
    start_date: date
    end_date: date
    sma_short: int = Field(20, gt=0, description="Short SMA window (days)")
    sma_long: int = Field(50, gt=0, description="Long SMA window (days)")
    train_fraction: float = Field(
        0.7, gt=0, lt=1, description="Fraction of the range used for ML training"
    )
    probability_threshold: float = Field(
        0.5, ge=0, le=1, description="Min predicted P(up) to go long in the ML strategy"
    )

    @model_validator(mode="after")
    def _check_ranges(self) -> "BacktestRequest":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date.")
        if self.sma_short >= self.sma_long:
            raise ValueError("sma_short must be less than sma_long.")
        return self


class EquityPoint(BaseModel):
    date: str
    value: float


class TradeOut(BaseModel):
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    return_pct: float


class MetricsOut(BaseModel):
    total_return: float
    cagr: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    num_trades: int


class StrategyResult(BaseModel):
    equity_curve: list[EquityPoint]
    metrics: MetricsOut
    trades: list[TradeOut]


class BacktestResponse(BaseModel):
    ticker: str
    start_date: str
    end_date: str
    out_of_sample_start_date: str

    rule_based: StrategyResult                  # full requested date range
    ml: StrategyResult                          # out-of-sample period only
    buy_and_hold: StrategyResult                # full requested date range (pairs with rule_based)
    buy_and_hold_out_of_sample: StrategyResult  # same window as `ml`, for a fair head-to-head

    feature_importances: dict[str, float]
    train_size: int
    test_size: int


class HealthResponse(BaseModel):
    status: str
