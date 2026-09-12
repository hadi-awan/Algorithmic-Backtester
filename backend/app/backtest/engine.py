"""The single shared backtest engine. Every strategy (rule-based, ML,
buy-and-hold) is run through this same function so results are directly
comparable and correctness only needs to be verified in one place.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import metrics as m


@dataclass
class Trade:
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    return_pct: float


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    strategy_returns: pd.Series
    trades: list[Trade]
    total_return: float
    cagr: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    num_trades: int


def _as_date_str(idx) -> str:
    return str(idx.date()) if hasattr(idx, "date") else str(idx)


def _extract_trades(close: pd.Series, signal: pd.Series) -> list[Trade]:
    """Reconstruct discrete long trades from a 0/1 signal series."""
    trades: list[Trade] = []
    in_position = False
    entry_idx = None

    for idx, pos in signal.items():
        if pos == 1 and not in_position:
            in_position = True
            entry_idx = idx
        elif pos == 0 and in_position:
            in_position = False
            entry_price = float(close.loc[entry_idx])
            exit_price = float(close.loc[idx])
            trades.append(
                Trade(
                    entry_date=_as_date_str(entry_idx),
                    exit_date=_as_date_str(idx),
                    entry_price=entry_price,
                    exit_price=exit_price,
                    return_pct=exit_price / entry_price - 1,
                )
            )
            entry_idx = None

    if in_position and entry_idx is not None:
        # Still in a position at the end of the window: close it out at
        # the last available price so metrics reflect the open trade.
        entry_price = float(close.loc[entry_idx])
        exit_price = float(close.iloc[-1])
        trades.append(
            Trade(
                entry_date=_as_date_str(entry_idx),
                exit_date=_as_date_str(close.index[-1]),
                entry_price=entry_price,
                exit_price=exit_price,
                return_pct=exit_price / entry_price - 1,
            )
        )

    return trades


def run_backtest(close: pd.Series, signal: pd.Series) -> BacktestResult:
    """Run a backtest given a price series and a 0/1 (flat/long) signal
    series aligned to the same index.

    No transaction costs or slippage are modeled (v1 simplifying
    assumption, documented in the README).

    Lookahead safety: a signal value for day T is only known at T's
    close, so it is shifted forward one day before being applied to
    returns (you can't act on today's signal until tomorrow's bar).
    """
    if not close.index.equals(signal.index):
        raise ValueError("close and signal must share the same index.")

    daily_returns = close.pct_change().fillna(0)
    position = signal.shift(1).fillna(0)  # act on yesterday's signal
    strategy_returns = position * daily_returns
    equity_curve = (1 + strategy_returns).cumprod()
    equity_curve.name = "equity"

    trades = _extract_trades(close, signal)
    trade_returns = pd.Series([t.return_pct for t in trades], dtype=float)

    return BacktestResult(
        equity_curve=equity_curve,
        strategy_returns=strategy_returns,
        trades=trades,
        total_return=m.total_return(equity_curve),
        cagr=m.cagr(equity_curve),
        sharpe_ratio=m.sharpe_ratio(strategy_returns),
        max_drawdown=m.max_drawdown(equity_curve),
        win_rate=m.win_rate(trade_returns),
        num_trades=m.num_trades(signal),
    )


def run_buy_and_hold(close: pd.Series) -> BacktestResult:
    """Buy-and-hold benchmark, run through the identical engine used for
    the strategies (signal is always 1/long)."""
    always_long = pd.Series(1, index=close.index, name="signal")
    return run_backtest(close, always_long)
