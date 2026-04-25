# SATARK — UPI Fraud Protection Platform

Real-time UPI fraud detection and protection powered by Databricks intelligence.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Next.js 14 (TypeScript + Tailwind)                      │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│  │ /protect  │ │ /learn   │ │ /relief  │ │ /dashboard │  │
│  │ Risk      │ │ Patterns │ │ Complaint│ │ Analytics  │  │
│  │ Checker   │ │ + Chat   │ │ + Chat   │ │ + Charts   │  │
│  └─────┬────┘ └────┬─────┘ └─────┬────┘ └─────┬──────┘  │
│        │           │             │             │         │
│  ┌─────┴───────────┴─────────────┴─────────────┴───────┐ │
│  │  API Routes: /score, /analyze, /chat, /dashboard    │ │
│  └─────┬────────────────────────────────────────┬──────┘ │
│        │                                        │        │
│  ┌─────┴────────┐                   ┌───────────┴──────┐ │
│  │ ONNX Scorer  │                   │ Databricks Client│ │
│  │ + Classifier │                   │ (SQL Warehouse)  │ │
│  │ + RAG Chat   │                   │ (Model Serving)  │ │
│  └──────────────┘                   └──────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

## Tech Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Charts**: Custom SVG components (BarChart, DonutChart) — zero dependencies
- **Scoring**: ONNX Runtime (XGBoost model) + keyword-based remark classifier
- **Chatbot**: Mock RAG with RBI guidance → Databricks Model Serving (when connected)
- **Data**: Databricks SQL Warehouse (Gold tables)

## Setup

```bash
cd web
npm install
cp .env.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Running Modes

### Offline Mode (default)

The app works fully without any Databricks credentials. All data comes from built-in mock datasets that mirror the synthetic data pipeline:

- **Dashboard**: Shows mock KPIs, scam breakdown charts, complaint status donut, and monthly trends
- **Protect**: Transaction scoring uses the heuristic fallback (no ONNX model needed)
- **Learn**: Keyword classifier runs locally, chatbot returns pre-built RBI guidance
- **Relief**: Complaint letter generation is fully client-side

Just run `npm run dev` without configuring `.env.local`.

### Databricks-Connected Mode

Fill in your `.env.local` with real credentials:

```env
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi_your_token_here
DATABRICKS_WAREHOUSE_ID=your_warehouse_id
DATABRICKS_SERVING_ENDPOINT=https://...  # optional, for RAG chatbot
```

When connected:
- Dashboard reads KPIs, scam breakdown, and alerts from Gold tables
- Chatbot calls the Databricks Model Serving endpoint
- Complaint insert writes to the complaints table
- All functions fail gracefully back to mock data if the connection drops

### With ONNX Model

```bash
# Export from MLflow and save:
mkdir -p models
# Place fraud_scorer.onnx in web/models/
npm install onnxruntime-node  # install the optional dependency
```

## Pages

| Route | Purpose |
|-------|---------|
| `/protect` | Transaction risk checker with 4 demo scenarios, risk gauge, recommendations |
| `/learn` | Fraud pattern feed, message analyzer, AI safety chatbot |
| `/relief` | 4-step complaint wizard with letter generation, bank helplines, RBI rights |
| `/dashboard` | KPI cards, scam type bar chart, complaint donut, trend chart, alert feed |

## Project Structure

```
web/src/
├── app/              # Pages + API routes
│   ├── api/
│   │   ├── score-transaction/   # ONNX/heuristic scoring
│   │   ├── analyze-message/     # Keyword classifier
│   │   ├── chat/                # RAG chatbot
│   │   └── dashboard/           # Dashboard data feed
│   ├── protect/, learn/, relief/, dashboard/
├── components/       # TopNav, RiskGauge, BarChart, DonutChart, ChatPanel, etc.
├── lib/
│   ├── databricks/   # SQL client + data queries (KPI, patterns, alerts, complaints, dashboard)
│   ├── scoring/      # ONNX loader + remark classifier + feature builder
│   └── chatbot/      # Mock RAG → Databricks Model Serving
└── types/            # All TypeScript interfaces
```

## Remaining Work

1. Train XGBoost model in Databricks and export to ONNX
2. Build RAG chain in Databricks with RBI document retrieval
3. Connect live SQL Warehouse with Gold tables
4. Add real-time WebSocket updates for the dashboard
5. Add end-to-end test coverage
6. Mobile-responsive polish
