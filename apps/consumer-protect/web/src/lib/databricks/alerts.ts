import { AlertItem, RiskLevel } from "@/types";
import { executeStatement } from "./client";

const MOCK_ALERTS: AlertItem[] = [
  {
    id: "alert-1",
    timestamp: "2024-03-15T22:14:00Z",
    type: "KYC",
    severity: "high" as RiskLevel,
    message: "Spike in KYC scam transactions from Maharashtra region",
    vpaMasked: "a***9@upi",
    amount: 4500,
  },
  {
    id: "alert-2",
    timestamp: "2024-03-15T21:45:00Z",
    type: "IMPERSONATION",
    severity: "critical" as RiskLevel,
    message: "Mule VPA cluster detected — 35 unique senders in 1 hour",
    vpaMasked: "m***2@paytm",
    amount: 28000,
  },
  {
    id: "alert-3",
    timestamp: "2024-03-15T20:30:00Z",
    type: "INVESTMENT",
    severity: "high" as RiskLevel,
    message: "High-value investment scam pattern — multiple ₹50K+ transfers",
    vpaMasked: "i***7@okaxis",
    amount: 55000,
  },
  {
    id: "alert-4",
    timestamp: "2024-03-15T19:20:00Z",
    type: "LOTTERY",
    severity: "medium" as RiskLevel,
    message: "KBC lottery scam remark detected in 12 transactions",
    vpaMasked: "l***4@oksbi",
    amount: 8000,
  },
  {
    id: "alert-5",
    timestamp: "2024-03-15T18:00:00Z",
    type: "TECH_SUPPORT",
    severity: "medium" as RiskLevel,
    message: "Amazon refund scam remarks trending in Gujarat",
    vpaMasked: "t***1@ybl",
    amount: 3200,
  },
];

/**
 * Fetch recent fraud alerts from the alert feed.
 * Falls back to mock alerts if Databricks is unavailable.
 */
export async function fetchAlerts(limit = 10): Promise<AlertItem[]> {
  const sql = `
    SELECT
      txn_id AS id,
      txn_timestamp AS timestamp,
      fraud_type AS type,
      amount_numeric AS amount,
      recipient_vpa_hash AS vpa_masked,
      upi_remark AS message
    FROM gold_transactions
    WHERE is_fraud = true
    ORDER BY txn_timestamp DESC
    LIMIT ${limit}
  `;

  const rows = await executeStatement(sql);
  if (!rows || rows.length === 0) return MOCK_ALERTS;

  return rows.map((r) => {
    const amount = parseFloat(r.amount);
    const severity: RiskLevel =
      amount > 25000 ? "critical" : amount > 10000 ? "high" : amount > 3000 ? "medium" : "low";

    return {
      id: r.id,
      timestamp: r.timestamp,
      type: r.type,
      severity,
      message: `${r.type} scam detected: "${r.message}"`,
      vpaMasked: r.vpa_masked?.substring(0, 4) + "***",
      amount,
    };
  });
}
