import { KpiSummary } from "@/types";
import { executeStatement } from "./client";

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

/**
 * Fetch dashboard KPIs from Gold tables.
 * Falls back to mock data if Databricks is unavailable.
 */
export async function fetchKpiSummary(): Promise<KpiSummary> {
  const sql = `
    SELECT
      COUNT(*) AS total_transactions,
      SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) AS fraud_count,
      AVG(CASE WHEN is_fraud THEN amount_numeric ELSE NULL END) AS avg_fraud_amount,
      MODE(CASE WHEN is_fraud THEN fraud_type ELSE NULL END) AS top_scam_type
    FROM gold_transactions
  `;

  const rows = await executeStatement(sql);
  if (!rows || rows.length === 0) return MOCK_KPI;

  const r = rows[0];

  // Also fetch complaint stats
  const complaintSql = `
    SELECT
      SUM(CASE WHEN complaint_status = 'OPEN' THEN 1 ELSE 0 END) AS open_count,
      SUM(CASE WHEN complaint_status = 'RESOLVED' THEN 1 ELSE 0 END) AS resolved_count,
      AVG(CASE WHEN resolution_days IS NOT NULL THEN resolution_days ELSE NULL END) AS avg_resolution
    FROM gold_complaints
  `;

  const cRows = await executeStatement(complaintSql);
  const c = cRows?.[0];

  const totalTxn = parseInt(r.total_transactions) || MOCK_KPI.totalTransactions;
  const fraudCount = parseInt(r.fraud_count) || MOCK_KPI.fraudCount;

  return {
    totalTransactions: totalTxn,
    fraudCount,
    fraudRate: totalTxn > 0 ? fraudCount / totalTxn : 0,
    avgFraudAmount: parseFloat(r.avg_fraud_amount) || MOCK_KPI.avgFraudAmount,
    topScamType: r.top_scam_type || MOCK_KPI.topScamType,
    complaintsOpen: c ? parseInt(c.open_count) || 0 : MOCK_KPI.complaintsOpen,
    complaintsResolved: c ? parseInt(c.resolved_count) || 0 : MOCK_KPI.complaintsResolved,
    avgResolutionDays: c ? parseFloat(c.avg_resolution) || 0 : MOCK_KPI.avgResolutionDays,
  };
}
