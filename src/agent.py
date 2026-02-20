"""
agent.py — InsightX Agentic Execution Loop (v2)
================================================
Implements intelligent multi-dimensional root cause analysis.

ARCHITECTURE:
Instead of asking the LLM to plan sub-queries (fragile, unreliable),
this version runs deterministic cross-dimensional pandas analyses
and uses the LLM only for synthesis.

FLOW for "why" queries:
    1. Identify subject entity & metric from parsed intent
    2. Run failure_rate grouped by each of N dimensions directly via pandas
    3. Rank dimensions by explanatory spread
    4. LLM synthesises findings into a root cause narrative

FLOW for standard queries:
    → Single-pass pipeline (unchanged)
"""

import json
import re
import os
from google import genai
from dotenv import load_dotenv

try:
    from src.query_parser import parse_query
    from src.analytics_engine import (
        run_query,
        _grouped_failure_rate,
        _grouped_flag_rate,
        _apply_filters,
    )
    from src.insight_generator import generate_insight, suggest_followups
    from src.data_loader import CONSTANTS, VALID_VALUES, get_dataframe
    from src.judge import judge_response 
except ModuleNotFoundError:
    from query_parser import parse_query
    from analytics_engine import (
        run_query,
        _grouped_failure_rate,
        _grouped_flag_rate,
        _apply_filters,
    )
    from insight_generator import generate_insight, suggest_followups
    from data_loader import CONSTANTS, VALID_VALUES, get_dataframe
    from judge import judge_response

load_dotenv()

_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MODEL = "gemini-3.1-pro-preview"

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

MAX_DIMENSIONS = 4

INVESTIGABLE_DIMENSIONS = [
    "sender_state",
    "transaction_type",
    "sender_bank",
    "network_type",
    "device_type",
    "sender_age_group",
    "merchant_category",
    "day_of_week",
    "is_weekend",
]

DIM_LABELS = {
    "sender_state":      "state",
    "transaction_type":  "transaction type",
    "sender_bank":       "sender bank",
    "network_type":      "network type",
    "device_type":       "device type",
    "sender_age_group":  "age group",
    "merchant_category": "merchant category",
    "day_of_week":       "day of week",
    "is_weekend":        "weekend vs weekday",
}

AGENTIC_TRIGGERS = [
    "why", "what causes", "what drives", "reason",
    "root cause", "explain", "what is behind",
    "what factor", "what is causing", "deep dive",
    "investigate", "diagnose", "how come",
]


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------

def run_agent(user_query: str, conversation_context: dict = None) -> dict:
    """
    Main entry point. Routes to single-pass or agentic mode.

    Returns
    -------
    dict with keys:
        response  : str   — final narrative
        result    : dict  — primary analytics result
        followups : list  — suggested follow-up questions
        mode      : str   — "single_pass" or "agentic"
        steps     : list  — investigation steps (agentic only)
        synthesis : str   — synthesised narrative (agentic only)
    """
    parsed = parse_query(user_query, conversation_context)

    if _should_use_agentic(user_query):
        return _run_agentic(user_query, parsed)
    else:
        return _run_single_pass(user_query, parsed)


# ---------------------------------------------------------------------------
# MODE DECISION
# ---------------------------------------------------------------------------

def _should_use_agentic(user_query: str) -> bool:
    """Return True if the query warrants multi-dimensional investigation."""
    q = user_query.lower()
    return any(trigger in q for trigger in AGENTIC_TRIGGERS)


# ---------------------------------------------------------------------------
# SINGLE PASS
# ---------------------------------------------------------------------------

def _run_single_pass(user_query: str, parsed: dict) -> dict:
    result    = run_query(parsed)
    response  = generate_insight(result)

    # Judge validates before reaching user
    verdict   = judge_response(user_query, response, result=result)
    response  = verdict["final_response"]

    followups = suggest_followups(result)

    return {
        "response":  response,
        "result":    result,
        "followups": followups,
        "mode":      "single_pass",
        "steps":     [],
        "synthesis": None,
        "verdict":   verdict,
    }


# ---------------------------------------------------------------------------
# AGENTIC ROOT CAUSE ANALYSIS
# ---------------------------------------------------------------------------

