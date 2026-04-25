"use client";

import { useState, useMemo } from "react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import { kpiData, scamCategories, bankResolutionData, complaintsData } from "@/lib/data";
import { ComplaintStatus } from "@/lib/types";

// ── Status config ──
const statusConfig: Record<
  ComplaintStatus,
  { color: string; bg: string; label: string }
> = {
  OPEN: { color: "#D97706", bg: "#FFFBEB", label: "OPEN" },
  RESOLVED: { color: "#16A34A", bg: "#F0FDF4", label: "RESOLVED" },
  ESCALATED: { color: "#DC2626", bg: "#FEF2F2", label: "ESCALATED" },
};

// ── Donut data ──
const donutData = [
  { name: "OPEN", value: kpiData.openComplaints, color: "#D97706" },
  { name: "RESOLVED", value: kpiData.resolvedComplaints, color: "#16A34A" },
  { name: "ESCALATED", value: kpiData.escalatedComplaints, color: "#DC2626" },
];

// ── Scam complaints bar data ──
const scamBarData = scamCategories
  .map((s) => ({ name: s.type, complaints: s.complaints }))
  .sort((a, b) => b.complaints - a.complaints);

// ── SLA breach calculation ──
const SLA_DAYS = 30;
const slaBreached = complaintsData.filter(
  (c) => c.daysOpen !== null && c.daysOpen > SLA_DAYS
).length;

// ── Unique filter values ──
const uniqueStatuses: ComplaintStatus[] = ["OPEN", "RESOLVED", "ESCALATED"];
const uniqueScamTypes = Array.from(new Set(complaintsData.map((c) => c.scamType))).sort();
const uniqueStates = Array.from(new Set(complaintsData.map((c) => c.state))).sort();
const uniqueBanks = Array.from(new Set(complaintsData.map((c) => c.bank))).sort();

const ROWS_PER_PAGE = 20;

// ── Custom Tooltips ──
interface BankTooltipProps {
  active?: boolean;
  payload?: Array<{ payload: (typeof bankResolutionData)[0] }>;
}
function BankTooltip({ active, payload }: BankTooltipProps) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-sidebar text-white text-xs px-3 py-2 rounded border border-white/10">
      <p className="font-semibold mb-0.5">{d.bank}</p>
      <p>Avg: {d.avgDays} days</p>
      <p>{d.complaints} complaints</p>
    </div>
  );
}

interface ScamTooltipProps {
  active?: boolean;
  payload?: Array<{ payload: (typeof scamBarData)[0] }>;
}
function ScamTooltip({ active, payload }: ScamTooltipProps) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-sidebar text-white text-xs px-3 py-2 rounded border border-white/10">
      <p className="font-semibold">{d.name}</p>
      <p>{d.complaints.toLocaleString()} complaints</p>
    </div>
  );
}

// ── Donut center label (custom) ──
function DonutCenter() {
  return (
    <text
      x="50%"
      y="50%"
      textAnchor="middle"
      dominantBaseline="central"
      className="fill-text-primary"
    >
      <tspan x="50%" dy="-8" fontSize="20" fontWeight="600">
        {kpiData.totalComplaints.toLocaleString()}
      </tspan>
      <tspan x="50%" dy="18" fontSize="10" className="fill-text-muted">
        TOTAL
      </tspan>
    </text>
  );
}

