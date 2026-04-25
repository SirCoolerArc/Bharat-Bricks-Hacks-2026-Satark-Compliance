// ─────────────────────────────────────────────
// SATARK shared types — all data contracts live here
// ─────────────────────────────────────────────

/** Risk severity levels used across the app */
export type RiskLevel = "low" | "medium" | "high" | "critical";

// ── Transaction Scoring ──────────────────────

export interface TransactionInput {
  amount: number;
  senderVpa: string;
  recipientVpa: string;
  remark: string;
  recipientAgeDays: number;
  recipientFanIn7d: number;
  isNewDevice: boolean;
  ipStateMatch: boolean;
  sessionDurationSec: number;
  isVpn: boolean;
}

export interface TransactionScore {
  riskScore: number; // 0–100
  riskLevel: RiskLevel;
  remarkCategory: string;
  remarkConfidence: number;
  flags: string[];
  timestamp: string;
}

// ── Message / Remark Analysis ────────────────

export interface MessageAnalysisInput {
  message: string;
}

export interface MessageAnalysisResult {
  category: string; // LEGITIMATE | KYC | LOTTERY | etc.
  confidence: number; // 0–1
  riskLevel: RiskLevel;
  matchedKeywords: string[];
  advice: string;
}

// ── Fraud Pattern Cards ──────────────────────

export interface FraudPattern {
  id: string;
  type: string; // KYC, LOTTERY, IMPERSONATION, etc.
  title: string;
  description: string;
  exampleRemark: string;
  avgAmountRange: string;
  frequency: string; // "Very Common", "Common", "Occasional"
  riskLevel: RiskLevel;
  tips: string[];
}

// ── Chatbot ──────────────────────────────────

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  sources?: string[]; // RAG source document references
}

// ── Complaints ───────────────────────────────

export interface ComplaintRecord {
  complaintId: string;
  txnId: string;
  senderVpaHash: string;
  complaintTs: string;
  scamType: string;
  amountBucket: string;
  complaintStatus: "OPEN" | "ESCALATED" | "RESOLVED";
  resolutionDays: number | null;
  bankId: string;
}

export interface ComplaintInsert {
  txnId: string;
  senderVpaHash: string;
  scamType: string;
  amountBucket: string;
  bankId: string;
  description: string;
}

// ── Dashboard KPIs ───────────────────────────

export interface KpiSummary {
  totalTransactions: number;
  fraudCount: number;
  fraudRate: number;
  avgFraudAmount: number;
  topScamType: string;
  complaintsOpen: number;
  complaintsResolved: number;
  avgResolutionDays: number;
}

// ── Alert Feed ───────────────────────────────

export interface AlertItem {
  id: string;
  timestamp: string;
  type: string;
  severity: RiskLevel;
  message: string;
  vpaMasked: string;
  amount: number;
}
