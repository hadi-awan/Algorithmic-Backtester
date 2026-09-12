// Mirrors backend/app/api/schemas.py -- keep in sync with that file.

export interface BacktestRequest {
  ticker: string;
  start_date: string; // YYYY-MM-DD
  end_date: string; // YYYY-MM-DD
  sma_short: number;
  sma_long: number;
  train_fraction: number;
  probability_threshold: number;
}

export interface EquityPoint {
  date: string;
  value: number;
}

export interface Trade {
  entry_date: string;
  exit_date: string;
  entry_price: number;
  exit_price: number;
  return_pct: number;
}

export interface Metrics {
  total_return: number;
  cagr: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  num_trades: number;
}

export interface StrategyResult {
  equity_curve: EquityPoint[];
  metrics: Metrics;
  trades: Trade[];
}

export interface BacktestResponse {
  ticker: string;
  start_date: string;
  end_date: string;
  out_of_sample_start_date: string;
  rule_based: StrategyResult;
  ml: StrategyResult;
  buy_and_hold: StrategyResult;
  buy_and_hold_out_of_sample: StrategyResult;
  feature_importances: Record<string, number>;
  train_size: number;
  test_size: number;
}
