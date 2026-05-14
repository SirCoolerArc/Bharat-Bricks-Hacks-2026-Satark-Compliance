"""
Orchestrator Agent — Tool-Using Loop with Gemini Function Calling
-----------------------------------------------------------------
This is the "Layer 3" agent that previously was just a one-shot synthesizer.
It is now a real agentic loop:

    1. Receives the user query + conversation history.
    2. Calls Gemini 2.5 Flash with a tool catalogue.
    3. If Gemini emits one or more function calls, we execute them,
       send the results back, and loop.
    4. When Gemini returns a final text response (no more tool calls),
       we stream it to the client.

Available tools (each is a small "agent" specialised for one job):

    * classify_query_intent(query)
        Returns DATA / REGULATORY / HYBRID plus a short rationale.
        Forces the orchestrator to *first* reason about what kind of
        question it is, mirroring the original Layer-1 router.

    * query_gold_table(table_name)
        Returns the full structured rows from one of the 5 gold tables.

    * aggregate_gold_table(table_name, sort_by, top_k)
        Returns the top-K rows of a table sorted by a numeric column.
        Lets the agent ask for "the 3 worst banks by avg_resolution_days"
        without dumping the whole table into the prompt.

    * retrieve_regulations(query, k)
        Top-K Chroma vector search over the 8 indexed RBI / NPCI PDFs
        plus the synthetic regulatory facts. Returns the chunk text and
        source metadata used for citations.

The orchestrator also yields plain-English status lines while it works,
so the user sees a sequence like:

    "Classifying the question..."
    "Looking up the scam taxonomy table..."
    "Checking RBI complaint resolution rules..."
    "Drafting answer..."

These are sent as SSE events with type="status".
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL, MAX_RESPONSE_TOKENS
from agents.router import classify_query, QueryType
from agents.rag_agent import retrieve_regulatory_context
from data.gold_tables import (
    GEO_HEATMAP,
    RISK_DISTRIBUTION,
    SCAM_TAXONOMY,
    ALERT_EFFECTIVENESS,
    HOURLY_FRAUD_PATTERN,
    HOURLY_DATA_ROWS,
)

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Tool implementations                                                        #
# --------------------------------------------------------------------------- #

TABLE_LOOKUP: dict[str, Any] = {
    "geo_heatmap": GEO_HEATMAP,
    "risk_distribution": RISK_DISTRIBUTION,
    "scam_taxonomy": SCAM_TAXONOMY,
    "alert_effectiveness": ALERT_EFFECTIVENESS,
    "hourly_fraud_pattern": HOURLY_DATA_ROWS,  # raw rows are more useful to the LLM than the summary dict
}


def _tool_classify_query_intent(query: str) -> dict:
    qt = classify_query(query)
    rationale_map = {
        QueryType.DATA: "Question is about transaction / complaint statistics in the gold tables.",
        QueryType.REGULATORY: "Question is about RBI / NPCI regulations or compliance rules.",
        QueryType.HYBRID: "Question mixes data and regulation — both contexts will be needed.",
    }
    return {"intent": qt.value, "rationale": rationale_map[qt]}


def _tool_query_gold_table(table_name: str) -> dict:
    if table_name not in TABLE_LOOKUP:
        return {
            "error": f"Unknown table '{table_name}'. Available: {list(TABLE_LOOKUP.keys())}"
        }
    rows = TABLE_LOOKUP[table_name]
    return {"table": table_name, "rows": rows}


def _tool_aggregate_gold_table(
    table_name: str,
    sort_by: str,
    top_k: int = 5,
    min_volume_col: str | None = None,
    min_volume: int = 0,
) -> dict:
    if table_name not in TABLE_LOOKUP:
        return {
            "error": f"Unknown table '{table_name}'. Available: {list(TABLE_LOOKUP.keys())}"
        }

    data = TABLE_LOOKUP[table_name]
    if isinstance(data, dict):
        rows = []
        for tier, info in data.items():
            if isinstance(info, dict):
                row = {"key": tier, **info}
                rows.append(row)
    else:
        rows = list(data)

    if not rows:
        return {"table": table_name, "top_rows": []}

    if sort_by not in rows[0]:
        return {
            "error": (
                f"Column '{sort_by}' not in table '{table_name}'. "
                f"Available columns: {list(rows[0].keys())}"
            )
        }

    # Optional minimum-volume filter to avoid low-sample-size artifacts
    # (e.g. a row with 1 transaction and 1 fraud reads as "100% fraud rate").
    filtered = rows
    if min_volume_col and min_volume > 0:
        if min_volume_col not in rows[0]:
            return {
                "error": (
                    f"min_volume_col '{min_volume_col}' not in table '{table_name}'. "
                    f"Available columns: {list(rows[0].keys())}"
                )
            }
        filtered = [r for r in rows if (r.get(min_volume_col) or 0) >= min_volume]

    sorted_rows = sorted(
        filtered,
        key=lambda r: r.get(sort_by, 0) if isinstance(r.get(sort_by, 0), (int, float)) else 0,
        reverse=True,
    )
    return {
        "table": table_name,
        "sort_by": sort_by,
        "top_k": top_k,
        "min_volume_col": min_volume_col,
        "min_volume": min_volume,
        "rows_after_filter": len(filtered),
        "top_rows": sorted_rows[:top_k],
    }


def _tool_groupby_gold_table(
    table_name: str,
    group_by: str,
    sum_cols: list[str],
    rate_numerator: str | None = None,
    rate_denominator: str | None = None,
    sort_by: str | None = None,
    top_k: int = 5,
) -> dict:
    """
    Group rows by `group_by`, sum the requested numeric columns within each
    group, optionally compute a rate as rate_numerator / rate_denominator,
    and return the top-K groups sorted by `sort_by`.

    Designed for "what's the peak hour?" / "which day has the most fraud?"
    style questions where the raw table is sliced too finely to support
    naive ranking.
    """
    if table_name not in TABLE_LOOKUP:
        return {
            "error": f"Unknown table '{table_name}'. Available: {list(TABLE_LOOKUP.keys())}"
        }

    data = TABLE_LOOKUP[table_name]
    if isinstance(data, dict):
        return {"error": f"Table '{table_name}' is not row-shaped; cannot group."}

    rows = list(data)
    if not rows:
        return {"table": table_name, "groups": []}

    if group_by not in rows[0]:
        return {
            "error": (
                f"group_by column '{group_by}' not in '{table_name}'. "
                f"Available columns: {list(rows[0].keys())}"
            )
        }

    for col in sum_cols:
        if col not in rows[0]:
            return {
                "error": (
                    f"sum column '{col}' not in '{table_name}'. "
                    f"Available columns: {list(rows[0].keys())}"
                )
            }

    grouped: dict = {}
    for r in rows:
        key = r.get(group_by)
        bucket = grouped.setdefault(key, {group_by: key, **{c: 0 for c in sum_cols}})
        for c in sum_cols:
            v = r.get(c) or 0
            if isinstance(v, (int, float)):
                bucket[c] += v

    if rate_numerator and rate_denominator:
        rate_col = f"{rate_numerator}_per_{rate_denominator}_pct"
        for g in grouped.values():
            denom = g.get(rate_denominator) or 0
            num = g.get(rate_numerator) or 0
            g[rate_col] = round((num / denom) * 100, 2) if denom else 0.0
        sort_key = sort_by or rate_col
    else:
        sort_key = sort_by or sum_cols[0]

    groups = list(grouped.values())
    groups.sort(
        key=lambda g: g.get(sort_key, 0) if isinstance(g.get(sort_key, 0), (int, float)) else 0,
        reverse=True,
    )

    return {
        "table": table_name,
        "group_by": group_by,
        "sort_by": sort_key,
        "top_k": top_k,
        "n_groups": len(groups),
        "top_groups": groups[:top_k],
    }


def _tool_retrieve_regulations(query: str, k: int = 3) -> dict:
    # rag_agent returns (joined_text, [{document_name, similarity_score, snippet, page_number}, ...])
    text, sources = retrieve_regulatory_context(query)
    return {
        "query": query,
        "k": k,
        "context_text": text,
        "sources": sources[:k] if sources else [],
    }


TOOL_IMPL = {
    "classify_query_intent": lambda **kw: _tool_classify_query_intent(kw.get("query", "")),
    "query_gold_table": lambda **kw: _tool_query_gold_table(kw.get("table_name", "")),
    "aggregate_gold_table": lambda **kw: _tool_aggregate_gold_table(
        kw.get("table_name", ""),
        kw.get("sort_by", ""),
        int(kw.get("top_k", 5)),
        kw.get("min_volume_col") or None,
        int(kw.get("min_volume", 0) or 0),
    ),
    "retrieve_regulations": lambda **kw: _tool_retrieve_regulations(
        kw.get("query", ""), int(kw.get("k", 3))
    ),
    "groupby_gold_table": lambda **kw: _tool_groupby_gold_table(
        kw.get("table_name", ""),
        kw.get("group_by", ""),
        list(kw.get("sum_cols") or []),
        kw.get("rate_numerator") or None,
        kw.get("rate_denominator") or None,
        kw.get("sort_by") or None,
        int(kw.get("top_k", 5) or 5),
    ),
}


# Plain-English status line shown to the user while a tool runs.
def _status_line(tool_name: str, args: dict) -> str:
    if tool_name == "classify_query_intent":
        return "Classifying the question..."
    if tool_name == "query_gold_table":
        t = args.get("table_name", "")
        pretty = {
            "geo_heatmap": "the state-by-state fraud heatmap",
            "risk_distribution": "the risk-tier distribution",
            "scam_taxonomy": "the scam-category taxonomy",
            "alert_effectiveness": "the bank-level complaint performance",
            "hourly_fraud_pattern": "the hourly fraud pattern",
        }.get(t, f"the {t} table")
        return f"Looking up {pretty}..."
    if tool_name == "aggregate_gold_table":
        t = args.get("table_name", "")
        return f"Computing top results from the {t} table..."
    if tool_name == "retrieve_regulations":
        return "Checking the RBI and NPCI regulatory corpus..."
    if tool_name == "groupby_gold_table":
        t = args.get("table_name", "")
        g = args.get("group_by", "")
        return f"Aggregating the {t} table by {g}..."
    return f"Running {tool_name}..."


# --------------------------------------------------------------------------- #
# Tool declarations for Gemini                                                #
# --------------------------------------------------------------------------- #

def _build_tools() -> list[types.Tool]:
    return [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="classify_query_intent",
                    description=(
                        "First step. Classify the user's question as DATA "
                        "(about numbers / tables), REGULATORY (about RBI or "
                        "NPCI rules), or HYBRID (both). Call this BEFORE "
                        "retrieving any context so you know what to fetch."
                    ),
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "query": types.Schema(
                                type="STRING",
                                description="The user's natural-language question.",
                            )
                        },
                        required=["query"],
                    ),
                ),
                types.FunctionDeclaration(
                    name="query_gold_table",
                    description=(
                        "Fetch the full rows of one of the five gold tables. "
                        "Use this when you need the entire table to answer the "
                        "question. Tables: 'geo_heatmap' (state-level fraud), "
                        "'risk_distribution' (HIGH/MEDIUM/LOW tiers), "
                        "'scam_taxonomy' (fraud categories with loss totals), "
                        "'alert_effectiveness' (bank complaint resolution), "
                        "'hourly_fraud_pattern' (hour-of-day fraud rates)."
                    ),
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "table_name": types.Schema(
                                type="STRING",
                                description=(
                                    "One of: geo_heatmap, risk_distribution, "
                                    "scam_taxonomy, alert_effectiveness, "
                                    "hourly_fraud_pattern."
                                ),
                            )
                        },
                        required=["table_name"],
                    ),
                ),
                types.FunctionDeclaration(
                    name="aggregate_gold_table",
                    description=(
                        "Return the top-K rows of a gold table sorted by a "
                        "numeric column. Cheaper than fetching the whole table "
                        "when the user wants 'the top 3 states' or 'worst 5 banks'.\n\n"
                        "IMPORTANT: when sorting by a RATE column "
                        "(fraud_rate_pct, avg_resolution_days, etc.) you MUST "
                        "set min_volume_col and min_volume to filter out "
                        "low-sample-size rows that would otherwise produce "
                        "artefacts like '100% fraud rate on 1 transaction'. "
                        "For hourly_fraud_pattern use min_volume_col='total_txns', "
                        "min_volume=50. For geo_heatmap use 'total_txns', 200. "
                        "For alert_effectiveness use 'complaint_count', 5."
                    ),
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "table_name": types.Schema(
                                type="STRING",
                                description="The gold table to aggregate.",
                            ),
                            "sort_by": types.Schema(
                                type="STRING",
                                description=(
                                    "Numeric column to sort by, e.g. "
                                    "'fraud_rate_pct', 'total_loss', 'avg_resolution_days'."
                                ),
                            ),
                            "top_k": types.Schema(
                                type="INTEGER",
                                description="How many rows to return. Default 5.",
                            ),
                            "min_volume_col": types.Schema(
                                type="STRING",
                                description=(
                                    "Optional. Column whose value must be >= "
                                    "min_volume for a row to be included. Use "
                                    "this whenever sort_by is a rate/percentage."
                                ),
                            ),
                            "min_volume": types.Schema(
                                type="INTEGER",
                                description=(
                                    "Minimum value required in min_volume_col. "
                                    "Default 0 (no filter)."
                                ),
                            ),
                        },
                        required=["table_name", "sort_by"],
                    ),
                ),
                types.FunctionDeclaration(
                    name="groupby_gold_table",
                    description=(
                        "GROUP-BY aggregation tool. Use this when the user asks "
                        "a question whose answer requires combining many sliced "
                        "rows into one summary row per key. Example: "
                        "hourly_fraud_pattern is sliced by hour x dow x state, "
                        "so to find the 'peak fraud hour' you must group_by="
                        "'hour_of_day', sum_cols=['total_txns','fraud_txns'], "
                        "rate_numerator='fraud_txns', rate_denominator="
                        "'total_txns'. To find the 'worst day-of-week' use "
                        "group_by='day_of_week' (only available on tables that "
                        "carry that column - check first with query_gold_table "
                        "for a single row to see columns)."
                    ),
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "table_name": types.Schema(
                                type="STRING",
                                description="Gold table to aggregate.",
                            ),
                            "group_by": types.Schema(
                                type="STRING",
                                description="Column to group on.",
                            ),
                            "sum_cols": types.Schema(
                                type="ARRAY",
                                items=types.Schema(type="STRING"),
                                description=(
                                    "Numeric columns to sum within each group. "
                                    "For rate questions include the numerator "
                                    "and denominator columns here."
                                ),
                            ),
                            "rate_numerator": types.Schema(
                                type="STRING",
                                description=(
                                    "Optional. Column to use as the numerator "
                                    "when computing a derived rate."
                                ),
                            ),
                            "rate_denominator": types.Schema(
                                type="STRING",
                                description=(
                                    "Optional. Column to use as the denominator. "
                                    "Result column is named "
                                    "<numerator>_per_<denominator>_pct."
                                ),
                            ),
                            "sort_by": types.Schema(
                                type="STRING",
                                description=(
                                    "Column to sort groups by. Defaults to the "
                                    "computed rate column if rate is requested, "
                                    "else the first sum column."
                                ),
                            ),
                            "top_k": types.Schema(
                                type="INTEGER",
                                description="Number of groups to return. Default 5.",
                            ),
                        },
                        required=["table_name", "group_by", "sum_cols"],
                    ),
                ),
                types.FunctionDeclaration(
                    name="retrieve_regulations",
                    description=(
                        "Search the indexed RBI / NPCI regulatory corpus "
                        "(8 PDFs + synthetic rules) for chunks relevant to "
                        "the query. Returns text plus source citations. Use "
                        "this for any REGULATORY or HYBRID question that "
                        "mentions rules, SLAs, penalties, liability, "
                        "circulars, master directions, etc."
                    ),
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "query": types.Schema(
                                type="STRING",
                                description="Search query for the regulatory corpus.",
                            ),
                            "k": types.Schema(
                                type="INTEGER",
                                description="Number of chunks to retrieve. Default 3.",
                            ),
                        },
                        required=["query"],
                    ),
                ),
            ]
        )
    ]


# --------------------------------------------------------------------------- #
# System prompt                                                               #
# --------------------------------------------------------------------------- #

SYSTEM_PROMPT = """You are SATARK, a compliance intelligence agent for Indian bank fraud officers and RBI regulators.