def _run_agentic(user_query: str, parsed: dict) -> dict:
    """
    Run a deterministic multi-dimensional investigation.

    Steps:
        1. Identify subject entity & base filters
        2. Run failure_rate grouped by each of N dimensions via pandas
        3. Rank by explanatory spread
        4. LLM synthesises findings into root cause narrative
    """
    df = get_dataframe()

    # Extract any base filters (e.g. is_weekend) to apply across all steps
    base_filters = _extract_base_filters(parsed)

    # Identify what the question is fundamentally about
    subject_dim = _identify_subject_dimension(parsed, user_query)

    # Select which dimensions to investigate
    dims_to_investigate = _select_dimensions(subject_dim, base_filters)

    # Run reference step: show all values of the subject dimension
    steps = []
    if subject_dim:
        ref_step = _run_dimension_analysis(df, subject_dim, 0, {})
        if ref_step:
            ref_step["role"] = "reference"
            steps.append(ref_step)

    # Run cross-dimensional investigation steps
    for i, dim in enumerate(dims_to_investigate, start=1):
        step = _run_dimension_analysis(df, dim, i, base_filters)
        if step:
            steps.append(step)

    # Get primary result for UI metrics strip
    primary_result = run_query(parsed)

    if len(steps) <= 1:
        # Not enough steps — fall back to single pass
        return _run_single_pass(user_query, parsed)

    # Synthesise all findings
    synthesis = _synthesise(user_query, steps, subject_dim)

    # Judge validates the synthesis
    verdict   = judge_response(user_query, synthesis, observations=steps)
    synthesis = verdict["final_response"]

    followups = _agentic_followups(subject_dim, dims_to_investigate)

    return {
        "response":  synthesis,
        "result":    primary_result,
        "followups": followups,
        "mode":      "agentic",
        "steps":     steps,
        "synthesis": synthesis,
    }


# ---------------------------------------------------------------------------
# DIMENSION ANALYSIS — deterministic pandas computation
# ---------------------------------------------------------------------------

def _run_dimension_analysis(
    df,
    dimension: str,
    step_num: int,
    base_filters: dict,
) -> dict | None:
    """
    Compute failure rate grouped by a single dimension.
    Returns a structured observation dict or None on failure.
    """
    try:
        working_df = df.copy()

        # Apply base filters
        for col, val in base_filters.items():
            if col in working_df.columns and val is not None:
                working_df = working_df[working_df[col] == val]

        # merchant_category only valid for P2M
        if dimension == "merchant_category":
            working_df = working_df[working_df["transaction_type"] == "P2M"]

        if len(working_df) < 200:
            return None

        result_df = _grouped_failure_rate(working_df, dimension)

        if result_df.empty or len(result_df) < 2:
            return None

        spread = round(
            result_df["failure_rate_pct"].max() -
            result_df["failure_rate_pct"].min(), 2
        )
        highest = result_df.iloc[0]
        lowest  = result_df.iloc[-1]

        if spread >= 2.0:
            strength = "strong"
        elif spread >= 0.75:
            strength = "moderate"
        elif spread >= 0.3:
            strength = "weak"
        else:
            strength = "negligible"

        return {
            "step_num":   step_num,
            "dimension":  dimension,
            "dim_label":  DIM_LABELS.get(dimension, dimension),
            "data":       result_df,
            "spread":     spread,
            "strength":   strength,
            "highest": {
                "segment":      str(highest[dimension]),
                "failure_rate": float(highest["failure_rate_pct"]),
                "total":        int(highest["total"]),
                "failed":       int(highest["failed"]),
            },
            "lowest": {
                "segment":      str(lowest[dimension]),
                "failure_rate": float(lowest["failure_rate_pct"]),
                "total":        int(lowest["total"]),
                "failed":       int(lowest["failed"]),
            },
            "key_finding": (
                f"{DIM_LABELS.get(dimension, dimension).title()}: "
                f"highest = {highest[dimension]} at "
                f"{highest['failure_rate_pct']}% "
                f"({int(highest['failed'])}/{int(highest['total'])}), "
                f"lowest = {lowest[dimension]} at "
                f"{lowest['failure_rate_pct']}% "
                f"({int(lowest['failed'])}/{int(lowest['total'])}), "
                f"spread = {spread}pp [{strength} explanatory power]"
            ),
            "table_str":  result_df.to_string(index=False),
            "role":       "investigation",
        }

    except Exception:
        return None


