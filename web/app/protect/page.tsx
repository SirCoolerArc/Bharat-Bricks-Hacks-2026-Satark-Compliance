"use client";

import { useState } from "react";
import Card from "@/components/Card";
import Input from "@/components/Input";
import TextArea from "@/components/TextArea";
import Button from "@/components/Button";
import RiskGauge from "@/components/RiskGauge";
import RiskBadge from "@/components/RiskBadge";
import InfoBanner from "@/components/InfoBanner";
import Skeleton from "@/components/Skeleton";
import { TransactionInput, TransactionScore, RiskLevel } from "@/types";

const DEFAULT_INPUT: TransactionInput = {
  amount: 0,
  senderVpa: "",
  recipientVpa: "",
  remark: "",
  recipientAgeDays: 365,
  recipientFanIn7d: 3,
  isNewDevice: false,
  ipStateMatch: true,
  sessionDurationSec: 120,
  isVpn: false,
};

// Pre-filled demo scenarios for quick testing
const SAMPLE_SCENARIOS: {
  label: string;
  description: string;
  risk: "safe" | "suspicious" | "scam";
  input: TransactionInput;
}[] = [
  {
    label: "Rent Payment",
    description: "Routine monthly rent to a known landlord",
    risk: "safe",
    input: {
      amount: 12000, senderVpa: "rahul42@upi", recipientVpa: "landlord88@oksbi",
      remark: "rent march", recipientAgeDays: 730, recipientFanIn7d: 2,
      isNewDevice: false, ipStateMatch: true, sessionDurationSec: 180, isVpn: false,
    },
  },
  {
    label: "New VPA Store",
    description: "Payment to a recently-created merchant VPA",
    risk: "suspicious",
    input: {
      amount: 4500, senderVpa: "priya21@upi", recipientVpa: "newshop99@paytm",
      remark: "furniture payment advance", recipientAgeDays: 8, recipientFanIn7d: 18,
      isNewDevice: false, ipStateMatch: true, sessionDurationSec: 90, isVpn: false,
    },
  },
  {
    label: "KYC Fraud",
    description: "Fake KYC penalty with urgency keywords",
    risk: "scam",
    input: {
      amount: 2500, senderVpa: "amit33@upi", recipientVpa: "kychelp007@ybl",
      remark: "electricity KYC penalty avoid disconnection urgent",
      recipientAgeDays: 5, recipientFanIn7d: 45, isNewDevice: true,
      ipStateMatch: false, sessionDurationSec: 25, isVpn: true,
    },
  },
  {
    label: "Impersonation",
    description: "CBI officer demanding settlement fee",
    risk: "scam",
    input: {
      amount: 35000, senderVpa: "deepa56@upi", recipientVpa: "settle444@okaxis",
      remark: "CBI officer case settlement fee urgent",
      recipientAgeDays: 3, recipientFanIn7d: 62, isNewDevice: true,
      ipStateMatch: false, sessionDurationSec: 18, isVpn: false,
    },
  },
];

const SCENARIO_STYLES: Record<string, { border: string; dot: string; emoji: string }> = {
  safe:       { border: "border-l-[3px] border-l-[var(--risk-low)]",      dot: "bg-risk-low",      emoji: "🟢" },
  suspicious: { border: "border-l-[3px] border-l-[var(--risk-medium)]",   dot: "bg-risk-medium",   emoji: "🟡" },
  scam:       { border: "border-l-[3px] border-l-[var(--risk-high)]",     dot: "bg-risk-high",     emoji: "🔴" },
};

const RISK_RECOMMENDATIONS: Record<RiskLevel, { title: string; color: string; message: string }> = {
  low: {
    title: "Transaction appears safe",
    color: "bg-green-50",
    message: "This transaction does not show any significant fraud signals. Proceed with normal caution.",
  },
  medium: {
    title: "Proceed with caution",
    color: "bg-amber-50",
    message: "Some risk signals were detected. Verify the recipient before completing the transaction. If unsure, contact your bank.",
  },
  high: {
    title: "High risk — verify before proceeding",
    color: "bg-red-50",
    message: "Multiple fraud indicators are present. We strongly recommend verifying the recipient independently and checking the remark for scam patterns.",
  },
  critical: {
    title: "Do not proceed — likely fraud",
    color: "bg-red-100",
    message: "This transaction matches known fraud patterns with high confidence. Do NOT complete this payment. If you've already paid, report immediately to your bank and at cybercrime.gov.in.",
  },
};

