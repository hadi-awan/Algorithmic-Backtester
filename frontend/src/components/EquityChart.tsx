import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { StrategyResult } from "../types";
import { palette } from "../theme/palette";
import { usePrefersDark } from "../hooks/usePrefersDark";

interface Props {
  ruleBased: StrategyResult;
  ml: StrategyResult;
  buyAndHold: StrategyResult;
  outOfSampleStartDate: string;
}

interface ChartRow {
  date: string;
  ruleBased: number | null;
  buyAndHold: number | null;
  ml: number | null;
}

function mergeSeries(
  ruleBased: StrategyResult,
  ml: StrategyResult,
  buyAndHold: StrategyResult,
): ChartRow[] {
  const rows = new Map<string, ChartRow>();

  const upsert = (date: string, key: keyof Omit<ChartRow, "date">, value: number) => {
    const existing = rows.get(date) ?? { date, ruleBased: null, buyAndHold: null, ml: null };
    existing[key] = value;
    rows.set(date, existing);
  };

  for (const p of ruleBased.equity_curve) upsert(p.date, "ruleBased", p.value);
  for (const p of buyAndHold.equity_curve) upsert(p.date, "buyAndHold", p.value);
  for (const p of ml.equity_curve) upsert(p.date, "ml", p.value);

  return Array.from(rows.values()).sort((a, b) => a.date.localeCompare(b.date));
}

export default function EquityChart({ ruleBased, ml, buyAndHold, outOfSampleStartDate }: Props) {
  const isDark = usePrefersDark();
  const colors = isDark ? palette.dark : palette.light;
  const data = mergeSeries(ruleBased, ml, buyAndHold);

  return (
    <div className="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-900">
      <h3 className="mb-1 text-sm font-semibold text-neutral-900 dark:text-neutral-100">
        Equity Curve (growth of $1)
      </h3>
      <p className="mb-3 text-xs text-neutral-500 dark:text-neutral-400">
        ML strategy only appears from its out-of-sample test period onward ({outOfSampleStartDate})
        -- it is never trained or backtested on data it could have seen in advance.
      </p>
      <ResponsiveContainer width="100%" height={360}>
        <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
          <CartesianGrid stroke={colors.gridline} vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fill: colors.muted, fontSize: 12 }}
            stroke={colors.baseline}
            minTickGap={40}
          />
          <YAxis
            tick={{ fill: colors.muted, fontSize: 12 }}
            stroke={colors.baseline}
            width={48}
            domain={["auto", "auto"]}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: colors.surface,
              border: `1px solid ${colors.gridline}`,
              fontSize: 12,
              color: colors.textPrimary,
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12, color: colors.textSecondary }} />
          <ReferenceLine
            x={outOfSampleStartDate}
            stroke={colors.muted}
            strokeDasharray="4 4"
            label={{
              value: "Out-of-sample start",
              position: "insideTopRight",
              fill: colors.muted,
              fontSize: 11,
            }}
          />
          <Line
            type="monotone"
            dataKey="ruleBased"
            name="Rule-Based (SMA)"
            stroke={colors.series.ruleBased}
            strokeWidth={2}
            dot={false}
            connectNulls={false}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="buyAndHold"
            name="Buy & Hold"
            stroke={colors.series.buyAndHold}
            strokeWidth={2}
            dot={false}
            connectNulls={false}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="ml"
            name="ML Strategy"
            stroke={colors.series.ml}
            strokeWidth={2}
            dot={false}
            connectNulls={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
