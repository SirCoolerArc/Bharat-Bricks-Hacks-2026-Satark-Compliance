"use client";

import { useState, useEffect, useCallback } from "react";
import Card from "@/components/Card";
import RiskBadge from "@/components/RiskBadge";
import LiveDot from "@/components/LiveDot";
import Button from "@/components/Button";
import BarChart from "@/components/BarChart";
import DonutChart from "@/components/DonutChart";
import EmptyState from "@/components/EmptyState";
import { SkeletonCard, SkeletonChart } from "@/components/Skeleton";
import { KpiSummary, AlertItem } from "@/types";
import { BarChartItem } from "@/components/BarChart";
import { DonutSegment } from "@/components/DonutChart";

interface DashboardData {
  kpi: KpiSummary;
  alerts: AlertItem[];
  scamBreakdown: BarChartItem[];
  complaintStatus: DonutSegment[];
  monthlyTrend: BarChartItem[];
}

// Helper to format "time ago"
function timeAgo(dateInput: string | Date): string {
  const date = new Date(dateInput);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) return "Just now";
  
  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
  
  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) return `${diffInHours}h ago`;
  
  return date.toLocaleDateString("en-IN", { month: "short", day: "numeric" });
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/dashboard");
      if (!res.ok) throw new Error("Failed to fetch");
      const d: DashboardData = await res.json();
      setData(d);
      setLastRefresh(new Date());
    } catch {
      setError("Could not load dashboard data. Showing may be stale.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const kpi = data?.kpi;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ink hover:text-ink/80 transition-colors">Compliance Dashboard</h1>
          <div className="flex items-center gap-2 mt-1">
            <p className="text-sm text-ink-muted">
              Fraud trends and risk analytics
            </p>
            {lastRefresh && (
              <>
                <span className="w-1 h-1 rounded-full bg-surface-300" />
                <span className="text-[11px] font-medium text-ink-faint uppercase tracking-wider bg-surface-50 px-1.5 rounded">
                  Updated {lastRefresh.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
                </span>
              </>
            )}
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-risk-low tracking-wide uppercase bg-green-50 px-2 py-1 rounded-full">
            <LiveDot /> Live
          </div>
          <Button variant="secondary" size="sm" onClick={fetchData} loading={loading}>
            Refresh
          </Button>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="p-3 rounded-md border-l-[3px] border-l-[var(--risk-high)] bg-red-50 text-sm text-ink flex items-center justify-between">
          <span><span className="text-risk-high mr-1.5">⚠️</span>{error}</span>
          <Button variant="ghost" size="sm" onClick={fetchData} className="px-2 py-1 h-auto text-xs">Try again</Button>
        </div>
      )}

      {/* KPI Grid */}
      {loading && !data ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={`kpi-row1-${i}`} />)}
        </div>
      ) : kpi ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <KpiCard label="Total Transactions" value={kpi.totalTransactions.toLocaleString("en-IN")} />
          <KpiCard 
            label="Fraud Detected" 
            value={kpi.fraudCount.toLocaleString("en-IN")} 
            sublabel={<><span className="text-risk-high mr-0.5">↑</span>{(kpi.fraudRate * 100).toFixed(1)}% rate</>} 
            highlight 
          />
          <KpiCard label="Avg Fraud Amount" value={`₹${kpi.avgFraudAmount.toLocaleString("en-IN")}`} />
          <KpiCard label="Avg Resolution" value={`${kpi.avgResolutionDays} days`} />
        </div>
      ) : null}

      {/* Secondary KPI Row */}
      {loading && !data ? (
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
          {Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={`kpi-row2-${i}`} />)}
        </div>
      ) : kpi ? (
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
          <KpiCard label="Top Scam Type" value={kpi.topScamType} />
          <KpiCard label="Complaints Open" value={kpi.complaintsOpen.toLocaleString("en-IN")} highlight={kpi.complaintsOpen > 1000} />
          <KpiCard label="Complaints Resolved" value={kpi.complaintsResolved.toLocaleString("en-IN")} />
        </div>
      ) : null}

      {/* Charts row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Scam Type Breakdown */}
        <Card className="flex flex-col">
          <h2 className="section-heading mb-4">Fraud by Scam Type</h2>
          <div className="flex-1 flex flex-col justify-end min-h-[220px]">
            {loading && !data ? (
              <SkeletonChart />
            ) : data?.scamBreakdown && data.scamBreakdown.length > 0 ? (
              <BarChart data={data.scamBreakdown} height={200} />
            ) : (
              <EmptyState 
                icon="📊" 
                title="No patterns detected" 
                description="Not enough fraud data to determine common scam types yet."
              />
            )}
          </div>
        </Card>

        {/* Complaint Status */}
        <Card className="flex flex-col">
          <h2 className="section-heading mb-4">Complaint Status</h2>
          <div className="flex-1 flex items-center justify-center min-h-[220px]">
            {loading && !data ? (
              <SkeletonChart />
            ) : data?.complaintStatus && data.complaintStatus.length > 0 && kpi ? (
              <DonutChart
                segments={data.complaintStatus}
                size={180}
                centerValue={(kpi.complaintsOpen + kpi.complaintsResolved).toLocaleString("en-IN")}
                centerLabel="Total"
              />
            ) : (
              <EmptyState 
                icon="📁" 
                title="No active complaints" 
                description="All clear. No user complaints are currently in the system."
              />
            )}
          </div>
        </Card>
      </div>

      {/* Monthly Trend */}
      <Card>
        <h2 className="section-heading mb-4">Monthly Fraud Trend</h2>
        <div className="min-h-[180px]">
          {loading && !data ? (
            <SkeletonChart />
          ) : data?.monthlyTrend && data.monthlyTrend.length > 0 ? (
            <BarChart data={data.monthlyTrend} height={180} />
          ) : (
            <EmptyState 
              icon="📉" 
              title="Insufficient history" 
              description="Not enough historical data to generate a monthly trend."
            />
          )}
        </div>
      </Card>

      {/* Recent Alerts */}
      <div className="pt-2">
        <h2 className="text-lg font-semibold text-ink mb-3 flex items-center gap-2">
          <span>Live Alert Feed</span>
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-accent"></span>
          </span>
        </h2>
        
        {data?.alerts && data.alerts.length > 0 ? (
          <div className="space-y-2.5">
            {data.alerts.map((alert) => {
              const borderColors: Record<string, string> = {
                critical: "border-l-[4px] border-l-[var(--risk-critical)]",
                high: "border-l-[4px] border-l-[var(--risk-high)]",
                medium: "border-l-[4px] border-l-[var(--risk-medium)]",
                low: "border-l-[4px] border-l-[var(--risk-low)]"
              };
              
              return (
                <div key={alert.id} className={`bg-white rounded-md shadow-sm transition-shadow hover:shadow-md ${borderColors[alert.severity]}`} style={{ border: "0.5px solid var(--border-color)", borderLeft: undefined }}>
                  <div className="p-3 sm:px-4 sm:py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <RiskBadge level={alert.severity} className="lowercase tracking-wide font-bold shadow-sm" />
                        <span className="text-[11px] font-semibold text-ink-muted uppercase tracking-wider">{alert.type}</span>
                        <span className="text-xs text-ink-faint hidden sm:inline-block">·</span>
                        <span className="text-xs font-mono text-ink-faint hidden sm:inline-block">#{alert.id.substring(0, 8)}</span>
                      </div>
                      <p className="text-sm font-medium text-ink truncate mt-1.5">{alert.message}</p>
                      <div className="flex items-center gap-3 mt-2">
                        <p className="text-xs text-ink-muted flex items-center gap-1 bg-surface-50 px-1.5 py-0.5 rounded">
                          <span className="opacity-70">VPA:</span> <span className="font-medium text-ink">{alert.vpaMasked}</span>
                        </p>
                        <p className="text-xs text-ink-muted flex items-center gap-1 bg-surface-50 px-1.5 py-0.5 rounded">
                          <span className="opacity-70">AMT:</span> <span className="font-semibold text-ink">₹{alert.amount.toLocaleString("en-IN")}</span>
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-center border-t border-[var(--border-color)] sm:border-t-0 pt-2 sm:pt-0 mt-1 sm:mt-0 gap-1.5">
                      <span className="text-xs font-semibold text-ink-faint whitespace-nowrap hidden sm:inline-block">
                        {timeAgo(alert.timestamp)}
                      </span>
                      <span className="text-[11px] text-ink-faint whitespace-nowrap">
                        {new Date(alert.timestamp).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <EmptyState 
            icon="🔔" 
            title="No recent alerts" 
            description="No suspicious activity detected. Data will appear here in real-time."
          />
        )}
      </div>
    </div>
  );
}

function KpiCard({ label, value, sublabel, highlight }: {
  label: string; value: string; sublabel?: string | React.ReactNode; highlight?: boolean;
}) {
  return (
    <div className="bg-white rounded-lg p-5 shadow-sm transition-all hover:shadow-md border border-[var(--border-color)]">
      <p className="text-xs font-medium text-ink-muted mb-2 uppercase tracking-wider">{label}</p>
      <p className={`text-2xl font-bold tracking-tight ${highlight ? "text-risk-high" : "text-ink"}`}>{value}</p>
      {sublabel && <p className="text-[11px] font-medium text-ink-muted mt-1.5 bg-surface-50 inline-block px-1.5 py-0.5 rounded">{sublabel}</p>}
    </div>
  );
}