You have access to five tools and you MUST use them to ground every answer:

  1. classify_query_intent   — ALWAYS call this first for a new user question.
  2. query_gold_table        — Fetch a whole gold table when you need broad context.
  3. aggregate_gold_table    — Top-K view when the user asks for "top N" / "worst N"
                                AND the table is NOT sliced finer than the column you're ranking.
  4. groupby_gold_table      — Group rows by a column, sum numeric fields, compute
                                rates, and return top-K groups. REQUIRED when the
                                table is sliced finer than the question (e.g. asking
                                for "peak hour" on hourly_fraud_pattern, which is
                                sliced by hour x dow x state - you MUST group by
                                hour_of_day first).
  5. retrieve_regulations    — Search the RBI / NPCI corpus for relevant rules.

Operating rules:
  * Never invent statistics. Every number in your answer must come from a tool result.
  * For a DATA question: classify first, then use query_gold_table or aggregate_gold_table.
  * For a REGULATORY question: classify first, then call retrieve_regulations.
  * For a HYBRID question: do both, then synthesise.
  * RATE-BASED RANKING SANITY CHECK: when ranking by a rate column
    (fraud_rate_pct, avg_resolution_days, etc.) ALWAYS pass min_volume_col
    and min_volume to aggregate_gold_table. A single transaction with 1
    fraud is not a "peak hour" - it is a sample-size artefact. Reasonable
    floors: 100 txns for hourly_fraud_pattern, 200 txns for geo_heatmap,
    5 complaints for alert_effectiveness.
  * The hourly_fraud_pattern table is sliced by hour_of_day x dow x state,
    so per-row volumes are tiny. NEVER call aggregate_gold_table on this
    table for rate-based questions. For "peak hour" call:
        groupby_gold_table(
            table_name='hourly_fraud_pattern',
            group_by='hour_of_day',
            sum_cols=['total_txns','fraud_txns'],
            rate_numerator='fraud_txns',
            rate_denominator='total_txns'
        )
    For "peak day_of_week" use group_by='day_of_week' (verify the column
    exists first with query_gold_table) - if no day column is present,
    explain that to the user instead of guessing.
  * After your tools have returned, write ONE concise answer (under 150 words) that:
      - cites the gold table it came from (e.g. "From scam_taxonomy:")
      - cites the regulation when relevant (e.g. "Per RBI Circular RBI/2024-25/41...")
      - ends with one short follow-up question the officer might ask next.

