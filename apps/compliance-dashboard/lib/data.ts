import { AlertRow, ScamCategory, HeatmapCell, KPIData, StateData, Complaint, BankResolution } from "./types";

export const kpiData: KPIData = {
  totalTransactions: 150031,
  highRisk24h: 6324,
  highFraudRate: 87.9,
  highRiskDelta: 412,
  mediumRisk24h: 32540,
  medFraudRate: 16.2,
  overrideRate: 3.8,
  confirmedFraud: 5558,
  estExposureLakhs: 264.26,
  resolutionRate: 25.2,
  avgResolveDays: 45.5,
  resolvedComplaints: 1258,
  totalComplaints: 5000,
  openComplaints: 2776,
  escalatedComplaints: 966,
};

export const alertRows: AlertRow[] = [
  {
    id: "a1",
    vpa: "758d...@upi",
    remark: "electricity disconnection avoid KYC payment",
    risk: "HIGH",
    amount: 500,
    fraudType: "KYC",
    signals: { vpn: true, newDevice: false, ipMismatch: true },
  },
  {
    id: "a2",
    vpa: "9a91...@upi",
    remark: "laptop warranty refund charge",
    risk: "HIGH",
    amount: 4197,
    fraudType: "TECH_SUPPORT",
    signals: { vpn: false, newDevice: true, ipMismatch: true },
  },
  {
    id: "a3",
    vpa: "9cde...@upi",
    remark: "investment return processing fee today only",
    risk: "HIGH",
    amount: 25471,
    fraudType: "INVESTMENT",
    signals: { vpn: true, newDevice: true, ipMismatch: false },
  },
  {
    id: "a4",
    vpa: "df0f...@upi",
    remark: "IT department penalty fee",
    risk: "HIGH",
    amount: 50000,
    fraudType: "IMPERSONATION",
    signals: { vpn: true, newDevice: true, ipMismatch: true },
  },
  {
    id: "a5",
    vpa: "fa7680...@upi",
    remark: "joining fee MNC company",
    risk: "MEDIUM",
    amount: 3284,
    fraudType: "JOB",
    signals: { vpn: false, newDevice: false, ipMismatch: true },
  },
  {
    id: "a6",
    vpa: "53b5...@upi",
    remark: "lunch",
    risk: "LOW",
    amount: 4420,
    fraudType: "NONE",
    signals: { vpn: false, newDevice: false, ipMismatch: false },
  },
];

export const scamCategories: ScamCategory[] = [
  { type: "LOTTERY", complaints: 981, lossLakhs: 68.99 },
  { type: "IMPERSONATION", complaints: 487, lossLakhs: 55.85 },
  { type: "INVESTMENT", complaints: 225, lossLakhs: 53.40 },
  { type: "KYC", complaints: 1441, lossLakhs: 31.68 },
  { type: "TECH_SUPPORT", complaints: 662, lossLakhs: 21.06 },
  { type: "EMERGENCY", complaints: 135, lossLakhs: 19.37 },
  { type: "JOB", complaints: 448, lossLakhs: 13.91 },
];

// Generate heatmap data — realistic pattern with weekend evening spikes
const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

// Deterministic pseudo-random to avoid SSR/client hydration mismatch
function seededRandom(dayIdx: number, hour: number): number {
  const seed = (dayIdx * 24 + hour) * 2654435761;
  return ((seed >>> 0) % 1000) / 1000;
}

function generateHeatmapData(): HeatmapCell[] {
  const data: HeatmapCell[] = [];
  for (let di = 0; di < days.length; di++) {
    const day = days[di];
    for (let hour = 0; hour < 24; hour++) {
      let base = 2.0 + seededRandom(di, hour) * 1.5;

      // Daytime bump
      if (hour >= 9 && hour <= 18) base += 1.5;

      // Evening bump
      if (hour >= 19 && hour <= 23) base += 3.0;

      // Weekend multiplier
      if (day === "Sat" || day === "Sun") {
        base *= 1.4;
        if (hour >= 20 && hour <= 23) base += 3.0;
      }

      // Peak: Sunday 21:00
      if (day === "Sun" && hour === 21) base = 15.02;

      data.push({ day, hour, value: parseFloat(base.toFixed(2)) });
    }
  }
  return data;
}

