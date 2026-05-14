"""
SATARK — FastAPI Chatbot Backend
Tool-using orchestrator agent over gold tables + RBI / NPCI regulatory corpus, driven by Gemini 2.5 Flash function-calling.

Endpoints:
  POST /api/chat          — Streaming SSE chat responses
  POST /api/dashboard-data — Pre-aggregated KPI snapshot
  GET  /api/health        — Health check
"""

import json
import logging
import asyncio
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents.orchestrator import run_orchestrator
from data.gold_tables import get_dashboard_kpi

# ── Logging ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("satark-api")

# ── FastAPI App ───────────────────────────────────────────────────
app = FastAPI(
    title="SATARK API",
    description="Fraud compliance chatbot backend with 3-layer query pipeline",
    version="1.0.0",
)

# CORS — allow the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ─────────────────────────────────────
class HistoryMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[list[HistoryMessage]] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    pipeline: dict


# ── Endpoints ─────────────────────────────────────────────────────


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="satark-api",
        version="1.0.0",
        pipeline={
            "layer1_router": "active",
            "layer2a_data_agent": "active",
            "layer2b_rag_agent": "active",
            "layer3_synthesizer": "active",
        },
    )


@app.post("/api/dashboard-data")
async def dashboard_data():
    """Return pre-aggregated KPI snapshot from gold tables."""
    try:
        kpi = get_dashboard_kpi()
        return {"status": "ok", "data": kpi}
    except Exception as e:
        logger.error(f"Dashboard data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analytics")
async def analytics_data(request: dict):
    """Serve structured rows for specific requested gold tables (replaces remote API)."""
    table = request.get("table", "")
    from data.gold_tables import (
        GEO_HEATMAP, SCAM_TAXONOMY, RISK_DISTRIBUTION, HOURLY_FRAUD_PATTERN, ALERT_EFFECTIVENESS
    )
    
    try:
        if table == "geo_heatmap":
            return {"data": GEO_HEATMAP}
        elif table == "scam_taxonomy":
            return {"data": SCAM_TAXONOMY}
        elif table == "hourly_fraud_pattern":
            from data.gold_tables import HOURLY_DATA_ROWS
            return {"data": HOURLY_DATA_ROWS}
        elif table == "risk_distribution":
            # Risk distribution is natively a dict {HIGH: ..., MEDIUM: ..., LOW: ..., totals: ...}
            # The frontend expects an array like: [ {rule_risk_tier: 'HIGH', txn_count: ..., fraud_count: ..., fraud_rate_pct: ...} ]
            tiers = []
            for tier in ["HIGH", "MEDIUM", "LOW"]:
                if tier in RISK_DISTRIBUTION:
                    d = RISK_DISTRIBUTION[tier]
                    tiers.append({
                        "rule_risk_tier": tier,
                        "txn_count": d.get("count", 0),
                        "fraud_count": 0, # mock
                        "fraud_rate_pct": d.get("fraud_rate_pct", 0)
                    })
            return {"data": tiers}
        elif table == "alert_effectiveness":
            # Provide an array to prevent crashes
            return {"data": [{"dummy": 1}]}
        else:
            raise HTTPException(status_code=404, detail=f"Table {table} not found")
            
    except Exception as e:
        logger.error(f"Analytics endpoint error reading {table}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Main chat endpoint — drives the tool-using orchestrator agent.
    Streams SSE events as the agent classifies, calls tools, and writes
    the final answer.
    """
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    history = [{"role": m.role, "content": m.content} for m in (request.history or [])]
    logger.info(f"Query: '{message[:80]}...'")

    async def event_stream():
        # Opening meta event so the chatbot route can populate diagnostics
        # incrementally as tools fire.
        opening = {
            "type": "meta",
            "data_tables_used": [],
            "rag_sources": [],
            "row_count": 150031,
        }
        yield f"data: {json.dumps(opening)}\n\n"

        tables_used: list[str] = []
        rag_sources: list[dict] = []

        async for event in _drive_orchestrator(message, history):
            etype = event.get("type")

            if etype == "tables_used":
                tables_used = event.get("tables", [])
                # Emit an updated meta so the frontend sees what tools touched.
                yield f"data: {json.dumps({'type': 'meta', 'data_tables_used': tables_used, 'rag_sources': rag_sources, 'row_count': 150031})}\n\n"
            elif etype == "rag_sources":
                rag_sources = event.get("sources", [])
                yield f"data: {json.dumps({'type': 'meta', 'data_tables_used': tables_used, 'rag_sources': rag_sources, 'row_count': 150031})}\n\n"
            else:
                yield f"data: {json.dumps(event)}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


async def _drive_orchestrator(message: str, history: list[dict]):
    """
    Bridge the orchestrator's sync Gemini calls into the FastAPI async loop.
    The orchestrator itself is an async generator but its inner Gemini calls
    are blocking — we offload each step into a thread via asyncio.to_thread
    indirectly by running the generator on the default event loop.
    """
    import queue
    import threading

    q: queue.Queue = queue.Queue()
    sentinel = object()

    def _run():
        try:
            import asyncio as _asyncio

            async def _collect():
                async for ev in run_orchestrator(message, history):
                    q.put(ev)

            _asyncio.run(_collect())
        except Exception as e:
            logger.exception("Orchestrator crashed")
            q.put({"type": "text", "content": f"Internal error: {e}"})
        finally:
            q.put(sentinel)

    threading.Thread(target=_run, daemon=True).start()

    while True:
        try:
            item = q.get_nowait()
        except queue.Empty:
            await asyncio.sleep(0.02)
            continue

        if item is sentinel:
            return
        yield item


# ── Run ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
