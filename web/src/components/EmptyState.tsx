interface EmptyStateProps {
  icon?: string;
  title: string;
  description?: string;
  className?: string;
}

export default function EmptyState({
  icon = "📭",
  title,
  description,
  className = "",
}: EmptyStateProps) {
  return (
    <div className={`card-surface flex flex-col items-center justify-center py-12 px-6 text-center ${className}`}>
      <span className="text-3xl mb-3">{icon}</span>
      <p className="text-sm font-medium text-ink-muted">{title}</p>
      {description && (
        <p className="text-xs text-ink-faint mt-1 max-w-xs">{description}</p>
      )}
    </div>
  );
}
