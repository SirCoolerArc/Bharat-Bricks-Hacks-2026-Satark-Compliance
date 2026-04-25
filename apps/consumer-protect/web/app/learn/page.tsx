"use client";

import { useState } from "react";
import Card from "@/components/Card";
import TextArea from "@/components/TextArea";
import Button from "@/components/Button";
import RiskBadge from "@/components/RiskBadge";
import ChatPanel from "@/components/ChatPanel";
import Skeleton from "@/components/Skeleton";
import { FraudPattern, MessageAnalysisResult, RiskLevel } from "@/types";

const MOCK_PATTERNS: FraudPattern[] = [
  {
    id: "pat-kyc", type: "KYC", title: "KYC Update Scam",
    description: "Fraudsters impersonate utility companies or banks, demanding a 'KYC verification fee' to prevent disconnection or account freeze.",
    exampleRemark: "electricity KYC penalty avoid disconnection",
    avgAmountRange: "₹500 – ₹5,000", frequency: "Very Common", riskLevel: "high",
    tips: ["No bank or utility asks for KYC fees via UPI", "Verify through the official app or branch", "Do not click links in SMS or WhatsApp messages"],
  },
  {
    id: "pat-impersonation", type: "IMPERSONATION", title: "Authority Impersonation",
    description: "Scammers pose as CBI, income tax, or police officials, threatening arrest unless an immediate 'settlement fee' is paid.",
    exampleRemark: "CBI officer case settlement fee",
    avgAmountRange: "₹2,000 – ₹50,000", frequency: "Very Common", riskLevel: "critical",
    tips: ["Government agencies never demand payments via UPI", "No legitimate officer will threaten arrest over a phone call", "Verify by calling the official helpline"],
  },
  {
    id: "pat-techsupport", type: "TECH_SUPPORT", title: "Tech Support Refund Scam",
    description: "Victims are told a refund is pending but must first pay a 'processing fee' to release it.",
    exampleRemark: "Amazon refund initiation fee",
    avgAmountRange: "₹500 – ₹10,000", frequency: "Common", riskLevel: "high",
    tips: ["Refunds never require you to pay money first", "Use the official app to check refund status", "Do not install screen-sharing apps on request"],
  },
  {
    id: "pat-lottery", type: "LOTTERY", title: "Lottery / Prize Scam",
    description: "Victims are told they have won a lottery and must pay a 'claim processing fee'.",
    exampleRemark: "KBC winner processing fee",
    avgAmountRange: "₹1,000 – ₹25,000", frequency: "Common", riskLevel: "high",
    tips: ["You cannot win a lottery you did not enter", "KBC never contacts winners via WhatsApp", "Never pay to 'claim' a prize"],
  },
  {
    id: "pat-investment", type: "INVESTMENT", title: "Investment / Crypto Scam",
    description: "Fraudsters promise high returns then demand 'withdrawal fees' when victims try to cash out.",
    exampleRemark: "crypto withdrawal processing charge",
    avgAmountRange: "₹5,000 – ₹1,00,000", frequency: "Common", riskLevel: "critical",
    tips: ["If returns sound too good to be true, they are", "Only invest through SEBI-registered platforms", "Never join 'investment groups' on Telegram"],
  },
  {
    id: "pat-job", type: "JOB", title: "Job Offer Scam",
    description: "Fake recruiters demand registration or training fees for non-existent jobs.",
    exampleRemark: "registration fee job placement",
    avgAmountRange: "₹500 – ₹8,000", frequency: "Occasional", riskLevel: "medium",
    tips: ["Legitimate employers never charge applicants", "Verify the company on official job portals", "Be wary of WhatsApp-only recruiters"],
  },
  {
    id: "pat-emergency", type: "EMERGENCY", title: "Emergency / Distress Scam",
    description: "Scammers impersonate friends or relatives in an emergency, demanding urgent transfers.",
    exampleRemark: "friend accident hospital fee",
    avgAmountRange: "₹2,000 – ₹50,000", frequency: "Occasional", riskLevel: "high",
    tips: ["Always call the person directly to verify", "Scammers create urgency to prevent verification", "Do not transfer money based on a single message"],
  },
];

const SAMPLE_MESSAGES = [
  "electricity KYC penalty avoid disconnection urgent",
  "KBC winner processing fee advance payment",
  "CBI officer case settlement fee",
  "rent march payment",
];

const CHAT_QUICK_CHIPS = [
  "How do I report UPI fraud?",
  "What are my RBI refund rights?",
  "Is this a KYC scam?",
  "How to stay safe on UPI?",
  "Investment scam red flags",
];

const KEYWORD_COLORS: Record<RiskLevel, { bg: string; text: string }> = {
  low:      { bg: "bg-green-50",  text: "text-risk-low" },
  medium:   { bg: "bg-amber-50",  text: "text-risk-medium" },
  high:     { bg: "bg-red-50",    text: "text-risk-high" },
  critical: { bg: "bg-red-100",   text: "text-risk-critical" },
};

