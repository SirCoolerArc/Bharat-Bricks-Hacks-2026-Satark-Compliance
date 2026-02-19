# InsightX — Query Understanding & Insight Generation Approach

## 1. Dataset Characteristics (EDA-Informed)

Before describing the approach, it is essential to understand what the data actually looks like, as this directly shapes design decisions.

**Scale & Coverage**
- 250,000 transactions across a full calendar year (2024-01-01 to 2024-12-30)
- 17 columns, zero duplicate transaction IDs, zero unexpected NULLs
- 10 Indian states, 8 banks, 4 transaction types, 4 network types, 3 device types

**Critical Observation — Uniformity of Failure Rates**
The most important finding from EDA is that failure rates are remarkably uniform across almost all dimensions:

| Dimension | Range of Failure Rates |
|---|---|
| Transaction Type | 4.88% – 5.09% |
| Sender Bank | 4.82% – 5.10% |
| Device Type | 4.93% – 5.15% |
| Network Type | 4.86% – 5.22% |
| Age Group | 4.84% – 5.13% |
| Merchant Category | 4.59% – 5.10% |
| Day of Week | 4.77% – 5.10% |

This is a synthetic dataset and this uniformity is a direct consequence of that. The system must report differences accurately and avoid exaggerating them. The largest real differentials exist in bank pairs (Yes Bank → Kotak at 6.59% vs overall 4.95%) and across states (Uttar Pradesh 5.22% vs Telangana 4.71%).

**Amount Distribution**
- Heavily right-skewed: median ₹629, mean ₹1,312, max ₹42,099
- High-value threshold defined as P90 = ₹3,236 (used consistently throughout the system)
- Education transactions have by far the highest average (₹5,134), followed by Shopping (₹2,616)
- Transport and Entertainment have the lowest averages (₹310 and ₹418 respectively)

**Fraud Flag Reality**
- Only 480 transactions flagged (0.19%) — extremely sparse
- Flagged transactions are actually *less* likely to fail (4.38%) than unflagged ones (4.95%)
- Highest concentration: Recharge 0.24%, Kotak bank 0.25%, age group 18-25 at 0.23%
- All differences are marginal — fraud flag analysis must always include sample size context

**Transaction Composition**
- P2P dominates at 45% of volume, P2M at 35%, Bill Payment at 15%, Recharge at 5%
- 26-35 age group is the largest sender segment (35% of volume, highest avg amount ₹1,326)
- Android dominates device usage at 75% of all transactions
- Maharashtra is the highest volume state (37,427 transactions)
- Peak transaction hour is 19:00, with a sustained cluster from 17:00–20:00

---

## 2. Query Understanding Framework

### 2.1 Intent Classification

Every incoming natural language query is classified into one of six intent types before any computation begins:

| Intent | Trigger Phrases | Example |
|---|---|---|
| **Descriptive** | "what is", "how many", "show me" | "What is the average transaction amount?" |
| **Comparative** | "compare", "vs", "difference between", "which is higher" | "Compare failure rates for HDFC vs SBI" |
| **Temporal** | "when", "peak", "trend", "during", "hours", "weekend" | "What are peak transaction hours?" |
| **Segmentation** | "which group", "by age", "broken down", "most frequently" | "Which age group uses P2P most?" |
| **Correlation** | "relationship", "is there", "does X affect Y", "related to" | "Is network type related to failure rate?" |
| **Risk** | "flagged", "fraud", "anomalous", "high-value", "risk" | "What % of high-value transactions are flagged?" |

### 2.2 Entity Extraction

Entities are strictly mapped to actual dataset columns. No fields are inferred or invented.

| Entity Type | Dataset Column | Valid Values |
|---|---|---|
| Transaction type | `transaction type` | P2P, P2M, Bill Payment, Recharge |
| Merchant category | `merchant_category` | Food, Grocery, Fuel, Entertainment, Shopping, Healthcare, Education, Transport, Utilities, Other |
| Time — hour | `hour_of_day` | 0–23 |
| Time — day | `day_of_week` | Monday–Sunday |
| Time — period | `is_weekend` | 0 (weekday), 1 (weekend) |
| Age group | `sender_age_group` | 18-25, 26-35, 36-45, 46-55, 56+ |
| State | `sender_state` | Delhi, Maharashtra, Karnataka, Tamil Nadu, Uttar Pradesh, Gujarat, Rajasthan, Telangana, West Bengal, Andhra Pradesh |
| Bank | `sender_bank` / `receiver_bank` | SBI, HDFC, ICICI, Axis, PNB, Kotak, IndusInd, Yes Bank |
| Device | `device_type` | Android, iOS, Web |
| Network | `network_type` | 4G, 5G, WiFi, 3G |
| Outcome | `transaction_status` | SUCCESS, FAILED |
| Risk | `fraud_flag` | 0, 1 |

