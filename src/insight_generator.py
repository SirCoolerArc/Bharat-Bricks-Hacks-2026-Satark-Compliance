"""
insight_generator.py — InsightX Analytics Engine
=================================================
Responsible for converting structured analytics results into
clear, executive-readable D-S-I-R narratives using Gemini.

D - Direct Answer
S - Supporting Metrics
I - Interpretation
R - Recommendation (where appropriate)

CRITICAL PRINCIPLE:
    The LLM receives ONLY pre-computed numbers from analytics_engine.py.
    It never computes, infers, or recalls statistics from memory.
    Its only job is to convert numbers into readable language.

Pipeline:
    analytics_engine result (dict)
        → _build_narrative_prompt()
        → Gemini API
        → formatted D-S-I-R response (str)

Usage:
    from src.insight_generator import generate_insight
    response = generate_insight(analytics_result)
"""

import os
import json
from google import genai
from dotenv import load_dotenv

try:
    from src.data_loader import CONSTANTS
except ModuleNotFoundError:
    from data_loader import CONSTANTS

load_dotenv()

# ---------------------------------------------------------------------------
# GEMINI SETUP
# ---------------------------------------------------------------------------
_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MODEL = "gemini-2.5-flash"

# ---------------------------------------------------------------------------
# SYSTEM PROMPT
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """
You are InsightX, a senior business analytics assistant for a digital payments platform.
Your role is to convert pre-computed data results into clear, executive-readable insights.

CRITICAL RULES:
1. You ONLY use the numbers provided in the data result. NEVER invent, recall, or estimate statistics.
2. Always follow the D-S-I-R structure (defined below).
3. Be honest about small differences — do not exaggerate insights.
4. Always mention the baseline (overall average) when comparing segments.
5. If a warning or assumption is provided, include it naturally in your response.
6. Keep the tone professional but conversational — this is for business leaders, not data scientists.
7. Never use bullet points. Write in clean paragraphs.
8. Keep responses concise — 150 to 250 words maximum.

D-S-I-R STRUCTURE:
- Direct Answer: One sentence directly answering the question.
- Supporting Metrics: The key numbers with denominators (e.g. "638 out of 12,527").
- Interpretation: What the pattern means in business context. Be honest if differences are small.
- Recommendation: One actionable next step. Skip if the data does not support a meaningful recommendation.

TONE GUIDELINES:
- For small differences (<0.5pp): use "marginally", "slightly", "negligible difference"
- For moderate differences (0.5–2pp): use "notably", "meaningfully"  
- For large differences (>2pp): use "significantly", "considerably"
- Never say "dramatically" unless the spread is above 3 percentage points.
- Never confirm fraud — always say "flagged for review" not "fraudulent".
"""

# ---------------------------------------------------------------------------
# MAIN FUNCTION
# ---------------------------------------------------------------------------

def generate_insight(result: dict) -> str:
    """
    Generate a D-S-I-R narrative from an analytics engine result.

    Parameters
    ----------
    result : dict
        Output from analytics_engine.run_query()

    Returns
    -------
    str
        Formatted narrative response ready to display to the user.
    """
    if not result.get("success"):
        return f"I wasn't able to answer that question. {result.get('error', 'Please try rephrasing.')}"

    prompt = _build_narrative_prompt(result)

    try:
        response = _client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        narrative = response.text.strip()
    except Exception as e:
        # Fallback to a structured plain-text response if Gemini fails
        narrative = _fallback_narrative(result)

    # Append assumption disclosure if present
    assumption = result.get("assumption")
    if assumption:
        narrative += f"\n\n*{assumption}*"

    # Append warning if present
    warning = result.get("warning")
    if warning and isinstance(warning, str):
        narrative += f"\n\n{warning}"

    return narrative


# ---------------------------------------------------------------------------
# PROMPT BUILDER
# ---------------------------------------------------------------------------

