import { ReactNode } from "react";

type BannerVariant = "info" | "warning" | "danger" | "success";

interface InfoBannerProps {
  variant?: BannerVariant;
  title?: string;
  children: ReactNode;
  className?: string;
  compact?: boolean;
}

const STYLES: Record<BannerVariant, { bg: string; border: string; icon: string; titleColor: string }> = {
  info: {
    bg: "bg-blue-50",
    border: "border-l-[3px] border-l-[var(--accent)]",
    icon: "ℹ️",
    titleColor: "text-accent",
  },
  warning: {
    bg: "bg-amber-50",
    border: "border-l-[3px] border-l-[var(--risk-medium)]",
    icon: "⚠️",
    titleColor: "text-risk-medium",
  },
  danger: {
    bg: "bg-red-50",
    border: "border-l-[3px] border-l-[var(--risk-high)]",
    icon: "🚨",
    titleColor: "text-risk-high",
  },
  success: {
    bg: "bg-green-50",
    border: "border-l-[3px] border-l-[var(--risk-low)]",
    icon: "✅",
    titleColor: "text-risk-low",
  },
};

export default function InfoBanner({
  variant = "info",
  title,
  children,
  className = "",
  compact = false,
}: InfoBannerProps) {
  const s = STYLES[variant];
  return (
    <div
      className={`${s.bg} ${s.border} rounded-md ${compact ? "px-3 py-2" : "px-4 py-3"} ${className}`}
    >
      {title && (
        <p className={`text-sm font-semibold ${s.titleColor} mb-1 flex items-center gap-1.5`}>
          <span>{s.icon}</span> {title}
        </p>
      )}
      <div className="text-sm text-ink-muted leading-relaxed">{children}</div>
    </div>
  );
}
