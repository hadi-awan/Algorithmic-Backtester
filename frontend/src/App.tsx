import { useState } from "react";
import BacktestForm from "./components/BacktestForm";
import EquityChart from "./components/EquityChart";
import ErrorBanner from "./components/ErrorBanner";
import FeatureImportanceChart from "./components/FeatureImportanceChart";
import LoadingSpinner from "./components/LoadingSpinner";
import MetricsTable from "./components/MetricsTable";
import TradeLogTable from "./components/TradeLogTable";
import { ApiError, runBacktest } from "./api/client";
import type { BacktestRequest, BacktestResponse } from "./types";

export default function App() {
  const [result, setResult] = useState<BacktestResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(params: BacktestRequest) {
    setIsLoading(true);
    setError(null);
    try {
      const response = await runBacktest(params);
      setResult(response);
    } catch (err) {
      setResult(null);
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="mx-auto min-h-screen max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
          Quant Signal Backtester
        </h1>
        <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400">
          Rule-based SMA crossover vs. an ML-driven strategy vs. buy &amp; hold, on real historical
          price data.
        </p>
      </header>

      <div className="mb-6">
        <BacktestForm onSubmit={handleSubmit} isLoading={isLoading} />
      </div>

      {error && (
        <div className="mb-6">
          <ErrorBanner message={error} />
        </div>
      )}

      {isLoading && <LoadingSpinner />}

      {!isLoading && result && (
        <div className="flex flex-col gap-6">
          <EquityChart
            ruleBased={result.rule_based}
            ml={result.ml}
            buyAndHold={result.buy_and_hold}
            outOfSampleStartDate={result.out_of_sample_start_date}
          />

          <MetricsTable
            ruleBased={result.rule_based.metrics}
            ml={result.ml.metrics}
            buyAndHold={result.buy_and_hold.metrics}
            buyAndHoldOutOfSample={result.buy_and_hold_out_of_sample.metrics}
            outOfSampleStartDate={result.out_of_sample_start_date}
            endDate={result.end_date}
          />

          <FeatureImportanceChart importances={result.feature_importances} />

          <TradeLogTable
            ruleBased={result.rule_based.trades}
            ml={result.ml.trades}
            buyAndHold={result.buy_and_hold.trades}
          />
        </div>
      )}

      {!isLoading && !result && !error && (
        <div className="rounded-lg border border-dashed border-neutral-300 py-16 text-center text-sm text-neutral-500 dark:border-neutral-700 dark:text-neutral-400">
          Enter a ticker and date range above, then run a backtest to see results.
        </div>
      )}

      <footer className="mt-10 border-t border-neutral-200 pt-4 text-xs text-neutral-500 dark:border-neutral-800 dark:text-neutral-400">
        Educational/portfolio project only -- not investment advice. Backtests do not account for
        transaction costs, slippage, or taxes, and past performance on historical data is not
        indicative of future results.
      </footer>
    </div>
  );
}
