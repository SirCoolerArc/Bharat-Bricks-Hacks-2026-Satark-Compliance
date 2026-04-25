"use client";

interface RiskGaugeProps {
  score: number; // 0–100
  size?: number; // diameter in px
}

export default function RiskGauge({ score, size = 180 }: RiskGaugeProps) {
  const clamped = Math.max(0, Math.min(100, score));

  // Semi-circle SVG gauge
  const cx = size / 2;
  const cy = size / 2;
  const r = (size - 20) / 2;
  const circumference = Math.PI * r; // half-circle
  const offset = circumference - (clamped / 100) * circumference;

  // Color based on score
  const color =
    clamped <= 30
      ? "var(--risk-low)"
      : clamped <= 60
        ? "var(--risk-medium)"
        : clamped <= 85
          ? "var(--risk-high)"
          : "var(--risk-critical)";

  const label =
    clamped <= 30 ? "Low" : clamped <= 60 ? "Medium" : clamped <= 85 ? "High" : "Critical";

  return (
    <div className="flex flex-col items-center">
      <svg
        width={size}
        height={size / 2 + 20}
        viewBox={`0 0 ${size} ${size / 2 + 20}`}
        className="overflow-visible"
      >
        {/* Background arc */}
        <path
          d={`M 10 ${cy} A ${r} ${r} 0 0 1 ${size - 10} ${cy}`}
          fill="none"
          stroke="var(--surface-200)"
          strokeWidth="10"
          strokeLinecap="round"
        />
        {/* Score arc */}
        <path
          d={`M 10 ${cy} A ${r} ${r} 0 0 1 ${size - 10} ${cy}`}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-700 ease-out"
        />
        {/* Score text */}
        <text
          x={cx}
          y={cy - 10}
          textAnchor="middle"
          className="text-3xl font-bold"
          fill="var(--ink)"
          style={{ fontSize: size * 0.18 }}
        >
          {clamped}
        </text>
        <text
          x={cx}
          y={cy + 10}
          textAnchor="middle"
          fill="var(--ink-muted)"
          style={{ fontSize: size * 0.08 }}
        >
          {label} Risk
        </text>
      </svg>
    </div>
  );
}