export default function ProtectPage() {
  const [input, setInput] = useState<TransactionInput>(DEFAULT_INPUT);
  const [result, setResult] = useState<TransactionScore | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const update = (field: keyof TransactionInput, value: string | number | boolean) =>
    setInput((prev) => ({ ...prev, [field]: value }));

  function loadSample(scenario: typeof SAMPLE_SCENARIOS[0]) {
    setInput(scenario.input);
    setResult(null);
    setError(null);
    handleScore(scenario.input);
  }

  async function handleScore(customInput?: TransactionInput) {
    setLoading(true);
    setError(null);
    setResult(null);

    const payload = customInput || input;

    try {
      const res = await fetch("/api/score-transaction", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`Scoring failed (${res.status})`);

      const data: TransactionScore = await res.json();
      setResult(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Something went wrong";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  const recommendation = result ? RISK_RECOMMENDATIONS[result.riskLevel] : null;
  const isHighRisk = result && (result.riskLevel === "high" || result.riskLevel === "critical");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-ink">Check a Transaction</h1>
        <p className="text-sm text-ink-muted mt-1">
          Enter transaction details below. We assess the fraud risk in real time using ML scoring and remark analysis.
        </p>
      </div>

      {/* Sample Buttons */}
      <div>
        <p className="text-xs text-ink-faint mb-2">Quick demo — try a sample scenario:</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {SAMPLE_SCENARIOS.map((s, i) => {
            const style = SCENARIO_STYLES[s.risk];
            return (
              <button
                key={i}
                onClick={() => loadSample(s)}
                className={`text-left px-3 py-2.5 rounded-md bg-white hover:bg-surface-100 transition-colors ${style.border}`}
                style={{ border: "0.5px solid var(--border-color)", borderLeft: undefined }}
              >
                <div className="flex items-center gap-1.5 mb-0.5">
                  <span className={`w-2 h-2 rounded-full ${style.dot} flex-shrink-0`} />
                  <span className="text-xs font-semibold text-ink">{s.label}</span>
                </div>
                <p className="text-[11px] text-ink-faint leading-tight">{s.description}</p>
              </button>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Input Form */}
        <Card>
          <div className="space-y-4">
            <Input
              label="Amount (₹)"
              type="number"
              placeholder="e.g. 5000"
              value={input.amount || ""}
              onChange={(e) => update("amount", parseFloat(e.target.value) || 0)}
            />

            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Sender VPA"
                placeholder="sender@upi"
                value={input.senderVpa}
                onChange={(e) => update("senderVpa", e.target.value)}
              />
              <Input
                label="Recipient VPA"
                placeholder="recipient@upi"
                value={input.recipientVpa}
                onChange={(e) => update("recipientVpa", e.target.value)}
              />
            </div>

            <TextArea
              label="UPI Remark"
              placeholder="e.g. electricity KYC penalty avoid disconnection"
              helperText="The remark or message attached to the payment"
              value={input.remark}
              onChange={(e) => update("remark", e.target.value)}
            />

            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Recipient Age (days)"
                type="number"
                value={input.recipientAgeDays}
                onChange={(e) => update("recipientAgeDays", parseInt(e.target.value) || 0)}
                helperText="How old is the recipient VPA"
              />
              <Input
                label="Inbound Transfers (7d)"
                type="number"
                value={input.recipientFanIn7d}
                onChange={(e) => update("recipientFanIn7d", parseInt(e.target.value) || 0)}
                helperText="Unique senders in last 7 days"
              />
            </div>

            <Input
              label="Session Duration (sec)"
              type="number"
              value={input.sessionDurationSec}
              onChange={(e) => update("sessionDurationSec", parseInt(e.target.value) || 0)}
            />

            <div className="flex flex-wrap gap-4 pt-1">
              <label className="flex items-center gap-2 text-sm text-ink cursor-pointer">
                <input type="checkbox" checked={input.isNewDevice} onChange={(e) => update("isNewDevice", e.target.checked)} className="rounded" />
                New device
              </label>
              <label className="flex items-center gap-2 text-sm text-ink cursor-pointer">
                <input type="checkbox" checked={!input.ipStateMatch} onChange={(e) => update("ipStateMatch", !e.target.checked)} className="rounded" />
                IP mismatch
              </label>
              <label className="flex items-center gap-2 text-sm text-ink cursor-pointer">
                <input type="checkbox" checked={input.isVpn} onChange={(e) => update("isVpn", e.target.checked)} className="rounded" />
                VPN detected
              </label>
            </div>

            <Button onClick={() => handleScore()} loading={loading} className="w-full mt-2">
              Assess Risk
            </Button>
          </div>
        </Card>

        {/* Results Panel */}
        <div className="space-y-4">
          {error && (
            <Card>
              <div className="flex items-start gap-2">
                <span className="text-risk-high text-lg">⚠</span>
                <div>
                  <p className="text-sm font-medium text-risk-high">Scoring Error</p>
                  <p className="text-sm text-ink-muted mt-1">{error}</p>
                </div>
              </div>
            </Card>
          )}

          {/* Loading skeleton */}
          {loading && (
            <Card className="flex flex-col items-center py-8">
              <div className="w-[180px] h-[110px] rounded-lg bg-surface-200 animate-pulse mb-4" />
              <Skeleton className="w-24" />
              <Skeleton className="w-40 mt-2" />
            </Card>
          )}

          {result && !loading && (
            <>
              {/* Score gauge */}
              <Card className="flex flex-col items-center py-6">
                <RiskGauge score={result.riskScore} />
                <div className="mt-3">
                  <RiskBadge level={result.riskLevel} />
                </div>
                <p className="text-xs text-ink-faint mt-2">
                  Scored at {new Date(result.timestamp).toLocaleTimeString()}
                </p>
              </Card>

              {/* Recommendation */}
              {recommendation && (
                <div className={`${recommendation.color} rounded-lg p-4`} style={{ border: "0.5px solid var(--border-color)" }}>
                  <p className="text-sm font-semibold text-ink mb-1">{recommendation.title}</p>
                  <p className="text-sm text-ink-muted">{recommendation.message}</p>
                </div>
              )}

              {/* HIGH RISK: Urgent guidance */}
              {isHighRisk && (
                <InfoBanner variant="danger" title="Immediate Action Required">
                  <ul className="space-y-1.5 mt-1">
                    <li className="flex items-start gap-2 text-sm">
                      <span className="font-semibold text-ink flex-shrink-0">1.</span>
                      <span><strong className="text-ink">Do NOT complete</strong> this transaction — close the payment screen.</span>
                    </li>
                    <li className="flex items-start gap-2 text-sm">
                      <span className="font-semibold text-ink flex-shrink-0">2.</span>
                      <span>If already paid, call your bank&apos;s fraud helpline <strong className="text-ink">within 3 days</strong> for zero liability.</span>
                    </li>
                    <li className="flex items-start gap-2 text-sm">
                      <span className="font-semibold text-ink flex-shrink-0">3.</span>
                      <span>Call the <strong className="text-ink">National Cyber Crime Helpline: 1930</strong> (24×7, toll-free).</span>
                    </li>
                    <li className="flex items-start gap-2 text-sm">
                      <span className="font-semibold text-ink flex-shrink-0">4.</span>
                      <span>File online at <strong className="text-ink">cybercrime.gov.in</strong> and preserve all evidence.</span>
                    </li>
                  </ul>
                </InfoBanner>
              )}

              {/* Remark classification */}
              {result.remarkCategory !== "LEGITIMATE" && (
                <Card padding="sm">
                  <p className="text-xs font-medium text-ink-muted mb-1">Remark Classification</p>
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-50 text-risk-high">
                      {result.remarkCategory}
                    </span>
                    <span className="text-sm text-ink">
                      pattern detected
                      <span className="text-ink-faint"> — {Math.round(result.remarkConfidence * 100)}% confidence</span>
                    </span>
                  </div>
                </Card>
              )}

              {/* Risk flags */}
              {result.flags.length > 0 && (
                <Card padding="sm">
                  <p className="text-xs font-medium text-ink-muted mb-2">Risk Flags ({result.flags.length})</p>
                  <ul className="space-y-2">
                    {result.flags.map((flag, i) => (
                      <li key={i} className="flex items-start gap-2.5 text-sm text-ink">
                        <span className="w-5 h-5 rounded-full bg-red-50 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-risk-high text-[10px]">⚑</span>
                        </span>
                        <span>{flag}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              )}

              {/* Legitimate result */}
              {result.remarkCategory === "LEGITIMATE" && result.flags.length === 0 && (
                <Card padding="sm">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-green-50 flex items-center justify-center flex-shrink-0">
                      <span className="text-risk-low text-sm">✓</span>
                    </span>
                    <p className="text-sm text-ink">No fraud indicators detected. Remark appears to be a normal transaction.</p>
                  </div>
                </Card>
              )}
            </>
          )}

          {!result && !error && !loading && (
            <Card className="flex flex-col items-center justify-center py-16">
              <div className="text-center">
                <p className="text-4xl mb-3">🛡️</p>
                <p className="text-sm text-ink-muted">
                  Enter transaction details and click &quot;Assess Risk&quot;
                </p>
                <p className="text-xs text-ink-faint mt-1">
                  or use a sample scenario above for a quick demo
                </p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
