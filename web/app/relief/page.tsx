"use client";

import { useState } from "react";
import Card from "@/components/Card";
import Input from "@/components/Input";
import TextArea from "@/components/TextArea";
import Button from "@/components/Button";
import ChatPanel from "@/components/ChatPanel";
import InfoBanner from "@/components/InfoBanner";

const SCAM_TYPES = [
  "KYC", "IMPERSONATION", "TECH_SUPPORT", "LOTTERY",
  "INVESTMENT", "JOB", "EMERGENCY", "OTHER",
];

const BANKS = [
  "SBI", "HDFC Bank", "ICICI Bank", "Axis Bank",
  "Kotak Mahindra", "PNB", "Bank of Baroda", "Canara Bank",
  "Union Bank", "IndusInd Bank", "Other",
];

const BANK_HELPLINES: Record<string, string> = {
  "SBI": "1800-111-109",
  "HDFC Bank": "1800-120-1243",
  "ICICI Bank": "1800-120-2020",
  "Axis Bank": "1860-419-5555",
  "Kotak Mahindra": "1800-209-0000",
  "PNB": "1800-180-2222",
  "Bank of Baroda": "1800-5700",
  "Canara Bank": "1800-425-0018",
  "Union Bank": "1800-222-244",
  "IndusInd Bank": "1860-267-7777",
};

interface FormData {
  victimName: string;
  scamType: string;
  bankName: string;
  amount: string;
  transactionDate: string;
  recipientVpa: string;
  description: string;
}

const INITIAL_FORM: FormData = {
  victimName: "",
  scamType: "",
  bankName: "",
  amount: "",
  transactionDate: "",
  recipientVpa: "",
  description: "",
};

const STEPS = [
  { num: 1, label: "Details" },
  { num: 2, label: "Describe" },
  { num: 3, label: "Review" },
  { num: 4, label: "Next Steps" },
];