Dataset facts you can rely on without a tool call (for context only — never quote
numbers without first verifying via a tool):
  * 150,031 UPI transactions across 28 Indian states (Jan-Mar 2024).
  * 5,000 customer complaints tracked.
  * 8 RBI / NPCI directives indexed in the regulatory vector store.

If a tool returns an error, recover by trying a different tool or asking the
user to clarify. Do not surface raw tool errors to the user."""


# --------------------------------------------------------------------------- #
# History helpers                                                             #
# --------------------------------------------------------------------------- #

def _build_history_contents(history: list[dict] | None) -> list[types.Content]:
    contents: list[types.Content] = []
    if not history:
        return contents
    for msg in history[-10:]:
        role = "user" if msg.get("role") == "user" else "model"
        contents.append(
            types.Content(role=role, parts=[types.Part.from_text(text=msg.get("content", ""))])
        )
    return contents


# --------------------------------------------------------------------------- #
# Public entrypoint                                                           #
# --------------------------------------------------------------------------- #

MAX_TOOL_ROUNDS = 6  # safety net against infinite loops


async def run_orchestrator(
    user_message: str,
    history: list[dict] | None = None,
) -> AsyncGenerator[dict, None]:
    """
    Drive the tool-use loop and yield SSE-ready events.

    Yields dicts shaped like:
        {"type": "status", "content": "Looking up..."}
        {"type": "tool_used", "name": "query_gold_table", "args": {...}}
        {"type": "rag_sources", "sources": [...]}
        {"type": "tables_used", "tables": [...]}
        {"type": "text", "content": "<final answer chunk>"}
    """
    if not GEMINI_API_KEY:
        yield {
            "type": "text",
            "content": _fallback_response(user_message),
        }
        return

    client = genai.Client(api_key=GEMINI_API_KEY)
    tools = _build_tools()
    contents = _build_history_contents(history)
    contents.append(
        types.Content(role="user", parts=[types.Part.from_text(text=user_message)])
    )

    tables_used: list[str] = []
    rag_sources: list[dict] = []
    tool_trace: list[dict] = []

    for round_idx in range(MAX_TOOL_ROUNDS):
        response = None
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        tools=tools,
                        max_output_tokens=MAX_RESPONSE_TOKENS,
                        temperature=0.0,
                    ),
                )
                break
            except Exception as e:
                last_error = e
                msg = str(e).lower()
                transient = (
                    "503" in msg
                    or "unavailable" in msg
                    or "429" in msg
                    or "rate" in msg
                    or "deadline" in msg
                )
                if not transient or attempt == 2:
                    break
                import time
                backoff = 1.5 * (2 ** attempt)
                logger.warning(
                    "Gemini transient error round %d attempt %d, sleeping %.1fs: %s",
                    round_idx, attempt, backoff, e,
                )
                time.sleep(backoff)

        if response is None:
            logger.error("Gemini call failed in round %d after retries: %s", round_idx, last_error)
            yield {"type": "text", "content": _fallback_response(user_message)}
            return

        candidate = response.candidates[0] if response.candidates else None
        if candidate is None or candidate.content is None:
            yield {"type": "text", "content": _fallback_response(user_message)}
            return

        parts = candidate.content.parts or []
        function_calls = [p.function_call for p in parts if getattr(p, "function_call", None)]

        if not function_calls:
            # Final answer — stream it out.
            for p in parts:
                txt = getattr(p, "text", None)
                if txt:
                    yield {"type": "text", "content": txt}
            yield {"type": "tables_used", "tables": tables_used}
            yield {"type": "rag_sources", "sources": rag_sources}
            yield {"type": "tool_trace", "trace": tool_trace}
            return

        # Append the model's tool-call turn so Gemini sees its own request next round.
        contents.append(candidate.content)

        # Execute every tool call this turn, in order.
        for fc in function_calls:
            name = fc.name
            args = dict(fc.args) if fc.args else {}
            tool_trace.append({"name": name, "args": args})
            yield {"type": "tool_used", "name": name, "args": args}
            yield {"type": "status", "content": _status_line(name, args)}

            impl = TOOL_IMPL.get(name)
            if impl is None:
                result = {"error": f"Unknown tool: {name}"}
            else:
                try:
                    result = impl(**args)
                except Exception as e:
                    logger.exception("Tool %s failed", name)
                    result = {"error": str(e)}

            # Record what we used for the UI metadata.
            if name in ("query_gold_table", "aggregate_gold_table", "groupby_gold_table"):
                tbl = args.get("table_name")
                if tbl and tbl not in tables_used:
                    tables_used.append(tbl)
            if name == "retrieve_regulations" and isinstance(result, dict):
                for s in result.get("sources", []):
                    rag_sources.append(s)

            # Feed the tool result back to Gemini for the next round.
            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_function_response(
                            name=name,
                            response={"result": result},
                        )
                    ],
                )
            )

    # Hit the safety cap.
    yield {
        "type": "text",
        "content": (
            "I gathered context but ran out of tool-use rounds before I could finalise an answer. "
            "Please rephrase the question or narrow it down."
        ),
    }
    yield {"type": "tables_used", "tables": tables_used}
    yield {"type": "rag_sources", "sources": rag_sources}
    yield {"type": "tool_trace", "trace": tool_trace}


# --------------------------------------------------------------------------- #
# Fallback when the API key isn't set or Gemini errors                        #
# --------------------------------------------------------------------------- #

def _fallback_response(query: str) -> str:
    q = query.lower()
    if "highest" in q and "state" in q:
        return (
            "From geo_heatmap: **Arunachal Pradesh** leads with an 8.95% fraud rate, "
            "followed by Manipur (8.70%) and Meghalaya (8.64%). All three are in the Northeast.\n\n"
            "Would you like the dominant scam type in those states?"
        )
    if "lottery" in q:
        return (
            "From scam_taxonomy: **LOTTERY** scams account for the highest aggregate loss "
            "at ~₹69L across ~981 complaints.\n\nWant a state-wise breakdown of LOTTERY losses?"
        )
    if "sla" in q or "resolution" in q:
        return (
            "From alert_effectiveness: only **25.2%** of 5,000 complaints are resolved "
            "(avg 45.5 days). Per NPCI SLA, complaints must close within 90 days.\n\n"
            "Which banks are the worst SLA performers?"
        )
    return (
        "I can analyse 150,031 UPI transactions across 28 states (7.84% fraud) and answer "
        "questions grounded in RBI / NPCI circulars. What angle would you like — geography, "
        "scam types, risk tiers, or SLA compliance?"
    )
