import { RiskLevel } from "@/types";

const COLORS: Record<RiskLevel, { bg: string; text: string; label: string }> = {
  low:      { bg: "bg-green-50",  text: "text-risk-low",      label: "Low Risk" },
  medium:   { bg: "bg-amber-50",  text: "text-risk-medium",   label: "Medium Risk" },
  high:     { bg: "bg-red-50",    text: "text-risk-high",     label: "High Risk" },
  critical: { bg: "bg-red-100",   text: "text-risk-critical", label: "Critical" },
};

interface RiskBadgeProps {
  level: RiskLevel;
  className?: string;
}

export default function RiskBadge({ level, className = "" }: RiskBadgeProps) {
  const { bg, text, label } = COLORS[level];
  return (
    <span
      className={`
        inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
        ${bg} ${text} ${className}
      `}
    >
      {label}
    </span>
  );
}