export default function ReliefPage() {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState<FormData>(INITIAL_FORM);
  const [generatedText, setGeneratedText] = useState<string | null>(null);
  const [complaintId, setComplaintId] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const update = (field: keyof FormData, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const canProceedStep1 = form.victimName && form.scamType && form.bankName && form.amount;
  const canProceedStep2 = form.description.trim().length > 10;

  function generateComplaintText() {
    const scamLabel = form.scamType.toLowerCase().replace(/_/g, " ");
    const text = `Subject: ACTION REQUIRED: UPI Fraud Complaint — ${form.scamType} Scam
To: The Nodal Officer,
${form.bankName}

Respected Sir/Madam,

I, ${form.victimName}, wish to report a UPI fraud that occurred on ${form.transactionDate || "[Date]"}.

I was a victim of a ${scamLabel} scam and lost ₹${parseFloat(form.amount || "0").toLocaleString("en-IN")} in the fraudulent transaction.${form.recipientVpa ? ` The payment was sent to the VPA: ${form.recipientVpa}.` : ""}

**Details of the incident:**
${form.description}

**I request you to immediately:**
1. Freeze the recipient's account/VPA to prevent further fraud
2. Initiate the refund process as per RBI guidelines on Limiting Liability of Customers in Unauthorised Electronic Banking Transactions (RBI/2017-18/15)
3. Report this incident to the Cyber Crime Cell and NPCI
4. Provide me with a written acknowledgment of this complaint within 24 hours

As per the above RBI circular:
• Reporting within 3 working days means the customer bears zero liability
• The bank must provisionally credit the disputed amount within 10 working days

I will also file a complaint on the National Cyber Crime Portal (cybercrime.gov.in) and the NPCI Dispute Redressal Mechanism.

Reference ID: ${complaintId || "SATARK-" + Date.now().toString(36).toUpperCase()}

I request your urgent attention to this matter.

Yours sincerely,
${form.victimName}
Date: ${new Date().toLocaleDateString("en-IN")}`;

    setGeneratedText(text);
    if (!complaintId) {
      setComplaintId(`SATARK-${Date.now().toString(36).toUpperCase()}`);
    }
    setStep(3);
  }

  async function handleCopy() {
    if (!generatedText) return;
    await navigator.clipboard.writeText(generatedText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleReset() {
    setStep(1);
    setForm(INITIAL_FORM);
    setGeneratedText(null);
    setComplaintId(null);
    setCopied(false);
  }

  const helpline = BANK_HELPLINES[form.bankName];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-ink">Post-Fraud Relief</h1>
        <p className="text-sm text-ink-muted mt-1">
          If you have been a victim of UPI fraud, we will help you file a complaint and understand your rights under RBI guidelines.
        </p>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center">
        {STEPS.map((s, i) => (
          <div key={s.num} className="flex items-center">
            <div className="flex flex-col items-center gap-1.5 relative w-16">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors z-10 ${
                  step > s.num ? "bg-risk-low text-white shadow-sm" :
                  step === s.num ? "bg-accent text-white shadow-md ring-2 ring-accent/20 ring-offset-2" :
                  "bg-surface-200 text-ink-muted"
                }`}
              >
                {step > s.num ? "✓" : s.num}
              </div>
              <span className={`text-[11px] font-medium absolute -bottom-5 w-20 text-center ${
                step >= s.num ? "text-ink" : "text-ink-faint"
              }`}>
                {s.label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div
                className={`w-12 h-[2px] -ml-2 -mr-2 z-0 rounded-full transition-colors ${
                  step > s.num ? "bg-risk-low" : "bg-surface-200"
                }`}
              />
            )}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6">
        {/* Left: Form area (2 cols) */}
        <div className="md:col-span-2 space-y-4">

          {/* Step 1: Basic Details */}
          {step === 1 && (
            <>
              <InfoBanner variant="warning" title="Time is Critical" className="mb-2">
                Under RBI guidelines, if you report unauthorized transactions to your bank within <strong className="text-ink">3 working days</strong>, you have <strong className="text-ink">zero liability</strong> for the loss. <span className="underline decoration-ink-faint underline-offset-2">Do not delay.</span>
              </InfoBanner>

              <Card>
                <h2 className="text-base font-semibold text-ink mb-4">Incident Details</h2>
                <div className="space-y-4">
                  <Input
                    label="Your Name"
                    placeholder="Enter your full name"
                    value={form.victimName}
                    onChange={(e) => update("victimName", e.target.value)}
                  />

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-sm font-medium text-ink block mb-1">Scam Type</label>
                      <select
                        className="w-full px-3 py-2 rounded-md text-sm bg-white text-ink focus:outline-none focus:ring-2 focus:ring-accent/30 transition-shadow"
                        style={{ border: "0.5px solid var(--border-color)" }}
                        value={form.scamType}
                        onChange={(e) => update("scamType", e.target.value)}
                      >
                        <option value="">Select type</option>
                        {SCAM_TYPES.map((t) => (
                          <option key={t} value={t}>{t.replace(/_/g, " ")}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="text-sm font-medium text-ink block mb-1">Your Bank</label>
                      <select
                        className="w-full px-3 py-2 rounded-md text-sm bg-white text-ink focus:outline-none focus:ring-2 focus:ring-accent/30 transition-shadow"
                        style={{ border: "0.5px solid var(--border-color)" }}
                        value={form.bankName}
                        onChange={(e) => update("bankName", e.target.value)}
                      >
                        <option value="">Select bank</option>
                        {BANKS.map((b) => (
                          <option key={b} value={b}>{b}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <Input
                      label="Amount Lost (₹)"
                      type="number"
                      placeholder="e.g. 5000"
                      value={form.amount}
                      onChange={(e) => update("amount", e.target.value)}
                    />
                    <Input
                      label="Date of Transaction"
                      type="date"
                      value={form.transactionDate}
                      onChange={(e) => update("transactionDate", e.target.value)}
                    />
                  </div>

                  <Input
                    label="Recipient VPA (if known)"
                    placeholder="e.g. scammer123@upi"
                    value={form.recipientVpa}
                    onChange={(e) => update("recipientVpa", e.target.value)}
                    helperText="This helps the bank freeze the account faster"
                  />

                  <Button
                    onClick={() => setStep(2)}
                    className="w-full"
                    disabled={!canProceedStep1}
                  >
                    Continue
                  </Button>
                </div>
              </Card>
            </>
          )}

          {/* Step 2: Description */}
          {step === 2 && (
            <Card>
              <h2 className="text-base font-semibold text-ink mb-4">Describe the Incident</h2>
              <div className="space-y-4">
                <TextArea
                  label="What happened?"
                  placeholder="Describe in detail: How were you contacted? What did the scammer say? How was the payment made? Include any phone numbers, names, or VPAs the scammer used."
                  helperText="Be as specific as possible. This will be included in your complaint letter."
                  value={form.description}
                  onChange={(e) => update("description", e.target.value)}
                  rows={8}
                />

                <div className="flex gap-3">
                  <Button variant="secondary" onClick={() => setStep(1)}>
                    Back
                  </Button>
                  <Button onClick={generateComplaintText} className="flex-1" disabled={!canProceedStep2}>
                    Generate Complaint Letter
                  </Button>
                </div>
              </div>
            </Card>
          )}

          {/* Step 3: Generated Complaint */}
          {step === 3 && generatedText && (
            <>
              {complaintId && (
                <Card padding="sm">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-ink">
                      Reference: <span className="font-mono font-semibold">{complaintId}</span>
                    </p>
                    <span className="text-xs text-ink-faint">Save this ID</span>
                  </div>
                </Card>
              )}

              <Card>
                <div className="flex items-center justify-between mb-3 border-b border-[var(--border-color)] pb-3">
                  <div>
                    <h2 className="text-base font-semibold text-ink">Your Complaint Letter</h2>
                    <p className="text-xs text-ink-muted mt-0.5">Email this to your bank&apos;s Nodal Officer immediately.</p>
                  </div>
                  <Button variant="secondary" size="sm" onClick={handleCopy} className="flex bg-surface-50">
                    <span className="mr-1.5">{copied ? "✓" : "📋"}</span>
                    {copied ? "Copied" : "Copy text"}
                  </Button>
                </div>
                
                <div className="bg-surface-50 p-4 rounded-md border border-[var(--border-color)] max-h-[400px] overflow-y-auto">
                  <pre className="whitespace-pre-wrap text-[13px] text-ink font-sans leading-relaxed selection:bg-accent-light">
                    {generatedText.split('\n').map((line, i) => {
                      if (line.startsWith('**') && line.endsWith('**')) {
                        return <strong key={i} className="block mt-4 mb-1">{line.replace(/\*\*/g, '')}</strong>;
                      }
                      return <span key={i} className="block min-h-[1em]">{line}</span>;
                    })}
                  </pre>
                </div>

                <div className="flex gap-3 mt-4">
                  <Button variant="ghost" onClick={() => setStep(2)}>
                    ← Edit Description
                  </Button>
                  <Button onClick={() => setStep(4)} className="flex-1">
                    See Next Steps →
                  </Button>
                </div>
              </Card>
            </>
          )}

          {/* Step 4: Next Steps */}
          {step === 4 && (
            <div className="space-y-4">
              {helpline && (
                <div className="bg-risk-high text-white rounded-lg p-4 flex items-center justify-between shadow-sm">
                  <div>
                    <p className="text-xs font-medium opacity-90 mb-0.5 uppercase tracking-wider">{form.bankName} Fraud Helpline</p>
                    <p className="text-2xl font-bold tracking-tight">{helpline}</p>
                  </div>
                  <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center text-xl">
                    📞
                  </div>
                </div>
              )}

              <Card>
                <h2 className="text-base font-semibold text-ink mb-1">Immediate Action Plan</h2>
                <p className="text-xs text-ink-muted mb-4 pb-3 border-b border-[var(--border-color)]">Complete these steps as soon as possible to secure your account and initiate the refund process.</p>
                
                <div className="space-y-5">
                  <TimelineStep
                    number={1}
                    title="Call your bank NOW"
                    description={`Call ${form.bankName || "your bank"}'s fraud helpline. Request an immediate block on the recipient VPA and your account if necessary. Ask for a complaint reference number.`}
                    urgent
                  />
                  <TimelineStep
                    number={2}
                    title="File on Cyber Crime Portal"
                    description="Go to cybercrime.gov.in and file a complaint under 'Financial Fraud'. You will receive an acknowledgment number — save it."
                    link={{ label: "Open cybercrime.gov.in", href: "https://cybercrime.gov.in" }}
                  />
                  <TimelineStep
                    number={3}
                    title="Report to NPCI"
                    description="File a dispute on the NPCI portal. Select 'Unauthorized Transaction' and provide your UPI transaction ID."
                    link={{ label: "Open NPCI Dispute Portal", href: "https://www.npci.org.in/what-we-do/upi/dispute-redressal-mechanism" }}
                  />
                  <TimelineStep
                    number={4}
                    title="Send the complaint letter"
                    description={`Email the generated complaint letter to ${form.bankName || "your bank"}'s nodal officer, or visit your home branch physically to submit it.`}
                  />
                  <TimelineStep
                    number={5}
                    title="Preserve all evidence"
                    description="Take screenshots of the transaction, any WhatsApp/SMS chat messages, call logs, and the scammer's VPA or phone number. Do not delete anything."
                  />
                </div>
              </Card>

              <div className="flex gap-3 pt-2">
                <Button variant="secondary" onClick={() => setStep(3)}>
                  Back to Letter
                </Button>
                <Button variant="ghost" onClick={handleReset} className="ml-auto">
                  Start New Complaint
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Right: Chatbot (1 col) */}
        <div className="md:col-span-1">
          <ChatPanel
            title="Relief Assistant"
            placeholder="Ask about refund process…"
            welcomeMessage="I'm here to help you through this. Ask me about refund timelines, your rights under RBI guidelines, or how to escalate your complaint."
            quickChips={["RBI Refund Rules", "How to escalate?"]}
          />
        </div>
      </div>
    </div>
  );
}

// ── Timeline step helper ──

function TimelineStep({
  number,
  title,
  description,
  urgent,
  link,
}: {
  number: number;
  title: string;
  description: string;
  urgent?: boolean;
  link?: { label: string; href: string };
}) {
  return (
    <div className="flex gap-3">
      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5 ${urgent ? "bg-risk-high text-white ring-2 ring-risk-high/30 ring-offset-1" : "bg-surface-200 text-ink-muted"}`}>
        {number}
      </div>
      <div className="flex-1">
        <p className={`text-sm font-semibold ${urgent ? "text-risk-high" : "text-ink"}`}>{title}</p>
        <p className="text-sm text-ink-muted mt-1 leading-relaxed">{description}</p>
        {link && (
          <a href={link.href} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 mt-1.5 px-2 py-1 rounded bg-surface-100 text-xs font-medium text-accent hover:bg-accent hover:text-white transition-colors">
            {link.label} <span>↗</span>
          </a>
        )}
      </div>
    </div>
  );
}
