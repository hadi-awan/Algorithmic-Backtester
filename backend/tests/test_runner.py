from app.backtest.runner import run_full_backtest
from tests.conftest import make_synthetic_ohlcv


def test_run_full_backtest_shapes():
    ohlcv = make_synthetic_ohlcv(n=300, seed=5)
    result = run_full_backtest(ohlcv, sma_short=10, sma_long=30, train_fraction=0.7)

    # Rule-based + full buy-and-hold span the full requested range.
    assert len(result.rule_based.equity_curve) == len(ohlcv)
    assert len(result.buy_and_hold_full.equity_curve) == len(ohlcv)

    # ML + its matching buy-and-hold span only the out-of-sample window,
    # and that window must be the same length for both.
    assert len(result.ml.equity_curve) == len(result.buy_and_hold.equity_curve)
    assert len(result.ml.equity_curve) == result.ml_meta.test_size
    assert len(result.ml.equity_curve) < len(ohlcv)


def test_run_full_backtest_all_metrics_present():
    ohlcv = make_synthetic_ohlcv(n=300, seed=5)
    result = run_full_backtest(ohlcv)
    for backtest_result in (result.rule_based, result.ml, result.buy_and_hold):
        assert isinstance(backtest_result.total_return, float)
        assert isinstance(backtest_result.sharpe_ratio, float)
        assert isinstance(backtest_result.max_drawdown, float)
        assert isinstance(backtest_result.win_rate, float)
        assert isinstance(backtest_result.num_trades, int)
