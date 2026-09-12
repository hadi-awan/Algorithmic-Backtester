import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts";
import { palette } from "../theme/palette";
import { usePrefersDark } from "../hooks/usePrefersDark";

interface Props {
  importances: Record<string, number>;
}

const FEATURE_LABELS: Record<string, string> = {
  return_1d: "1-Day Return",
  return_5d: "5-Day Return",
  rsi_14: "RSI (14)",
  macd: "MACD",
  macd_signal: "MACD Signal",
  bollinger_position: "Bollinger Position",
  volatility_10d: "10-Day Volatility",
  volume_change: "Volume Change",
};

export default function FeatureImportanceChart({ importances }: Props) {
  const isDark = usePrefersDark();
  const colors = isDark ? palette.dark : palette.light;

  const data = Object.entries(importances)
    .map(([feature, value]) => ({
      feature: FEATURE_LABELS[feature] ?? feature,
      value,
    }))
    .sort((a, b) => b.value - a.value);

  return (
    <div className="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-900">
      <h3 className="mb-1 text-sm font-semibold text-neutral-900 dark:text-neutral-100">
        ML Feature Importances
      </h3>
      <p className="mb-3 text-xs text-neutral-500 dark:text-neutral-400">
        Relative importance each technical indicator had in the RandomForest's next-day up/down
        prediction.
      </p>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 48, left: 8, bottom: 4 }}>
          <CartesianGrid stroke={colors.gridline} horizontal={false} />
          <XAxis
            type="number"
            tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
            tick={{ fill: colors.muted, fontSize: 12 }}
            stroke={colors.baseline}
          />
          <YAxis
            type="category"
            dataKey="feature"
            width={130}
            tick={{ fill: colors.textSecondary, fontSize: 12 }}
            stroke={colors.baseline}
          />
          <Bar
            dataKey="value"
            fill={colors.sequential}
            radius={[0, 4, 4, 0]}
            isAnimationActive={false}
          >
            <LabelList
              dataKey="value"
              position="right"
              formatter={(v: number) => `${(v * 100).toFixed(1)}%`}
              fill={colors.textSecondary}
              fontSize={11}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
