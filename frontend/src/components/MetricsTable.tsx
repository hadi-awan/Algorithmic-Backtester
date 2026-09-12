import type { Metrics } from "../types";

interface Props {
  ruleBased: Metrics;
  ml: Metrics;
  buyAndHold: Metrics;
  buyAndHoldOutOfSample: Metrics;
  outOfSampleStartDate: string;
  endDate: string;
}

const ROWS: { key: keyof Metrics; label: string; format: (v: number) => string }[] = [
  { key: "total_return", label: "Total Return", format: (v) => `${(v * 100).toFixed(1)}%` },
  { key: "cagr", label: "CAGR", format: (v) => `${(v * 100).toFixed(1)}%` },
  { key: "sharpe_ratio", label: "Sharpe Ratio", format: (v) => v.toFixed(2) },
  { key: "max_drawdown", label: "Max Drawdown", format: (v) => `${(v * 100).toFixed(1)}%` },
  { key: "win_rate", label: "Win Rate", format: (v) => `${(v * 100).toFixed(0)}%` },
  { key: "num_trades", label: "# Trades", format: (v) => String(v) },
];

export default function MetricsTable({
  ruleBased,
  ml,
  buyAndHold,
  buyAndHoldOutOfSample,
  outOfSampleStartDate,
  endDate,
}: Props) {
  return (
    <div className="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-900">
      <h3 className="mb-3 text-sm font-semibold text-neutral-900 dark:text-neutral-100">
        Performance Metrics
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-neutral-200 text-neutral-500 dark:border-neutral-800 dark:text-neutral-400">
              <th className="py-2 pr-4 font-medium">Metric</th>
              <th className="py-2 pr-4 font-medium">Rule-Based</th>
              <th className="py-2 pr-4 font-medium">ML (out-of-sample)</th>
              <th className="py-2 pr-4 font-medium">Buy &amp; Hold</th>
            </tr>
          </thead>
          <tbody className="tabular-nums">
            {ROWS.map(({ key, label, format }) => (
              <tr
                key={key}
                className="border-b border-neutral-100 last:border-0 dark:border-neutral-800"
              >
                <td className="py-2 pr-4 text-neutral-600 dark:text-neutral-400">{label}</td>
                <td className="py-2 pr-4 text-neutral-900 dark:text-neutral-100">
                  {format(ruleBased[key])}
                </td>
                <td className="py-2 pr-4 text-neutral-900 dark:text-neutral-100">
                  {format(ml[key])}
                </td>
                <td className="py-2 pr-4 text-neutral-900 dark:text-neutral-100">
                  {format(buyAndHold[key])}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-xs text-neutral-500 dark:text-neutral-400">
        The "Buy &amp; Hold" column above spans the full requested range, same as Rule-Based. For a
        strictly apples-to-apples read against the ML strategy, buy-and-hold over that same
        out-of-sample window ({outOfSampleStartDate} to {endDate}) returned{" "}
        <span className="font-medium text-neutral-700 dark:text-neutral-300">
          {(buyAndHoldOutOfSample.total_return * 100).toFixed(1)}%
        </span>{" "}
        total return with a Sharpe ratio of{" "}
        <span className="font-medium text-neutral-700 dark:text-neutral-300">
          {buyAndHoldOutOfSample.sharpe_ratio.toFixed(2)}
        </span>
        .
      </p>
    </div>
  );
}
