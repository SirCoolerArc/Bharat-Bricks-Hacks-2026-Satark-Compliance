"use client";

import { useEffect, useState } from "react";
import { kpiData } from "@/lib/data";

export default function Topbar() {
  const [elapsed, setElapsed] = useState<number | null>(null);

  useEffect(() => {
    setElapsed(0);
    const interval = setInterval(() => {
      setElapsed((e) => (e ?? 0) + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="fixed top-0 left-14 right-0 h-[48px] bg-white/75 backdrop-blur-md border-b border-border/50 flex items-center justify-between px-6 z-40 shadow-sm transition-all duration-300">
      {/* Left: logo text + live indicator */}
      <div className="flex items-center gap-3">
        <h1 className="text-[15px] font-semibold tracking-tight text-text-primary">
          SATARK
        </h1>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-risk-low animate-pulse-live" />
          <span className="text-label uppercase text-text-muted font-medium">
            Live
          </span>
        </div>
        <span className="text-label text-text-muted" suppressHydrationWarning>
          {elapsed !== null ? `Last updated ${elapsed}s ago` : "Connecting..."}
        </span>
      </div>

      {/* Right: high-risk badge */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 bg-risk-high-bg/80 border border-risk-high/20 rounded-lg px-3 py-1.5 shadow-sm">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M7 1l6 11H1L7 1z" stroke="#DC2626" strokeWidth="1.2" fill="#DC2626" fillOpacity="0.15" />
            <line x1="7" y1="5" x2="7" y2="8" stroke="#DC2626" strokeWidth="1.2" strokeLinecap="round" />
            <circle cx="7" cy="10" r="0.7" fill="#DC2626" />
          </svg>
          <span className="text-label font-bold text-risk-high">
            {kpiData.highRisk24h.toLocaleString()} HIGH
          </span>
          <span className="text-label text-text-muted">unreviewed</span>
        </div>
      </div>
    </header>
  );
}
