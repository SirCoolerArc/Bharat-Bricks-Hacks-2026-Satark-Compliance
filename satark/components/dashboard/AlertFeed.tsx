"use client";

import { useState } from "react";
import { alertRows } from "@/lib/data";
import { RiskTier } from "@/lib/types";

const riskConfig: Record<RiskTier, { border: string; bg: string; text: string; badge: string }> = {
  HIGH: {
    border: "border-l-risk-high",
    bg: "bg-risk-high-bg",
    text: "text-risk-high",
    badge: "bg-risk-high text-white",
  },
  MEDIUM: {
    border: "border-l-risk-med",
    bg: "bg-risk-med-bg",
    text: "text-risk-med",
    badge: "bg-risk-med text-white",
  },
  LOW: {
    border: "border-l-risk-low",
    bg: "bg-risk-low-bg",
    text: "text-risk-low",
    badge: "bg-risk-low text-white",
  },
};

function SignalBadge({ label, active }: { label: string; active: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-1 text-label px-1.5 py-0.5 rounded ${
        active
          ? "bg-risk-high-bg text-risk-high border border-risk-high/20"
          : "bg-gray-100 text-text-muted border border-border"
      }`}
    >
      {label}: {active ? "Yes" : "No"}
    </span>
  );
}

export default function AlertFeed() {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <div className="bg-white/70 backdrop-blur-md border border-white/40 shadow-card hover:shadow-soft transition-all duration-300 rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-border/50 flex items-center justify-between bg-white/40">
        <div className="flex items-center gap-2">
          <h2 className="text-body font-semibold text-text-primary">
            Live Alert Feed
          </h2>
          <span className="w-1.5 h-1.5 rounded-full bg-risk-low animate-pulse-live" />
        </div>
        <span className="text-label text-text-muted">
          {alertRows.length} alerts
        </span>
      </div>

      {/* Table header */}
      <div className="grid grid-cols-[1fr_2fr_80px_100px] gap-2 px-5 py-2.5 border-b border-border/50 bg-white/30 backdrop-blur">
        <span className="text-label uppercase text-text-muted font-medium">VPA</span>
        <span className="text-label uppercase text-text-muted font-medium">UPI Remark</span>
        <span className="text-label uppercase text-text-muted font-medium">Risk</span>
        <span className="text-label uppercase text-text-muted font-medium text-right">Amount</span>
      </div>

      {/* Rows */}
      {alertRows.map((row) => {
        const config = riskConfig[row.risk];
        const isExpanded = expandedId === row.id;

        return (
          <div key={row.id}>
            <button
              onClick={() => setExpandedId(isExpanded ? null : row.id)}
              className={`w-full grid grid-cols-[1fr_2fr_80px_100px] gap-2 px-5 py-3 border-l-[4px] ${config.border} hover:bg-white/60 transition-colors text-left items-center border-b border-border/40`}
            >
              <span className="text-body text-text-primary font-mono text-xs truncate">
                {row.vpa}
              </span>
              <span className="text-body text-text-secondary truncate">
                {row.remark}
              </span>
              <span>
                <span className={`text-label font-semibold px-1.5 py-0.5 rounded ${config.badge}`}>
                  {row.risk}
                </span>
              </span>
              <span className="text-body text-text-primary text-right font-medium">
                ₹{row.amount.toLocaleString()}
              </span>
            </button>

            {/* Expanded detail */}
            {isExpanded && (
              <div className={`px-5 py-4 ${config.bg} border-b border-border/40 border-l-[4px] ${config.border} shadow-inner bg-opacity-50 backdrop-blur-sm`}>
                <div className="flex items-center gap-4 mb-3">
                  <span className="text-label text-text-muted">Fraud Type:</span>
                  <span className={`text-label font-semibold px-2 py-0.5 rounded ${config.bg} ${config.text} border ${config.text === "text-risk-high" ? "border-risk-high/20" : config.text === "text-risk-med" ? "border-risk-med/20" : "border-risk-low/20"}`}>
                    {row.fraudType}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-label text-text-muted">Signals:</span>
                  <SignalBadge label="VPN" active={row.signals.vpn} />
                  <SignalBadge label="New Device" active={row.signals.newDevice} />
                  <SignalBadge label="IP Mismatch" active={row.signals.ipMismatch} />
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
