export type RiskTier = "HIGH" | "MEDIUM" | "LOW";

export interface AlertRow {
  id: string;
  vpa: string;
  remark: string;
  risk: RiskTier;
  amount: number;
  fraudType: string;
  signals: {
    vpn: boolean;
    newDevice: boolean;
    ipMismatch: boolean;
  };
}

export interface ScamCategory {
  type: string;
  complaints: number;
  lossLakhs: number;
}

export interface HeatmapCell {
  day: string;
  hour: number;
  value: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "bot";
  content: string;
  timestamp: Date;
}

export interface KPIData {
  totalTransactions: number;
  highRisk24h: number;
  highFraudRate: number;
  highRiskDelta: number;
  mediumRisk24h: number;
  medFraudRate: number;
  overrideRate: number;
  confirmedFraud: number;
  estExposureLakhs: number;
  resolutionRate: number;
  avgResolveDays: number;
  resolvedComplaints: number;
  totalComplaints: number;
  openComplaints: number;
  escalatedComplaints: number;
}

export interface StateData {
  name: string;
  fraudRate: number;
  fraudTxns: number;
  fraudVolumeLakhs: number;
  topScam: string;
  complaints: number;
}

export type ComplaintStatus = "OPEN" | "RESOLVED" | "ESCALATED";

export interface Complaint {
  id: string;
  date: string;
  scamType: string;
  amount: number;
  status: ComplaintStatus;
  bank: string;
  state: string;
  daysOpen: number | null;
}

export interface BankResolution {
  bank: string;
  avgDays: number;
  complaints: number;
}

// ── Analytics Gold Table Interfaces ──

export interface GeoHeatmapRow {
  sender_state: string;
  total_txns: number;
  fraud_txns: number;
  fraud_rate_pct: number;
}

export interface ScamTaxonomyRow {
  scam_type: string;
  complaint_count: number;
  avg_loss: number;
  total_loss: number;
}

export interface RiskDistributionRow {
  rule_risk_tier: string;
  txn_count: number;
  fraud_count: number;
  fraud_rate_pct: number;
}

export interface HourlyPatternRow {
  hour_of_day: number;
  total_txns: number;
  fraud_txns: number;
  fraud_rate_pct: number;
}

export interface AlertEffectivenessRow {
  rule_name: string;
  total_alerts: number;
  true_positives: number;
  false_positives: number;
  precision_pct: number;
}

// ── Local Chatbot API Interfaces ──

export interface ChatbotRequest {
  question: string;
  top_k?: number;
  include_analytics?: boolean;
}

export interface ChatbotAPIResponse {
  status: "success" | "error";
  message?: string;
  data?: ChatbotData;
}

export interface Source {
  document_name?: string;
  doc_id?: string;
  page_number?: number;
  chunk_text?: string;
  snippet?: string;
  similarity_score?: number;
  score?: number;
}

export interface ChatbotData {
  answer?: string;
  response?: string;
  sources: Source[];
  similarity_score?: number;
  chunk_text?: string;
  analytics_included?: boolean;
  analytics_summary?: string | null;
  meta?: any;
}
