export default function LiveDot() {
  return (
    <span className="relative flex h-2.5 w-2.5">
      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-risk-low opacity-75" />
      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-risk-low" />
    </span>
  );
}
