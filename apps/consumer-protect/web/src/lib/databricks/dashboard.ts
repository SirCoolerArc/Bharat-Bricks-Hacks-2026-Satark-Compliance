import { KpiSummary, AlertItem } from "@/types";
import { BarChartItem } from "@/components/BarChart";
import { DonutSegment } from "@/components/DonutChart";
import { executeStatement } from "./client";

// ─────────────────────────────────────────────
// Extended dashboard data — scam breakdown, complaint status, trend
// Calls Databricks SQL API on workspace.satark.gold_risk_scores
// ─────────────────────────────────────────────

export interface DashboardData {
  kpi: KpiSummary;
  alerts: AlertItem[];
  scamBreakdown: BarChartItem[];
  complaintStatus: DonutSegment[];
  monthlyTrend: BarChartItem[];
}

// ── Mock Fallback (if SQL fails/unconfigured) ──

const MOCK_KPI: KpiSummary = {
  totalTransactions: 150000,
  fraudCount: 9450,
  fraudRate: 0.063,
  avgFraudAmount: 12350,
  topScamType: "KYC",
  complaintsOpen: 2750,
  complaintsResolved: 1250,
  avgResolutionDays: 18,
};

const MOCK_ALERTS: AlertItem[] = [
  { id: "a1", timestamp: "2024-03-15T22:14:00Z", type: "KYC", severity: "high", message: "KYC scam spike detected in Maharashtra", vpaMasked: "a***9@upi", amount: 4500 },
  { id: "a2", timestamp: "2024-03-15T21:45:00Z", type: "IMPERSONATION", severity: "critical", message: "Mule VPA cluster — 35 unique senders in 1hr", vpaMasked: "m***2@paytm", amount: 28000 },
];

const MOCK_SCAM_BREAKDOWN: BarChartItem[] = [
  { label: "KYC", value: 3024, color: "var(--risk-high)" },
  { label: "IMPERSONATION", value: 2079, color: "var(--risk-critical)" },
  { label: "TECH_SUPPORT", value: 1512, color: "var(--risk-medium)" },
  { label: "LOTTERY", value: 1134, color: "var(--accent)" },
];

const MOCK_COMPLAINT_STATUS: DonutSegment[] = [
  { label: "Open", value: 2750, color: "var(--risk-medium)" },
  { label: "Escalated", value: 1000, color: "var(--risk-high)" },
  { label: "Resolved", value: 1250, color: "var(--risk-low)" },
];

const MOCK_MONTHLY_TREND: BarChartItem[] = [
  { label: "Oct", value: 1420 },
  { label: "Nov", value: 1680 },
  { label: "Dec", value: 2100 },
  { label: "Jan", value: 1890 },
  { label: "Feb", value: 2340 },
  { label: "Mar", value: 2020 },
];

/**
 * Fetch all dashboard data using the Databricks REST API.
 */
export async function fetchDashboardData(): Promise<DashboardData> {
  try {
    const scamSql = `
      SELECT scam_type, COUNT(*) as cnt 
      FROM workspace.satark.gold_risk_scores 
      WHERE is_fraud = 1 
      GROUP BY scam_type 
      ORDER BY cnt DESC
      LIMIT 6
    `;
    const scamRows = await executeStatement(scamSql);

    if (scamRows && scamRows.length > 0) {
      const colors = ["var(--risk-high)", "var(--risk-critical)", "var(--risk-medium)", "var(--accent)", "#8E24AA", "var(--risk-low)"];
      const scamBreakdown: BarChartItem[] = scamRows.map((r, i) => ({
        label: r.scam_type.length > 10 ? r.scam_type.slice(0, 10) : r.scam_type,
        value: parseInt(r.cnt),
        color: colors[i % colors.length],
      }));

      const [kpiResult, alertsResult] = await Promise.all([
        fetchKpi(),
        fetchRecentAlerts(),
      ]);

      return {
        kpi: kpiResult,
        alerts: alertsResult,
        scamBreakdown,
        complaintStatus: MOCK_COMPLAINT_STATUS, // Complaints logic usually belongs in a separate gold_complaints table
        monthlyTrend: MOCK_MONTHLY_TREND,
      };
    }
  } catch (err) {
    console.warn("[dashboard] Databricks unavailable or query failed. Using mock data.");
  }

  return {
    kpi: MOCK_KPI,
    alerts: MOCK_ALERTS,
    scamBreakdown: MOCK_SCAM_BREAKDOWN,
    complaintStatus: MOCK_COMPLAINT_STATUS,
    monthlyTrend: MOCK_MONTHLY_TREND,
  };
}

// ── Internal SQL Fetch Helpers ──

async function fetchKpi(): Promise<KpiSummary> {
  const sql = `
    SELECT 
      COUNT(*) as total, 
      SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) as fraud,
      AVG(CASE WHEN is_fraud = 1 THEN amount ELSE NULL END) as avg_amt
    FROM workspace.satark.gold_risk_scores
  `;
  const rows = await executeStatement(sql);
  
  if (!rows || rows.length === 0) return MOCK_KPI;
  
  const r = rows[0];
  const total = parseInt(r.total || "0");
  const fraud = parseInt(r.fraud || "0");
  const avgAmt = parseFloat(r.avg_amt || "0");

  return {
    ...MOCK_KPI,
    totalTransactions: total > 0 ? total : MOCK_KPI.totalTransactions,
    fraudCount: fraud > 0 ? fraud : MOCK_KPI.fraudCount,
    fraudRate: total > 0 ? fraud / total : MOCK_KPI.fraudRate,
    avgFraudAmount: avgAmt > 0 ? avgAmt : MOCK_KPI.avgFraudAmount,
  };
}

async function fetchRecentAlerts(): Promise<AlertItem[]> {
  const sql = `
    SELECT transaction_id, timestamp, scam_type, amount, recipient_vpa, risk_score 
    FROM workspace.satark.gold_risk_scores 
    WHERE is_fraud = 1 
    ORDER BY timestamp DESC 
    LIMIT 5
  `;
  const rows = await executeStatement(sql);
  
  if (!rows || rows.length === 0) return MOCK_ALERTS;

  return rows.map((r) => {
    const riskScore = parseFloat(r.risk_score || "0");
    const severity = riskScore >= 0.85 ? "critical" : riskScore >= 0.60 ? "high" : "medium";
    const amount = parseFloat(r.amount || "0");
    const vpa = r.recipient_vpa || "unknown";
    
    return {
      id: r.transaction_id || `txn-${Date.now()}`,
      timestamp: r.timestamp || new Date().toISOString(),
      type: r.scam_type || "UNKNOWN",
      severity: severity,
      message: `${r.scam_type || "Scam"} detected with ${(riskScore * 100).toFixed(0)}% confidence`,
      vpaMasked: vpa.length > 5 ? vpa.substring(0, 4) + "***" : vpa,
      amount: amount,
    };
  });
}
