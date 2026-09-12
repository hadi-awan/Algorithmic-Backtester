import type { Trade } from "../types";

interface Section {
  label: string;
  trades: Trade[];
}

interface Props {
  ruleBased: Trade[];
  ml: Trade[];
  buyAndHold: Trade[];
}

function TradeTable({ trades }: { trades: Trade[] }) {
  if (trades.length === 0) {
    return (
      <p className="py-3 text-sm text-neutral-500 dark:text-neutral-400">
        No trades were taken over this period.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-neutral-200 text-neutral-500 dark:border-neutral-800 dark:text-neutral-400">
            <th className="py-2 pr-4 font-medium">Entry Date</th>
            <th className="py-2 pr-4 font-medium">Exit Date</th>
            <th className="py-2 pr-4 font-medium">Entry Price</th>
            <th className="py-2 pr-4 font-medium">Exit Price</th>
            <th className="py-2 pr-4 font-medium">Return</th>
          </tr>
        </thead>
        <tbody className="tabular-nums">
          {trades.map((t, i) => (
            <tr
              key={`${t.entry_date}-${i}`}
              className="border-b border-neutral-100 last:border-0 dark:border-neutral-800"
            >
              <td className="py-2 pr-4">{t.entry_date}</td>
              <td className="py-2 pr-4">{t.exit_date}</td>
              <td className="py-2 pr-4">${t.entry_price.toFixed(2)}</td>
              <td className="py-2 pr-4">${t.exit_price.toFixed(2)}</td>
              <td
                className={
                  t.return_pct >= 0
                    ? "py-2 pr-4 text-emerald-600 dark:text-emerald-400"
                    : "py-2 pr-4 text-red-600 dark:text-red-400"
                }
              >
                {(t.return_pct * 100).toFixed(1)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function TradeLogTable({ ruleBased, ml, buyAndHold }: Props) {
  const sections: Section[] = [
    { label: "Rule-Based Trades", trades: ruleBased },
    { label: "ML Strategy Trades", trades: ml },
    { label: "Buy & Hold", trades: buyAndHold },
  ];

  return (
    <div className="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-900">
      <h3 className="mb-3 text-sm font-semibold text-neutral-900 dark:text-neutral-100">
        Trade Logs
      </h3>
      <div className="divide-y divide-neutral-100 dark:divide-neutral-800">
        {sections.map((section) => (
          <details key={section.label} className="group py-2">
            <summary className="cursor-pointer list-none py-1 text-sm font-medium text-neutral-700 marker:content-none dark:text-neutral-300">
              <span className="inline-block w-4 text-neutral-400 transition-transform group-open:rotate-90">
                ▸
              </span>{" "}
              {section.label} ({section.trades.length})
            </summary>
            <TradeTable trades={section.trades} />
          </details>
        ))}
      </div>
    </div>
  );
}