export const heatmapData: HeatmapCell[] = generateHeatmapData();

export const quickActions = [
  ["Identify highest risk state", "Analyze LOTTERY scam trends", "Summarize SLA violations"],
  ["Review alert override rates", "Compare bank performance", "Detect peak fraud windows"],
];

// State-level fraud data — names match TopoJSON st_nm property exactly
export const stateData: StateData[] = [
  // User-provided top fraud rate states
  { name: "Arunachal Pradesh", fraudRate: 8.95, fraudTxns: 79, fraudVolumeLakhs: 4.82, topScam: "LOTTERY", complaints: 62 },
  { name: "Manipur", fraudRate: 8.70, fraudTxns: 56, fraudVolumeLakhs: 3.15, topScam: "INVESTMENT", complaints: 44 },
  { name: "Meghalaya", fraudRate: 8.64, fraudTxns: 59, fraudVolumeLakhs: 3.48, topScam: "IMPERSONATION", complaints: 47 },
  { name: "Assam", fraudRate: 8.56, fraudTxns: 107, fraudVolumeLakhs: 8.92, topScam: "KYC", complaints: 85 },
  { name: "Bihar", fraudRate: 8.38, fraudTxns: 205, fraudVolumeLakhs: 18.45, topScam: "LOTTERY", complaints: 162 },
  { name: "Jharkhand", fraudRate: 8.37, fraudTxns: 84, fraudVolumeLakhs: 7.14, topScam: "KYC", complaints: 66 },
  { name: "Nagaland", fraudRate: 8.33, fraudTxns: 35, fraudVolumeLakhs: 2.10, topScam: "IMPERSONATION", complaints: 28 },
  { name: "Himachal Pradesh", fraudRate: 8.32, fraudTxns: 108, fraudVolumeLakhs: 9.18, topScam: "TECH_SUPPORT", complaints: 86 },
  { name: "Tripura", fraudRate: 8.28, fraudTxns: 53, fraudVolumeLakhs: 3.71, topScam: "LOTTERY", complaints: 42 },
  { name: "Sikkim", fraudRate: 8.22, fraudTxns: 33, fraudVolumeLakhs: 1.98, topScam: "JOB", complaints: 26 },
  // Generated states (descending fraud rate)
  { name: "West Bengal", fraudRate: 8.15, fraudTxns: 198, fraudVolumeLakhs: 25.48, topScam: "KYC", complaints: 157 },
  { name: "Uttarakhand", fraudRate: 8.10, fraudTxns: 75, fraudVolumeLakhs: 12.82, topScam: "TECH_SUPPORT", complaints: 59 },
  { name: "Rajasthan", fraudRate: 8.05, fraudTxns: 312, fraudVolumeLakhs: 45.22, topScam: "LOTTERY", complaints: 248 },
  { name: "Madhya Pradesh", fraudRate: 8.01, fraudTxns: 287, fraudVolumeLakhs: 38.40, topScam: "IMPERSONATION", complaints: 228 },
  { name: "Uttar Pradesh", fraudRate: 7.98, fraudTxns: 425, fraudVolumeLakhs: 68.92, topScam: "KYC", complaints: 520 },
  { name: "Chhattisgarh", fraudRate: 7.92, fraudTxns: 96, fraudVolumeLakhs: 14.22, topScam: "LOTTERY", complaints: 76 },
  { name: "Maharashtra", fraudRate: 7.88, fraudTxns: 487, fraudVolumeLakhs: 103.64, topScam: "LOTTERY", complaints: 480 },
  { name: "Odisha", fraudRate: 7.85, fraudTxns: 142, fraudVolumeLakhs: 18.52, topScam: "INVESTMENT", complaints: 113 },
  { name: "Delhi", fraudRate: 7.82, fraudTxns: 185, fraudVolumeLakhs: 32.14, topScam: "IMPERSONATION", complaints: 147 },
  { name: "Punjab", fraudRate: 7.78, fraudTxns: 125, fraudVolumeLakhs: 16.82, topScam: "KYC", complaints: 99 },
  { name: "Haryana", fraudRate: 7.72, fraudTxns: 118, fraudVolumeLakhs: 15.42, topScam: "JOB", complaints: 94 },
  { name: "Gujarat", fraudRate: 7.65, fraudTxns: 245, fraudVolumeLakhs: 42.84, topScam: "INVESTMENT", complaints: 195 },
  { name: "Telangana", fraudRate: 7.55, fraudTxns: 178, fraudVolumeLakhs: 28.62, topScam: "TECH_SUPPORT", complaints: 141 },
  { name: "Karnataka", fraudRate: 7.48, fraudTxns: 265, fraudVolumeLakhs: 40.22, topScam: "IMPERSONATION", complaints: 210 },
  { name: "Andhra Pradesh", fraudRate: 7.42, fraudTxns: 195, fraudVolumeLakhs: 29.84, topScam: "KYC", complaints: 155 },
  { name: "Tamil Nadu", fraudRate: 7.35, fraudTxns: 285, fraudVolumeLakhs: 38.52, topScam: "LOTTERY", complaints: 226 },
  { name: "Kerala", fraudRate: 7.28, fraudTxns: 155, fraudVolumeLakhs: 22.42, topScam: "TECH_SUPPORT", complaints: 123 },
  { name: "Goa", fraudRate: 7.15, fraudTxns: 28, fraudVolumeLakhs: 4.22, topScam: "EMERGENCY", complaints: 22 },
  { name: "Mizoram", fraudRate: 7.05, fraudTxns: 22, fraudVolumeLakhs: 3.12, topScam: "JOB", complaints: 17 },
  // Union Territories
  { name: "Jammu and Kashmir", fraudRate: 7.95, fraudTxns: 68, fraudVolumeLakhs: 9.84, topScam: "LOTTERY", complaints: 54 },
  { name: "Ladakh", fraudRate: 7.02, fraudTxns: 8, fraudVolumeLakhs: 0.92, topScam: "KYC", complaints: 6 },
  { name: "Chandigarh", fraudRate: 7.18, fraudTxns: 15, fraudVolumeLakhs: 2.14, topScam: "IMPERSONATION", complaints: 12 },
  { name: "Puducherry", fraudRate: 7.12, fraudTxns: 12, fraudVolumeLakhs: 1.68, topScam: "LOTTERY", complaints: 9 },
  { name: "Andaman and Nicobar Islands", fraudRate: 6.98, fraudTxns: 6, fraudVolumeLakhs: 0.72, topScam: "EMERGENCY", complaints: 5 },
  { name: "Lakshadweep", fraudRate: 7.08, fraudTxns: 4, fraudVolumeLakhs: 0.48, topScam: "KYC", complaints: 3 },
  { name: "Dadra and Nagar Haveli and Daman and Diu", fraudRate: 7.22, fraudTxns: 10, fraudVolumeLakhs: 1.42, topScam: "JOB", complaints: 8 },
];

