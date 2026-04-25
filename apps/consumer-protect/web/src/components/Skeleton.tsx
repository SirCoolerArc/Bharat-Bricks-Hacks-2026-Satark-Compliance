// ─────────────────────────────────────────────
// Skeleton loader component for loading states
// ─────────────────────────────────────────────

interface SkeletonProps {
  className?: string;
  lines?: number;
}

export default function Skeleton({ className = "", lines = 1 }: SkeletonProps) {
  return (
    <div className={`animate-pulse space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-4 bg-surface-200 rounded"
          style={{ width: i === lines - 1 && lines > 1 ? "60%" : "100%" }}
        />
      ))}
    </div>
  );
}

export function SkeletonCard({ className = "" }: { className?: string }) {
  return (
    <div className={`card-surface p-5 animate-pulse ${className}`}>
      <div className="h-3 bg-surface-200 rounded w-24 mb-3" />
      <div className="h-6 bg-surface-200 rounded w-16" />
    </div>
  );
}

export function SkeletonChart({ height = 200 }: { height?: number }) {
  return (
    <div
      className="card-surface p-5 animate-pulse flex items-end gap-3 justify-center"
      style={{ height }}
    >
      {[40, 70, 55, 85, 45, 60, 75].map((h, i) => (
        <div
          key={i}
          className="bg-surface-200 rounded-t"
          style={{ width: 28, height: `${h}%` }}
        />
      ))}
    </div>
  );
}