def _build_narrative_prompt(result: dict) -> str:
    """
    Build the prompt sent to Gemini.
    Injects only computed numbers — never asks the model to recall statistics.
    """
    summary = result.get("summary", {})
    data = result.get("data")
    intent = result.get("intent")
    metric = result.get("metric")
    raw_query = result.get("raw_query", "")
    filters = result.get("filters_applied", {})
    parser_assumptions = result.get("assumptions_from_parser", [])

    # Serialise the data table if present
    data_str = ""
    if data is not None and hasattr(data, "to_string"):
        data_str = f"\nFULL DATA TABLE:\n{data.to_string(index=False)}\n"

    # Serialise parser assumptions
    assumptions_str = ""
    if parser_assumptions:
        assumptions_str = f"\nASSUMPTIONS MADE DURING PARSING:\n" + \
                          "\n".join(f"  - {a}" for a in parser_assumptions)

    # Serialise active filters
    filter_str = ""
    active = {k: v for k, v in (filters or {}).items() if v is not None}
    if active:
        filter_str = f"\nFILTERS APPLIED: {json.dumps(active)}"

    prompt = f"""{_SYSTEM_PROMPT}

USER'S QUESTION: {raw_query}

QUERY CONTEXT:
  Intent type: {intent}
  Metric: {metric}
{filter_str}
{assumptions_str}

PRE-COMPUTED RESULTS (use ONLY these numbers):
SUMMARY:
{json.dumps(summary, indent=2)}
{data_str}

Now write a D-S-I-R response to the user's question using only the numbers above.
Do not add any statistics that are not in the data provided.
"""
    return prompt


# ---------------------------------------------------------------------------
# FALLBACK NARRATIVE (if Gemini call fails)
# ---------------------------------------------------------------------------

def _fallback_narrative(result: dict) -> str:
    """
    Generate a plain structured response without the LLM.
    Used as a safety net if the Gemini API is unavailable.
    """
    summary = result.get("summary", {})
    raw_query = result.get("raw_query", "your query")
    intent = result.get("intent", "")
    data = result.get("data")

    lines = [f"Here are the results for: \"{raw_query}\"\n"]

    # Pull key fields from summary
    if "highest" in summary:
        h = summary["highest"]
        lines.append(f"Highest: {h.get('segment')} at {h.get('value')}%")
    if "lowest" in summary:
        l = summary["lowest"]
        lines.append(f"Lowest: {l.get('segment')} at {l.get('value')}%")
    if "spread" in summary:
        lines.append(f"Spread: {summary['spread']} percentage points")
    if "baseline_failure_rate" in summary:
        lines.append(f"Overall baseline: {summary['baseline_failure_rate']}%")
    if "metric_value" in summary:
        lines.append(f"{summary.get('metric_label', 'Value')}: {summary['metric_value']} {summary.get('unit', '')}")
    if "interpretation" in summary:
        lines.append(f"\n{summary['interpretation']}")
    if "caution" in summary:
        lines.append(f"\n{summary['caution']}")

    # Add data table if available
    if data is not None and hasattr(data, "to_string"):
        lines.append(f"\nData:\n{data.to_string(index=False)}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# FOLLOW-UP SUGGESTION GENERATOR
# ---------------------------------------------------------------------------

def suggest_followups(result: dict) -> list[str]:
    """
    Generate 2-3 context-aware follow-up question suggestions.
    These are shown to the user after each response to guide exploration.

    Returns a list of suggested question strings.
    """
    intent = result.get("intent", "")
    group_by = result.get("group_by")
    filters = result.get("filters_applied", {}) or {}
    metric = result.get("metric", "")

    suggestions = []

    # Drill-down suggestions
    if group_by and group_by != "sender_state":
        suggestions.append(f"Break this down by state")
    if group_by and group_by != "sender_age_group":
        suggestions.append(f"How does this vary by age group?")

    # Temporal suggestions
    if "is_weekend" not in filters:
        suggestions.append("Does this change on weekends vs weekdays?")
    elif filters.get("is_weekend") == 1:
        suggestions.append("How does this compare on weekdays?")

    # Risk follow-up
    if intent != "risk" and metric == "failure_rate":
        suggestions.append("Are failed transactions more likely to be flagged for review?")

    # Comparative follow-up
    if intent == "comparative" and group_by == "transaction_type":
        suggestions.append("Which merchant categories have the highest failure rates?")

    # Trim to 3 max
    return suggestions[:3]


# ---------------------------------------------------------------------------
# Quick self-test — run from project root: python -m src.insight_generator
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        from src.analytics_engine import run_query
        from src.query_parser import parse_query
    except ModuleNotFoundError:
        from analytics_engine import run_query
        from query_parser import parse_query

    # Test with a single query to avoid API rate limits
    test_query = "Which transaction type has the highest failure rate?"

    print("=" * 60)
    print(f"Query: {test_query}")
    print("=" * 60)

    parsed = parse_query(test_query)
    result = run_query(parsed)
    response = generate_insight(result)

    print("\nINSIGHT RESPONSE:")
    print(response)

    followups = suggest_followups(result)
    if followups:
        print("\nSUGGESTED FOLLOW-UPS:")
        for f in followups:
            print(f"  → {f}")