# ---------------------------------------------------------------------------
# SYNTHESIS
# ---------------------------------------------------------------------------

_SYNTHESIS_SYSTEM = f"""
You are InsightX, a senior business analytics assistant for a digital payments platform.
You have completed a multi-dimensional root cause investigation.
Synthesise ALL findings into one executive-readable D-S-I-R response.

OVERALL PLATFORM BASELINES (for context):
- Overall failure rate: {CONSTANTS['OVERALL_FAILURE_RATE']}%
- Overall fraud flag rate: {CONSTANTS['OVERALL_FLAG_RATE']}%

D-S-I-R STRUCTURE:
- Direct Answer: One sentence naming the most likely root cause dimension
- Supporting Metrics: Numbers from MULTIPLE steps with denominators
- Interpretation: Which dimension has the highest spread?
  Is it strong enough to explain the pattern?
  If all spreads are small (<0.5pp), say honestly this is a synthetically
  uniform dataset with no strong root cause visible in the data.
- Recommendation: One actionable next step

CRITICAL RULES:
1. Use ONLY the numbers provided. Never invent statistics.
2. "Explanatory power" = spread in failure rates across a dimension.
   Highest spread = most likely root cause.
3. Explicitly state which dimension best explains the pattern and why.
4. Use "marginally" for <0.5pp, "notably" for 0.5-2pp, "significantly" for >2pp.
5. No bullet points. Clean paragraphs. 200-300 words maximum.
6. Never say "fraud" — say "flagged for review".
7. Professional, direct tone for business leaders.
"""


def _synthesise(
    original_query: str,
    steps: list[dict],
    subject_dim: str | None,
) -> str:
    """Ask Gemini to synthesise all dimensional findings into a narrative."""

    reference = [s for s in steps if s.get("role") == "reference"]
    investigation = [s for s in steps if s.get("role") != "reference"]
    investigation.sort(key=lambda x: x["spread"], reverse=True)

    findings_text = ""

    # Reference step first
    if reference:
        ref = reference[0]
        findings_text += (
            f"REFERENCE — All {ref['dim_label']}s "
            f"(shows where the anomaly sits):\n"
            f"{ref['table_str']}\n\n"
        )

    # Investigation steps sorted by explanatory power
    for s in investigation:
        findings_text += (
            f"INVESTIGATION — By {s['dim_label'].upper()} "
            f"(spread={s['spread']}pp, {s['strength']} explanatory power):\n"
            f"{s['table_str']}\n"
            f"Key finding: {s['key_finding']}\n\n"
        )

    # Tell Gemini which dimension is best
    if investigation:
        best = investigation[0]
        best_note = (
            f"BEST EXPLAINING DIMENSION: {best['dim_label']} "
            f"with {best['spread']}pp spread ({best['strength']})"
        )
    else:
        best_note = "No investigation dimensions available."

    prompt = f"""{_SYNTHESIS_SYSTEM}

ORIGINAL QUESTION: {original_query}

INVESTIGATION FINDINGS:
{findings_text}
{best_note}

Write the D-S-I-R synthesis now.
"""

    try:
        response = _client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )
        return response.text.strip()
    except Exception:
        return _fallback_synthesis(original_query, steps)


# ---------------------------------------------------------------------------
# HELPER UTILITIES
# ---------------------------------------------------------------------------

def _extract_base_filters(parsed: dict) -> dict:
    """Keep only temporal/contextual filters for application across all steps."""
    filters = parsed.get("filters", {}) or {}
    keep = ["is_weekend", "hour_of_day"]
    return {k: v for k, v in filters.items() if k in keep and v is not None}


def _identify_subject_dimension(parsed: dict, user_query: str) -> str | None:
    """Identify which dimension the user is fundamentally asking about."""
    filters = parsed.get("filters", {}) or {}
    group_by = parsed.get("group_by")

    entity_dims = [
        "sender_state", "transaction_type", "sender_bank",
        "network_type", "device_type", "sender_age_group",
        "merchant_category",
    ]

    for dim in entity_dims:
        if dim in filters and filters[dim]:
            return dim

    if group_by in entity_dims:
        return group_by

    # Infer from query text
    q = user_query.lower()
    if any(s.lower() in q for s in VALID_VALUES["sender_state"]):
        return "sender_state"
    if any(t.lower() in q for t in VALID_VALUES["transaction_type"]):
        return "transaction_type"
    if any(b.lower() in q for b in VALID_VALUES["sender_bank"]):
        return "sender_bank"
    if any(n.lower() in q for n in VALID_VALUES["network_type"]):
        return "network_type"

    return None