### 2.3 Metric Inference

| Query Phrase | Computed Metric | Formula |
|---|---|---|
| "failure rate" | Failure rate % | `FAILED / total × 100` |
| "success rate" | Success rate % | `SUCCESS / total × 100` |
| "most frequently" / "volume" | Transaction count & share | `count / total × 100` |
| "average amount" | Mean transaction value | `mean(amount_inr)` |
| "high value" | P90+ transactions | `amount_inr >= ₹3,236` (always stated explicitly in response) |
| "flagged" / "fraud flag" | Flag rate % | `fraud_flag=1 / total × 100` |
| "peak hours" | Top hours by volume | `groupby(hour_of_day).count()` sorted descending |
| "trend" | Change over time buckets | `groupby(time_unit).metric` with directional annotation |

### 2.4 Ambiguity Handling

When a query is ambiguous, the system states its assumption explicitly before answering rather than silently choosing one interpretation.

**Example:**
> Query: "Which transactions have high failure rates?"
> System: "I'll define 'high' as above the overall baseline of 4.95%. Would you like to adjust this threshold?"

**Threshold assumptions used consistently throughout the system:**
- "High value" → P90 (≥ ₹3,236) — always disclosed in response
- "Peak hours" → top 5 by volume (the 17:00–20:00 cluster, peaking at 19:00)
- "Significant difference" → >0.5 percentage point deviation from baseline
- "Low sample" warning → triggered when a segment has fewer than 200 transactions

---

## 3. Insight Generation Logic

### 3.1 Core Principle: Deterministic Analytics First

The LLM **never computes numbers**. The pipeline is strictly:

```
Natural Language Query
        ↓
LLM → Structured Intent JSON  (intent + entities + metric)
        ↓
Pandas → Actual computation on dataset
        ↓
LLM → Narrative wrapping of computed results only
```

This ensures insight accuracy is never dependent on the model's memory or hallucination.

### 3.2 Standard Computation Safeguards

**Always report with denominator context:**
- Not: "Recharge has the highest failure rate"
- But: "Recharge has a 5.09% failure rate (638 failed out of 12,527 transactions)"

**Always normalize for fair comparison:**
- Segment comparisons use rates, never absolute counts
- Example: P2P has more absolute failures (5,575) than Recharge (638) simply due to volume; the failure *rates* are comparable (4.96% vs 5.09%)

**Low sample warnings:**
- Fraud flag sub-segment analysis is particularly vulnerable given only 480 total flagged transactions
- Any segment with <200 transactions gets an explicit low-confidence note in the response

**Baseline anchoring:**
- Every metric is reported alongside the overall baseline
- Example: "Yes Bank's failure rate is 5.10%, slightly above the overall average of 4.95%"

### 3.3 Honest Reporting of Uniformity

Given the synthetic nature of the dataset, differences across most dimensions are small (typically <0.3 percentage points). The system will:
- Report differences accurately without inflating their significance
- Use language like "marginally higher" or "negligible difference" where appropriate
- Reserve "notably higher" for genuine outliers such as bank pairs (Yes Bank→Kotak at 6.59%) or state-level differences (Uttar Pradesh 5.22% vs Telangana 4.71%)

### 3.4 Response Structure — D-S-I-R Framework

Every response follows this mandatory four-part structure:

| Component | Purpose | Example |
|---|---|---|
| **D**irect Answer | One sentence answering the question | "Recharge transactions have the highest failure rate at 5.09%." |
| **S**upporting Metrics | The numbers behind the answer with denominators | "638 failed out of 12,527 transactions. Bill Payment is lowest at 4.88% (1,824/37,368)." |
| **I**nterpretation | What the pattern means in business context | "The spread across all types is narrow (4.88%–5.09%), suggesting no transaction type is systematically more failure-prone than others." |
| **R**ecommendation | Actionable next step where appropriate | "Monitor Recharge integrations for marginal improvement, but prioritize bank-pair reliability given the larger differentials observed there (up to 6.59%)." |

---

## 4. Pre-Computed Baselines (Analytics Engine Constants)

These baselines are established from EDA and used to validate live computation outputs and anchor all responses.