// Bank resolution data — top 10 slowest banks
export const bankResolutionData: BankResolution[] = [
  { bank: "BOB006", avgDays: 67.2, complaints: 142 },
  { bank: "UNION008", avgDays: 63.8, complaints: 98 },
  { bank: "PNB005", avgDays: 58.4, complaints: 215 },
  { bank: "INDIAN009", avgDays: 55.1, complaints: 87 },
  { bank: "CANARA007", avgDays: 52.6, complaints: 124 },
  { bank: "UCO011", avgDays: 49.8, complaints: 76 },
  { bank: "CENTRAL012", avgDays: 47.3, complaints: 65 },
  { bank: "ICICI003", avgDays: 44.2, complaints: 312 },
  { bank: "AXIS004", avgDays: 41.8, complaints: 278 },
  { bank: "HDFC002", avgDays: 38.5, complaints: 345 },
];

// Complaints data — realistic sample rows
const scamTypes = ["KYC", "LOTTERY", "TECH_SUPPORT", "IMPERSONATION", "JOB", "INVESTMENT", "EMERGENCY"] as const;
const statuses: Array<"OPEN" | "RESOLVED" | "ESCALATED"> = ["OPEN", "RESOLVED", "ESCALATED"];
const banks = ["SBI001", "HDFC002", "ICICI003", "AXIS004", "PNB005", "BOB006", "CANARA007", "UNION008", "KOTAK010"];
const states = ["Maharashtra", "Uttar Pradesh", "Bihar", "Rajasthan", "Tamil Nadu", "Karnataka", "Gujarat", "Odisha", "Telangana", "West Bengal", "Delhi", "Assam", "Kerala", "Punjab", "Haryana", "Madhya Pradesh", "Jharkhand", "Andhra Pradesh", "Chhattisgarh", "Himachal Pradesh"];

