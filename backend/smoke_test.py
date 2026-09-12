from app.data.ingestion import fetch_ohlcv
from app.backtest.runner import run_full_backtest

ohlcv = fetch_ohlcv("AAPL", "2022-01-01", "2026-09-01")
result = run_full_backtest(ohlcv, sma_short=20, sma_long=50, train_fraction=0.7)

for name, r in [("Rule-based", result.rule_based), ("ML (OOS)", result.ml), ("Buy & hold (OOS)", result.buy_and_hold)]:
    print(f"\n{name}: total_return={r.total_return:.2%} cagr={r.cagr:.2%} sharpe={r.sharpe_ratio:.2f} max_dd={r.max_drawdown:.2%} trades={r.num_trades}")

print("\nFeature importances:", result.ml_meta.feature_importances)