### Failure Rate Baselines
- **Overall:** 4.95% (12,376 / 250,000)
- **By type:** Recharge 5.09% > P2P 4.96% > P2M 4.95% > Bill Payment 4.88%
- **By bank:** Yes Bank 5.10% (highest) → HDFC 4.82% (lowest); spread: 0.28pp
- **By network:** 3G 5.22% (highest) → 5G/WiFi both 4.86% (lowest); spread: 0.36pp
- **By device:** Web 5.15% > Android 4.94% > iOS 4.93%
- **By age group:** 36-45 at 5.13% (highest) → 26-35 at 4.84% (lowest)
- **By state:** Uttar Pradesh 5.22% (highest) → Telangana 4.71% (lowest)
- **Bank pairs (P2P, notable outlier):** Yes Bank→Kotak 6.59% is the single largest observed differential

### Temporal Baselines
- **Peak hour:** 19:00 (21,232 transactions, 5.15% failure rate)
- **Peak cluster:** 17:00–20:00 sustained high volume
- **Weekend failure rate:** 5.09% vs weekday 4.89% (+0.20pp)
- **Highest failure day:** Sunday 5.10%, lowest: Friday 4.77%

### Fraud Flag Baselines
- **Overall flag rate:** 0.19% (480 / 250,000)
- **High-value (P90+) flag rate:** 0.25% — 1.31× overall concentration (modest)
- **Flagged transactions failure rate:** 4.38% (counterintuitively *lower* than unflagged 4.95%)
- **Highest flag rate by type:** Recharge 0.24%
- **Highest flag rate by bank:** Kotak 0.25%
- **Highest flag rate by age:** 18-25 at 0.23%

### Amount Baselines
- **Mean:** ₹1,312 | **Median:** ₹629 | **P90:** ₹3,236 | **P99:** ₹9,003
- **Highest avg category:** Education ₹5,134 (2.4× median amount)
- **Lowest avg category:** Transport ₹310
- **Amount distribution:** heavily right-skewed; log transformation recommended for visualization

---

## 5. Conversational Context Management

### State Vector
The system maintains a conversation state object across turns:

```json
{
  "active_filters": {
    "transaction_type": null,
    "time_period": null,
    "age_group": null,
    "bank": null,
    "device": null,
    "network": null,
    "is_weekend": null
  },
  "last_metric": null,
  "last_segment": null,
  "last_result": null,
  "turn_count": 0
}
```

### Supported Follow-Up Patterns

| Follow-Up Type | Example | System Handling |
|---|---|---|
| Drill-down | "Break that down by state" | Inherit all active filters, add new groupby dimension |
| Comparison toggle | "Compare with weekends" | Toggle is_weekend filter, rerun same metric |
| Scope change | "Now look at only P2M" | Update transaction_type filter, rerun |
| Entity correction | "Actually I meant ICICI not HDFC" | Replace entity in active filters, rerun |
| Why question | "Why is that?" | Return pre-computed interpretation from insight layer |
| Reset | "Start fresh" / "New question" | Clear state vector |

### Guardrails
- Drill-down producing a segment with <200 transactions triggers a low-confidence warning
- If scope change invalidates a previous assumption, this is stated explicitly
- Conversation history is passed to the LLM only for narrative context — all numbers are always freshly computed from pandas, never recalled from prior turns

---

## 6. Limitations & Honest Non-Claims

| What We Do Not Claim | Reason |
|---|---|
| Causal relationships | Correlation matrix shows near-zero correlations across all numeric fields; no causal inference is warranted |
| Fraud detection capability | fraud_flag is an automated review flag, not confirmed fraud; flagged transactions actually fail *less* often (4.38% vs 4.95%) |
| Forecasting or prediction | No time-series modelling; all temporal insights are descriptive |
| External benchmarks | No real-world UPI data to benchmark against |
| User-level patterns | No user IDs in dataset; all analysis is aggregate only |
| Drama where none exists | Failure rate differences are small across most dimensions due to synthetic data uniformity — the system will say so |

---

## 7. Technology Decisions

| Component | Choice | Rationale |
|---|---|---|
| Data computation | Pandas | 250k rows fits in memory; all aggregations run in under 1 second |
| LLM | Gemini API | Team familiarity; strong instruction-following for structured JSON output |
| Interface | Streamlit | Fastest path to demo-ready conversational UI in Python |
| State management | Python dict | Sufficient for the conversation depth expected; no over-engineering |
| No vector database | — | Structured tabular queries do not require semantic search |
| No SQL layer | — | Pandas operations are sufficient, more readable, and easier to debug |