function genHex(seed: number): string {
  return ((seed * 2654435761) >>> 0).toString(16).toUpperCase().padStart(8, "0");
}

export const complaintsData: Complaint[] = [
  // User-specified rows
  { id: "SATARK-A77DCC1A", date: "2024-03-23", scamType: "KYC", amount: 500, status: "OPEN", bank: "AXIS004", state: "Odisha", daysOpen: null },
  { id: "SATARK-5A8FEE02", date: "2024-02-16", scamType: "LOTTERY", amount: 13099, status: "OPEN", bank: "AXIS004", state: "Telangana", daysOpen: null },
  // Generated rows
  ...Array.from({ length: 38 }, (_, i) => {
    const seed = i + 100;
    const statusIdx = seed % 5 < 3 ? 0 : seed % 5 < 4 ? 2 : 1; // ~55% OPEN, ~20% ESCALATED, ~25% RESOLVED
    const status = statuses[statusIdx];
    const scam = scamTypes[seed % scamTypes.length];
    const month = ((seed % 12) + 1).toString().padStart(2, "0");
    const day = ((seed % 28) + 1).toString().padStart(2, "0");
    const amounts = [500, 1200, 2500, 3284, 4197, 5000, 8500, 10000, 13099, 15000, 25000, 25471, 50000];
    return {
      id: `SATARK-${genHex(seed)}`,
      date: `2024-${month}-${day}`,
      scamType: scam,
      amount: amounts[seed % amounts.length],
      status,
      bank: banks[seed % banks.length],
      state: states[seed % states.length],
      daysOpen: status === "RESOLVED" ? 15 + (seed % 45) : status === "ESCALATED" ? 35 + (seed % 60) : null,
    };
  }),
];

// ── Analytics API Fetchers ──

export async function fetchGeoHeatmap() {
  const res = await fetch("/api/analytics", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ table: "geo_heatmap" }),
  });
  if (!res.ok) throw new Error("Failed to fetch geo_heatmap");
  const data = await res.json();
  return data.data; // Array of GeoHeatmapRow
}

export async function fetchScamTaxonomy() {
  const res = await fetch("/api/analytics", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ table: "scam_taxonomy" }),
  });
  if (!res.ok) throw new Error("Failed to fetch scam_taxonomy");
  const data = await res.json();
  return data.data; // Array of ScamTaxonomyRow
}

export async function fetchRiskDistribution() {
  const res = await fetch("/api/analytics", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ table: "risk_distribution" }),
  });
  if (!res.ok) throw new Error("Failed to fetch risk_distribution");
  const data = await res.json();
  return data.data; // Array of RiskDistributionRow
}

export async function fetchHourlyPattern() {
  const res = await fetch("/api/analytics", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ table: "hourly_fraud_pattern" }),
  });
  if (!res.ok) throw new Error("Failed to fetch hourly_fraud_pattern");
  const data = await res.json();
  return data.data; // Array of HourlyPatternRow
}

export async function fetchAlertEffectiveness() {
  const res = await fetch("/api/analytics", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ table: "alert_effectiveness" }),
  });
  if (!res.ok) throw new Error("Failed to fetch alert_effectiveness");
  const data = await res.json();
  return data.data; // Array of AlertEffectivenessRow
}