export default function ComplaintsPage() {
  const [page, setPage] = useState(0);
  const [filterStatus, setFilterStatus] = useState<string>("ALL");
  const [filterScam, setFilterScam] = useState<string>("ALL");
  const [filterState, setFilterState] = useState<string>("ALL");
  const [filterBank, setFilterBank] = useState<string>("ALL");

  const filtered = useMemo(() => {
    return complaintsData.filter((c) => {
      if (filterStatus !== "ALL" && c.status !== filterStatus) return false;
      if (filterScam !== "ALL" && c.scamType !== filterScam) return false;
      if (filterState !== "ALL" && c.state !== filterState) return false;
      if (filterBank !== "ALL" && c.bank !== filterBank) return false;
      return true;
    });
  }, [filterStatus, filterScam, filterState, filterBank]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / ROWS_PER_PAGE));
  const pageData = filtered.slice(
    page * ROWS_PER_PAGE,
    (page + 1) * ROWS_PER_PAGE
  );

  // Reset page when filters change
  const handleFilter = (
    setter: React.Dispatch<React.SetStateAction<string>>,
    value: string
  ) => {
    setter(value);
    setPage(0);
  };

  return (
    <div className="p-4 space-y-4 overflow-y-auto h-[calc(100vh-48px)]">
      {/* ── KPI STRIP ── */}
      <div className="grid grid-cols-4 gap-3">
        <div className="bg-card border border-border rounded-md px-4 py-3.5">
          <p className="text-label uppercase text-text-muted font-medium mb-1">
            Total Complaints
          </p>
          <p className="text-kpi text-text-primary leading-none mb-1">
            {kpiData.totalComplaints.toLocaleString()}
          </p>
          <p className="text-label text-text-muted">All time filed</p>
        </div>
        <div className="bg-white/70 backdrop-blur-md border border-white/40 shadow-card hover:shadow-soft transition-all duration-300 rounded-2xl px-5 py-4">
          <p className="text-label uppercase text-text-muted font-medium mb-1">
            Resolution Rate
          </p>
          <p className="text-kpi text-risk-low leading-none mb-1">
            {kpiData.resolutionRate}%
          </p>
          <p className="text-label text-text-muted">
            {kpiData.resolvedComplaints.toLocaleString()} resolved
          </p>
        </div>
        <div className="bg-white/70 backdrop-blur-md border border-white/40 shadow-card hover:shadow-soft transition-all duration-300 rounded-2xl px-5 py-4">
          <p className="text-label uppercase text-text-muted font-medium mb-1">
            Avg Resolution Time
          </p>
          <p className="text-kpi text-text-primary leading-none mb-1">
            {kpiData.avgResolveDays}d
          </p>
          <p className="text-label text-text-muted">days to resolve</p>
        </div>
        <div className="bg-risk-high-bg/80 backdrop-blur-md border border-risk-high/20 shadow-card hover:shadow-soft transition-all duration-300 rounded-2xl px-5 py-4">
          <p className="text-label uppercase text-risk-high font-bold mb-1">
            SLA Breached ({">"}30d)
          </p>
          <p className="text-kpi text-risk-high leading-none mb-1">
            {slaBreached}
          </p>
          <p className="text-label text-risk-high/70">
            require immediate action
          </p>
        </div>
      </div>

      {/* ── SECTION 1: 3-Panel Charts ── */}
      <div className="grid grid-cols-3 gap-4">
        {/* Panel A: Donut Chart */}
        <div className="bg-white/70 backdrop-blur-md border border-white/40 shadow-card hover:shadow-soft transition-all duration-300 rounded-2xl overflow-hidden flex flex-col">
          <div className="px-5 py-4 border-b border-border/50 bg-white/40">
            <h2 className="text-body font-semibold text-text-primary">
              Complaints Status
            </h2>
          </div>
          <div className="p-4">
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={donutData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={2}
                  dataKey="value"
                  stroke="none"
                >
                  {donutData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <DonutCenter />
              </PieChart>
            </ResponsiveContainer>
            {/* Legend */}
            <div className="flex justify-center gap-4 mt-2">
              {donutData.map((d) => (
                <div key={d.name} className="flex items-center gap-1.5">
                  <div
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: d.color }}
                  />
                  <span className="text-label text-text-secondary">
                    {d.name}{" "}
                    <span className="font-semibold text-text-primary">
                      {d.value.toLocaleString()}
                    </span>{" "}
                    (
                    {((d.value / kpiData.totalComplaints) * 100).toFixed(1)}
                    %)
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Panel B: Avg Resolution Days by Bank */}
        <div className="bg-white/70 backdrop-blur-md border border-white/40 shadow-card hover:shadow-soft transition-all duration-300 rounded-2xl overflow-hidden flex flex-col">
          <div className="px-5 py-4 border-b border-border/50 bg-white/40">
            <h2 className="text-body font-semibold text-text-primary">
              Avg Resolution Days by Bank
            </h2>
          </div>
          <div className="p-4 flex-1">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart
                data={bankResolutionData}
                layout="vertical"
                margin={{ top: 0, right: 10, bottom: 0, left: 0 }}
                barSize={14}
              >
                <CartesianGrid
                  horizontal={false}
                  stroke="#E5E4DE"
                  strokeDasharray="3 3"
                />
                <XAxis
                  type="number"
                  tick={{ fontSize: 10, fill: "#9CA3AF" }}
                  axisLine={false}
                  tickLine={false}
                  domain={[0, 80]}
                  tickFormatter={(v: number) => `${v}d`}
                />
                <YAxis
                  type="category"
                  dataKey="bank"
                  tick={{ fontSize: 10, fill: "#6B7280", fontFamily: "monospace" }}
                  axisLine={false}
                  tickLine={false}
                  width={80}
                />
                <Tooltip
                  content={<BankTooltip />}
                  cursor={{ fill: "rgba(0,0,0,0.03)" }}
                />
                <Bar dataKey="avgDays" radius={[0, 2, 2, 0]}>
                  {bankResolutionData.map((entry) => (
                    <Cell
                      key={entry.bank}
                      fill={
                        entry.avgDays > 50
                          ? "#DC2626"
                          : entry.avgDays > 40
                          ? "#D97706"
                          : "#16A34A"
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Panel C: Complaints by Scam Type */}
        <div className="bg-white/70 backdrop-blur-md border border-white/40 shadow-card hover:shadow-soft transition-all duration-300 rounded-2xl overflow-hidden flex flex-col">
          <div className="px-5 py-4 border-b border-border/50 bg-white/40">
            <h2 className="text-body font-semibold text-text-primary">
              Complaints by Scam Type
            </h2>
          </div>
          <div className="p-4 flex-1">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart
                data={scamBarData}
                layout="vertical"
                margin={{ top: 0, right: 10, bottom: 0, left: 0 }}
                barSize={14}
              >
                <CartesianGrid
                  horizontal={false}
                  stroke="#E5E4DE"
                  strokeDasharray="3 3"
                />
                <XAxis
                  type="number"
                  tick={{ fontSize: 10, fill: "#9CA3AF" }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fontSize: 10, fill: "#6B7280", fontFamily: "monospace" }}
                  axisLine={false}
                  tickLine={false}
                  width={100}
                />
                <Tooltip
                  content={<ScamTooltip />}
                  cursor={{ fill: "rgba(0,0,0,0.03)" }}
                />
                <Bar dataKey="complaints" fill="#1D6FA5" radius={[0, 2, 2, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* ── SECTION 2: Complaints Table ── */}
      <div className="bg-white/70 backdrop-blur-md border border-white/40 shadow-card hover:shadow-soft transition-all duration-300 rounded-2xl overflow-hidden flex flex-col min-h-[400px]">
        {/* Header + Filters */}
        <div className="px-5 py-4 border-b border-border/50 bg-white/40">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-body font-semibold text-text-primary">
              Complaints Register
            </h2>
            <span className="text-label text-text-muted">
              {filtered.length} of {complaintsData.length} complaints
            </span>
          </div>
          <div className="flex gap-2 flex-wrap">
            {/* Status filter */}
            <select
              value={filterStatus}
              onChange={(e) => handleFilter(setFilterStatus, e.target.value)}
              className="text-[11px] px-2 py-1 border border-border rounded bg-white text-text-primary focus:outline-none focus:border-nav-active"
            >
              <option value="ALL">All Status</option>
              {uniqueStatuses.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            {/* Scam type filter */}
            <select
              value={filterScam}
              onChange={(e) => handleFilter(setFilterScam, e.target.value)}
              className="text-[11px] px-2 py-1 border border-border rounded bg-white text-text-primary focus:outline-none focus:border-nav-active"
            >
              <option value="ALL">All Scam Types</option>
              {uniqueScamTypes.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            {/* State filter */}
            <select
              value={filterState}
              onChange={(e) => handleFilter(setFilterState, e.target.value)}
              className="text-[11px] px-2 py-1 border border-border rounded bg-white text-text-primary focus:outline-none focus:border-nav-active"
            >
              <option value="ALL">All States</option>
              {uniqueStates.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            {/* Bank filter */}
            <select
              value={filterBank}
              onChange={(e) => handleFilter(setFilterBank, e.target.value)}
              className="text-[11px] px-2 py-1 border border-border rounded bg-white text-text-primary focus:outline-none focus:border-nav-active"
            >
              <option value="ALL">All Banks</option>
              {uniqueBanks.map((b) => (
                <option key={b} value={b}>
                  {b}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Table header */}
        <div className="grid grid-cols-[140px_90px_100px_90px_90px_90px_120px_70px] gap-2 px-5 py-3 border-b border-border/50 bg-white/30 backdrop-blur">
          <span className="text-label uppercase text-text-muted font-medium">
            Complaint ID
          </span>
          <span className="text-label uppercase text-text-muted font-medium">
            Date
          </span>
          <span className="text-label uppercase text-text-muted font-medium">
            Scam Type
          </span>
          <span className="text-label uppercase text-text-muted font-medium text-right">
            Amount
          </span>
          <span className="text-label uppercase text-text-muted font-medium">
            Status
          </span>
          <span className="text-label uppercase text-text-muted font-medium">
            Bank
          </span>
          <span className="text-label uppercase text-text-muted font-medium">
            State
          </span>
          <span className="text-label uppercase text-text-muted font-medium text-right">
            Days
          </span>
        </div>

        {/* Table rows */}
        <div className="overflow-x-auto">
          {pageData.length > 0 ? (
            pageData.map((c) => {
              const sc = statusConfig[c.status];
              const isBreach = c.daysOpen !== null && c.daysOpen > SLA_DAYS;
              return (
                <div
                  key={c.id}
                  className="grid grid-cols-[140px_90px_100px_90px_90px_90px_120px_70px] gap-2 px-5 py-3 border-b border-border/30 hover:bg-white/60 transition-colors items-center cursor-pointer"
                >
                  <span className="text-body font-mono text-xs text-text-primary truncate">
                    {c.id}
                  </span>
                  <span className="text-body text-text-secondary text-xs">
                    {c.date}
                  </span>
                  <span className="text-body text-text-primary text-xs font-mono">
                    {c.scamType}
                  </span>
                  <span className="text-body text-text-primary text-xs text-right font-medium">
                    ₹{c.amount.toLocaleString()}
                  </span>
                  <span>
                    <span
                      className="text-[10px] font-semibold px-2 py-0.5 rounded-full"
                      style={{
                        color: sc.color,
                        backgroundColor: sc.bg,
                        border: `1px solid ${sc.color}30`,
                      }}
                    >
                      {sc.label}
                    </span>
                  </span>
                  <span className="text-body text-text-secondary text-xs font-mono">
                    {c.bank}
                  </span>
                  <span className="text-body text-text-secondary text-xs truncate">
                    {c.state}
                  </span>
                  <span
                    className={`text-body text-xs text-right font-mono ${
                      isBreach
                        ? "text-risk-high font-semibold"
                        : "text-text-secondary"
                    }`}
                  >
                    {c.daysOpen !== null ? c.daysOpen : "—"}
                  </span>
                </div>
              );
            })
          ) : (
            <div className="px-4 py-8 text-center text-text-muted text-body w-full">
              No complaints match the selected filters.
            </div>
          )}
        </div>

        {/* Pagination */}
        <div className="px-4 py-3 border-t border-border flex items-center justify-between">
          <span className="text-label text-text-muted">
            Page {page + 1} of {totalPages} · Showing{" "}
            {page * ROWS_PER_PAGE + 1}–
            {Math.min((page + 1) * ROWS_PER_PAGE, filtered.length)} of{" "}
            {filtered.length}
          </span>
          <div className="flex gap-1">
            <button
              disabled={page === 0}
              onClick={() => setPage((p) => p - 1)}
              className="text-[11px] px-2.5 py-1 rounded border border-border text-text-secondary hover:bg-gray-50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              ← Prev
            </button>
            {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => (
              <button
                key={i}
                onClick={() => setPage(i)}
                className={`text-[11px] w-7 py-1 rounded border transition-colors ${
                  page === i
                    ? "bg-nav-active-bg border-nav-active/30 text-nav-active font-semibold"
                    : "border-border text-text-secondary hover:bg-gray-50"
                }`}
              >
                {i + 1}
              </button>
            ))}
            <button
              disabled={page >= totalPages - 1}
              onClick={() => setPage((p) => p + 1)}
              className="text-[11px] px-2.5 py-1 rounded border border-border text-text-secondary hover:bg-gray-50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              Next →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