def _select_dimensions(
    subject_dim: str | None,
    base_filters: dict,
) -> list[str]:
    """Select investigation dimensions, excluding subject and already-filtered dims."""
    priority = [
        "network_type",
        "transaction_type",
        "sender_bank",
        "device_type",
        "sender_age_group",
        "sender_state",
        "day_of_week",
        "is_weekend",
    ]

    selected = []
    for dim in priority:
        if dim == subject_dim:
            continue
        if dim in base_filters:
            continue
        selected.append(dim)
        if len(selected) >= MAX_DIMENSIONS:
            break

    return selected


def _agentic_followups(
    subject_dim: str | None,
    investigated: list[str],
) -> list[str]:
    """Generate targeted follow-up suggestions."""
    all_labels = list(DIM_LABELS.values())
    investigated_labels = [DIM_LABELS.get(d, d) for d in investigated]
    unexplored = [d for d in all_labels if d not in investigated_labels]

    suggestions = []
    if unexplored:
        suggestions.append(f"Explore this further by {unexplored[0]}")
    if subject_dim:
        label = DIM_LABELS.get(subject_dim, subject_dim)
        suggestions.append(f"How does the fraud flag rate vary by {label}?")
    suggestions.append("Which time of day shows the highest failure rate?")
    return suggestions[:3]


def _fallback_synthesis(original_query: str, steps: list[dict]) -> str:
    """Plain-text fallback if Gemini synthesis call fails."""
    lines = [f'Root cause analysis for: "{original_query}"\n']
    investigation = sorted(
        [s for s in steps if s.get("role") != "reference"],
        key=lambda x: x.get("spread", 0),
        reverse=True
    )
    for s in investigation:
        lines.append(
            f"• {s['dim_label'].title()}: spread={s['spread']}pp "
            f"({s['strength']}) — "
            f"highest={s['highest']['segment']} "
            f"at {s['highest']['failure_rate']}%"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# UI TRACE FORMATTER
# ---------------------------------------------------------------------------

def format_investigation_trace(steps: list[dict]) -> str:
    """Format investigation steps for the Streamlit expander."""
    if not steps:
        return ""

    lines = []
    reference = [s for s in steps if s.get("role") == "reference"]
    investigation = sorted(
        [s for s in steps if s.get("role") != "reference"],
        key=lambda x: x.get("spread", 0),
        reverse=True
    )

    if reference:
        ref = reference[0]
        lines.append(
            f"**📌 Reference — {ref['dim_label'].title()}** "
            f"(establishes baseline comparison)"
        )
        lines.append(f"↳ {ref['key_finding']}\n")

    for s in investigation:
        lines.append(
            f"**🔍 Step {s['step_num']} — {s['dim_label'].title()}** "
            f"(spread: {s['spread']}pp — {s['strength']} explanatory power)"
        )
        lines.append(f"↳ {s['key_finding']}\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_cases = [
        ("Why does Uttar Pradesh have a higher failure rate than other states?", True),
        ("Why do Recharge transactions fail more than other types?",             True),
       # ("What is the average transaction amount for bill payments?",            False),
    ]

    for query, expect_agentic in test_cases:
        print("\n" + "=" * 60)
        print(f"Query   : {query}")
        print(f"Expected: {'AGENTIC' if expect_agentic else 'SINGLE PASS'}")
        print("=" * 60)

        result = run_agent(query)

        print(f"Actual  : {result['mode'].upper()}")
        print(f"Steps   : {len(result['steps'])}")

        if result["steps"]:
            print("\n--- Investigation Trace ---")
            print(format_investigation_trace(result["steps"]))

        print(f"\n--- Response ---\n{result['response']}")

        if result["followups"]:
            print("\n--- Follow-ups ---")
            for f in result["followups"]:
                print(f"  → {f}")