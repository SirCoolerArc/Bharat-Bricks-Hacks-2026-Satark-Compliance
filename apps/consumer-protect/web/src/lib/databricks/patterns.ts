import { FraudPattern, RiskLevel } from "@/types";
import { executeStatement } from "./client";

const MOCK_PATTERNS: FraudPattern[] = [
  {
    id: "pat-kyc",
    type: "KYC",
    title: "KYC Update Scam",
    description:
      "Fraudsters impersonate utility companies or banks, demanding a 'KYC verification fee' to prevent disconnection or account freeze.",
    exampleRemark: "electricity KYC penalty avoid disconnection",
    avgAmountRange: "₹500 – ₹5,000",
    frequency: "Very Common",
    riskLevel: "high",
    tips: [
      "No bank or utility asks for KYC fees via UPI",
      "Verify through the official app or branch",
      "Do not click links in SMS or WhatsApp messages",
    ],
  },
  {
    id: "pat-impersonation",
    type: "IMPERSONATION",
    title: "Authority Impersonation",
    description:
      "Scammers pose as CBI, income tax, or police officials, threatening arrest unless an immediate 'settlement fee' is paid.",
    exampleRemark: "CBI officer case settlement fee",
    avgAmountRange: "₹2,000 – ₹50,000",
    frequency: "Very Common",
    riskLevel: "critical",
    tips: [
      "Government agencies never demand payments via UPI",
      "No legitimate officer will threaten arrest over a phone call",
      "Verify by calling the official helpline of that department",
    ],
  },
  {
    id: "pat-techsupport",
    type: "TECH_SUPPORT",
    title: "Tech Support Refund Scam",
    description:
      "Victims are told a refund is pending but must first pay a 'processing fee' to release it. Often impersonates Amazon, Flipkart, or banks.",
    exampleRemark: "Amazon refund initiation fee",
    avgAmountRange: "₹500 – ₹10,000",
    frequency: "Common",
    riskLevel: "high",
    tips: [
      "Refunds never require you to pay money first",
      "Use the official app to check refund status",
      "Do not install screen-sharing apps on request",
    ],
  },
  {
    id: "pat-lottery",
    type: "LOTTERY",
    title: "Lottery / Prize Scam",
    description:
      "Victims are told they have won a lottery or KBC prize and must pay a 'claim processing fee' to receive the winnings.",
    exampleRemark: "KBC winner processing fee",
    avgAmountRange: "₹1,000 – ₹25,000",
    frequency: "Common",
    riskLevel: "high",
    tips: [
      "You cannot win a lottery you did not enter",
      "KBC never contacts winners via WhatsApp",
      "Never pay to 'claim' a prize",
    ],
  },
  {
    id: "pat-investment",
    type: "INVESTMENT",
    title: "Investment / Crypto Scam",
    description:
      "Fraudsters promise high returns on investments or crypto trades, then demand 'withdrawal fees' when victims try to cash out.",
    exampleRemark: "crypto withdrawal processing charge",
    avgAmountRange: "₹5,000 – ₹1,00,000",
    frequency: "Common",
    riskLevel: "critical",
    tips: [
      "If returns sound too good to be true, they are",
      "Only invest through SEBI-registered platforms",
      "Never join 'investment groups' on Telegram or WhatsApp",
    ],
  },
  {
    id: "pat-job",
    type: "JOB",
    title: "Job Offer Scam",
    description:
      "Fake recruiters demand registration or training fees for jobs that do not exist. Often targets students and job seekers.",
    exampleRemark: "registration fee job placement",
    avgAmountRange: "₹500 – ₹8,000",
    frequency: "Occasional",
    riskLevel: "medium",
    tips: [
      "Legitimate employers never charge applicants",
      "Verify the company on official job portals",
      "Be wary of WhatsApp-only recruiters",
    ],
  },
  {
    id: "pat-emergency",
    type: "EMERGENCY",
    title: "Emergency / Distress Scam",
    description:
      "Scammers impersonate friends or relatives in an emergency (accident, arrest, stranding), demanding urgent money transfers.",
    exampleRemark: "friend accident hospital fee",
    avgAmountRange: "₹2,000 – ₹50,000",
    frequency: "Occasional",
    riskLevel: "high",
    tips: [
      "Always call the person directly to verify",
      "Scammers create urgency to prevent verification",
      "Do not transfer money based on a single message",
    ],
  },
];

/**
 * Fetch fraud pattern cards from Gold table.
 * Falls back to static mock data if Databricks is unavailable.
 */
export async function fetchFraudPatterns(): Promise<FraudPattern[]> {
  const sql = `
    SELECT
      fraud_type,
      COUNT(*) AS occurrence_count,
      AVG(amount_numeric) AS avg_amount,
      MIN(amount_numeric) AS min_amount,
      MAX(amount_numeric) AS max_amount
    FROM gold_transactions
    WHERE is_fraud = true
    GROUP BY fraud_type
    ORDER BY occurrence_count DESC
  `;

  const rows = await executeStatement(sql);
  if (!rows || rows.length === 0) return MOCK_PATTERNS;

  // Merge DB stats into our static pattern definitions
  return MOCK_PATTERNS.map((pattern) => {
    const dbRow = rows.find(
      (r) => r.fraud_type === pattern.type
    );
    if (dbRow) {
      const min = Math.round(parseFloat(dbRow.min_amount));
      const max = Math.round(parseFloat(dbRow.max_amount));
      return {
        ...pattern,
        avgAmountRange: `₹${min.toLocaleString("en-IN")} – ₹${max.toLocaleString("en-IN")}`,
        frequency:
          parseInt(dbRow.occurrence_count) > 2000
            ? "Very Common"
            : parseInt(dbRow.occurrence_count) > 500
              ? "Common"
              : "Occasional",
      };
    }
    return pattern;
  });
}
