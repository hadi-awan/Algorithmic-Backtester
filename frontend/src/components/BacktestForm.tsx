import { useState, FormEvent } from "react";
import type { BacktestRequest } from "../types";

interface Props {
  onSubmit: (params: BacktestRequest) => void;
  isLoading: boolean;
}

function defaultDateRange(): { start: string; end: string } {
  const end = new Date();
  const start = new Date();
  start.setFullYear(start.getFullYear() - 3); // spec default: last 3 years
  const fmt = (d: Date) => d.toISOString().slice(0, 10);
  return { start: fmt(start), end: fmt(end) };
}

export default function BacktestForm({ onSubmit, isLoading }: Props) {
  const { start, end } = defaultDateRange();
  const [ticker, setTicker] = useState("AAPL");
  const [startDate, setStartDate] = useState(start);
  const [endDate, setEndDate] = useState(end);
  const [smaShort, setSmaShort] = useState(20);
  const [smaLong, setSmaLong] = useState(50);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSubmit({
      ticker: ticker.trim().toUpperCase(),
      start_date: startDate,
      end_date: endDate,
      sma_short: smaShort,
      sma_long: smaLong,
      train_fraction: 0.7,
      probability_threshold: 0.5,
    });
  }

  const inputClasses =
    "w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm " +
    "text-neutral-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 " +
    "focus:ring-blue-500 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100";
  const labelClasses = "mb-1 block text-sm font-medium text-neutral-700 dark:text-neutral-300";

  return (
    <form
      onSubmit={handleSubmit}
      className="grid grid-cols-2 gap-4 rounded-lg border border-neutral-200 bg-white p-5 shadow-sm dark:border-neutral-800 dark:bg-neutral-900 sm:grid-cols-3 lg:grid-cols-6"
    >
      <div className="col-span-2 sm:col-span-1">
        <label className={labelClasses} htmlFor="ticker">
          Ticker
        </label>
        <input
          id="ticker"
          type="text"
          required
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          placeholder="AAPL"
          className={inputClasses}
        />
      </div>

      <div>
        <label className={labelClasses} htmlFor="start_date">
          Start date
        </label>
        <input
          id="start_date"
          type="date"
          required
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          className={inputClasses}
        />
      </div>

      <div>
        <label className={labelClasses} htmlFor="end_date">
          End date
        </label>
        <input
          id="end_date"
          type="date"
          required
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          className={inputClasses}
        />
      </div>

      <div>
        <label className={labelClasses} htmlFor="sma_short">
          SMA short
        </label>
        <input
          id="sma_short"
          type="number"
          min={1}
          required
          value={smaShort}
          onChange={(e) => setSmaShort(Number(e.target.value))}
          className={inputClasses}
        />
      </div>

      <div>
        <label className={labelClasses} htmlFor="sma_long">
          SMA long
        </label>
        <input
          id="sma_long"
          type="number"
          min={2}
          required
          value={smaLong}
          onChange={(e) => setSmaLong(Number(e.target.value))}
          className={inputClasses}
        />
      </div>

      <div className="flex items-end">
        <button
          type="submit"
          disabled={isLoading}
          className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isLoading ? "Running..." : "Run Backtest"}
        </button>
      </div>
    </form>
  );
}