export default function LearnPage() {
  const [patterns] = useState<FraudPattern[]>(MOCK_PATTERNS);
  const [message, setMessage] = useState("");
  const [analysis, setAnalysis] = useState<MessageAnalysisResult | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [expandedPattern, setExpandedPattern] = useState<string | null>(null);

  async function handleAnalyze(text?: string) {
    const toAnalyze = text || message;
    if (!toAnalyze.trim()) return;
    if (text) setMessage(text);
    setAnalyzing(true);
    setAnalysis(null);

    try {
      const res = await fetch("/api/analyze-message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: toAnalyze }),
      });
      const data: MessageAnalysisResult = await res.json();
      setAnalysis(data);
    } catch {
      setAnalysis(null);
    } finally {
      setAnalyzing(false);
    }
  }

  const keywordStyle = analysis ? KEYWORD_COLORS[analysis.riskLevel] : KEYWORD_COLORS.low;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-ink">Learn About Fraud Patterns</h1>
        <p className="text-sm text-ink-muted mt-1">
          Understand common UPI scam tactics, analyze suspicious messages, and get safety guidance from our AI assistant.
        </p>
      </div>

      {/* Two-column: Analyzer + Chatbot */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4" style={{ alignItems: "start" }}>
        {/* Message Analyzer */}
        <Card className="md:min-h-[420px] flex flex-col">
          <h2 className="text-base font-semibold text-ink mb-2">
            Suspicious Message Analyzer
          </h2>
          <p className="text-xs text-ink-muted mb-3">
            Paste a suspicious UPI remark or message to check if it matches a known scam.
          </p>

          {/* Sample buttons */}
          <div className="flex flex-wrap gap-1.5 mb-3">
            {SAMPLE_MESSAGES.map((msg, i) => (
              <button
                key={i}
                onClick={() => handleAnalyze(msg)}
                className="px-2 py-1 rounded text-xs bg-surface-100 text-ink-faint hover:bg-surface-200 hover:text-ink transition-colors truncate max-w-[200px]"
                style={{ border: "0.5px solid var(--border-color)" }}
              >
                &quot;{msg.length > 30 ? msg.slice(0, 28) + "…" : msg}&quot;
              </button>
            ))}
          </div>

          <div className="space-y-3">
            <TextArea
              placeholder="Paste a suspicious message here…"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={3}
            />
            <Button onClick={() => handleAnalyze()} loading={analyzing} size="sm">
              Analyze Message
            </Button>
          </div>

          {/* Loading state */}
          {analyzing && (
            <div className="mt-4 p-4 rounded-md bg-surface-50" style={{ border: "0.5px solid var(--border-color)" }}>
              <Skeleton lines={3} />
            </div>
          )}

          {analysis && !analyzing && (
            <div
              className="mt-4 p-4 rounded-md space-y-3"
              style={{
                border: "0.5px solid var(--border-color)",
                backgroundColor:
                  analysis.riskLevel === "low" ? "var(--surface-50)" :
                  analysis.riskLevel === "critical" ? "#FEF2F2" : "#FFFBEB",
              }}
            >
              <div className="flex items-center gap-2">
                <RiskBadge level={analysis.riskLevel} />
                <span className="text-sm font-medium text-ink">{analysis.category}</span>
                <span className="text-xs text-ink-faint">
                  ({Math.round(analysis.confidence * 100)}% confidence)
                </span>
              </div>

              <p className="text-sm text-ink leading-relaxed">{analysis.advice}</p>

              {/* Highlighted keywords */}
              {analysis.matchedKeywords.length > 0 && (
                <div>
                  <p className="text-xs text-ink-faint mb-1.5">Matched suspicious tokens:</p>
                  <div className="flex flex-wrap gap-1.5">
                    {analysis.matchedKeywords.map((kw) => (
                      <span
                        key={kw}
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${keywordStyle.bg} ${keywordStyle.text}`}
                      >
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </Card>

        {/* Chatbot */}
        <div className="md:min-h-[420px]">
          <ChatPanel
            title="Ask about UPI Safety"
            placeholder="How do I report UPI fraud?"
            welcomeMessage="Hi! I can answer questions about UPI safety, RBI guidelines, and how to handle fraud. Try asking about reporting fraud, refund timelines, or specific scam types."
            quickChips={CHAT_QUICK_CHIPS}
          />
        </div>
      </div>

      {/* Pattern Cards */}
      <div>
        <h2 className="section-heading">Common Fraud Types</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {patterns.map((pattern) => {
            const isExpanded = expandedPattern === pattern.id;
            return (
              <Card key={pattern.id} padding="md">
                <div className="space-y-3">
                  <div
                    className="flex items-start justify-between cursor-pointer"
                    onClick={() => setExpandedPattern(isExpanded ? null : pattern.id)}
                  >
                    <div>
                      <h3 className="text-base font-semibold text-ink">{pattern.title}</h3>
                      <p className="text-xs text-ink-faint">{pattern.frequency} · {pattern.avgAmountRange}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <RiskBadge level={pattern.riskLevel} />
                      <span className="text-ink-faint text-xs">{isExpanded ? "▲" : "▼"}</span>
                    </div>
                  </div>

                  <p className="text-sm text-ink-muted">{pattern.description}</p>

                  {isExpanded && (
                    <>
                      <div className="p-2 rounded bg-surface-50">
                        <p className="text-xs text-ink-faint mb-1">Example remark:</p>
                        <p className="text-sm text-ink font-mono">&quot;{pattern.exampleRemark}&quot;</p>
                      </div>

                      <div>
                        <p className="text-xs font-medium text-ink-muted mb-1">How to stay safe:</p>
                        <ul className="space-y-1">
                          {pattern.tips.map((tip, i) => (
                            <li key={i} className="flex items-start gap-2 text-xs text-ink-muted">
                              <span className="text-risk-low mt-0.5">✓</span>
                              {tip}
                            </li>
                          ))}
                        </ul>
                      </div>

                      <button
                        onClick={() => handleAnalyze(pattern.exampleRemark)}
                        className="text-xs text-accent hover:underline"
                      >
                        Analyze this remark →
                      </button>
                    </>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
}
