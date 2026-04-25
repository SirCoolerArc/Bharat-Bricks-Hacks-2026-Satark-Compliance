"use client";

// ─────────────────────────────────────────────
// Reusable SVG bar chart — no external dependencies
// Renders horizontal or vertical bars with labels
// ─────────────────────────────────────────────

export interface BarChartItem {
  label: string;
  value: number;
  color?: string;
}

interface BarChartProps {
  data: BarChartItem[];
  height?: number;
  showValues?: boolean;
  maxValue?: number;
}

const DEFAULT_COLORS = [
  "var(--accent)",
  "var(--risk-medium)",
  "var(--risk-high)",
  "var(--risk-low)",
  "var(--risk-critical)",
  "var(--ink-faint)",
  "#8E24AA",
  "#00897B",
];

export default function BarChart({
  data,
  height = 200,
  showValues = true,
  maxValue,
}: BarChartProps) {
  if (data.length === 0) return null;

  const max = maxValue || Math.max(...data.map((d) => d.value), 1);
  const barWidth = Math.max(20, Math.min(48, Math.floor(500 / data.length) - 12));
  const chartWidth = data.length * (barWidth + 12) + 40;

  return (
    <div className="w-full overflow-x-auto">
      <svg
        width="100%"
        height={height + 50}
        viewBox={`0 0 ${chartWidth} ${height + 50}`}
        preserveAspectRatio="xMidYEnd meet"
        className="block"
      >
        {/* Bars */}
        {data.map((item, i) => {
          const barHeight = (item.value / max) * (height - 20);
          const x = 20 + i * (barWidth + 12);
          const y = height - barHeight;
          const color = item.color || DEFAULT_COLORS[i % DEFAULT_COLORS.length];

          return (
            <g key={item.label}>
              {/* Bar */}
              <rect
                x={x}
                y={y}
                width={barWidth}
                height={barHeight}
                rx={3}
                fill={color}
                opacity={0.85}
                className="transition-all duration-500 ease-out"
              />
              {/* Value label */}
              {showValues && (
                <text
                  x={x + barWidth / 2}
                  y={y - 6}
                  textAnchor="middle"
                  fill="var(--ink-muted)"
                  style={{ fontSize: 11 }}
                >
                  {item.value >= 1000
                    ? `${(item.value / 1000).toFixed(1)}k`
                    : item.value.toString()}
                </text>
              )}
              {/* X label */}
              <text
                x={x + barWidth / 2}
                y={height + 16}
                textAnchor="middle"
                fill="var(--ink-faint)"
                style={{ fontSize: 10 }}
              >
                {item.label.length > 8 ? item.label.slice(0, 7) + "…" : item.label}
              </text>
            </g>
          );
        })}

        {/* Base line */}
        <line
          x1={16}
          y1={height}
          x2={chartWidth - 4}
          y2={height}
          stroke="var(--surface-300)"
          strokeWidth={0.5}
        />
      </svg>
    </div>
  );
}
