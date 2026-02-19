"""
query_parser.py — InsightX Analytics Engine
============================================
Responsible for converting natural language queries into structured
intent dictionaries that analytics_engine.py can consume directly.

Pipeline:
    raw user query (str)
        → Gemini API (returns JSON only)
        → parsed intent (dict)
        → validated & normalised intent (dict)
        → analytics_engine.py

The LLM's job here is ONLY to parse — it never computes numbers.
All computation happens downstream in analytics_engine.py.
"""

import os
import json
import re
from google import genai
from dotenv import load_dotenv
try:
    from src.data_loader import VALID_VALUES, CONSTANTS
except ModuleNotFoundError:
    from data_loader import VALID_VALUES, CONSTANTS

load_dotenv()

# ---------------------------------------------------------------------------
# GEMINI SETUP
# ---------------------------------------------------------------------------
_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# ---------------------------------------------------------------------------
# INTENT TYPES
# ---------------------------------------------------------------------------
INTENT_TYPES = [
    "descriptive",   # What is / how many / show me
    "comparative",   # Compare X vs Y / which is higher
    "temporal",      # Peak hours / trends / weekend patterns
    "segmentation",  # Which group / broken down by / most frequently
    "correlation",   # Is X related to Y / does X affect Y
    "risk",          # Flagged / fraud / high-value / anomalous
]

# ---------------------------------------------------------------------------
# METRIC TYPES
# ---------------------------------------------------------------------------
METRIC_TYPES = [
    "failure_rate",       # FAILED / total × 100
    "success_rate",       # SUCCESS / total × 100
    "transaction_count",  # raw count or volume share
    "average_amount",     # mean(amount_inr)
    "median_amount",      # median(amount_inr)
    "fraud_flag_rate",    # fraud_flag=1 / total × 100
    "total_volume",       # sum(amount_inr)
    "peak_hours",         # groupby hour_of_day by count
    "trend",              # metric over time buckets
]

# ---------------------------------------------------------------------------
# SYSTEM PROMPT FOR GEMINI
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = f"""
You are a query parser for a digital payments analytics system.
Your ONLY job is to convert a natural language query into a structured JSON object.
You must NEVER answer the question — only parse it.
You must ALWAYS return valid JSON and nothing else. No explanation, no markdown, no preamble.

The dataset contains UPI transaction data with these columns and valid values:

TRANSACTION TYPES: {VALID_VALUES['transaction_type']}
MERCHANT CATEGORIES: {VALID_VALUES['merchant_category']}
AGE GROUPS: {VALID_VALUES['sender_age_group']}
STATES: {VALID_VALUES['sender_state']}
BANKS: {VALID_VALUES['sender_bank']}
DEVICE TYPES: {VALID_VALUES['device_type']}
NETWORK TYPES: {VALID_VALUES['network_type']}
DAYS OF WEEK: {VALID_VALUES['day_of_week']}

SYSTEM CONSTANTS (use these exact values when relevant):
- High-value threshold (P90): ₹{CONSTANTS['HIGH_VALUE_THRESHOLD']}
- Overall failure rate baseline: {CONSTANTS['OVERALL_FAILURE_RATE']}%
- Overall fraud flag rate: {CONSTANTS['OVERALL_FLAG_RATE']}%
- Peak hour: {CONSTANTS['PEAK_HOUR']}:00

Return ONLY a JSON object with this exact structure:
{{
    "intent": <one of: descriptive | comparative | temporal | segmentation | correlation | risk>,
    "metric": <one of: failure_rate | success_rate | transaction_count | average_amount | median_amount | fraud_flag_rate | total_volume | peak_hours | trend>,
    "filters": {{
        // Only include filters that are explicitly mentioned in the query.
        // Use null for any filter not mentioned.
        // Examples of valid filter keys:
        //   "transaction_type": "P2P"            (single value)
        //   "sender_bank": ["HDFC", "SBI"]        (list for comparisons)
        //   "device_type": "Android"
        //   "network_type": "4G"
        //   "sender_age_group": "26-35"
        //   "sender_state": "Maharashtra"
        //   "merchant_category": "Food"
        //   "is_weekend": 1                       (1=weekend, 0=weekday)
        //   "hour_of_day": 19
        //   "transaction_status": "FAILED"
        //   "is_high_value": true                 (amount >= P90 threshold)
    }},
    "group_by": <column name to group results by, or null if not a comparison/segmentation>,
    "time_scope": <"hourly" | "daily" | "weekly" | "weekend_vs_weekday" | null>,
    "comparison_values": <list of values being compared, or null>,
    "assumptions": <list of strings describing any assumptions made, or []>,
    "ambiguous": <true if query is unclear and assumptions were required, false otherwise>,
    "raw_query": <the original query string, unchanged>
}}

RULES:
1. "filters" should only contain keys for dimensions explicitly mentioned in the query.
2. For comparative queries (X vs Y), put both values in "comparison_values" AND as a list in filters.
3. "group_by" should be the column that the comparison or segmentation is over.
4. If the query mentions "weekend", set is_weekend: 1 in filters.
5. If the query mentions "weekday", set is_weekend: 0 in filters.
6. If the query asks about "high value" transactions, set is_high_value: true in filters.
7. If a query mentions a bank without specifying sender/receiver, assume sender_bank.
8. If the query is about merchant categories, it implicitly filters to P2M transactions.
9. State any assumptions you made in the "assumptions" list.
10. If genuinely ambiguous (multiple valid interpretations), set ambiguous: true.
"""

# ---------------------------------------------------------------------------
# MAIN PARSE FUNCTION
# ---------------------------------------------------------------------------
def parse_query(user_query: str, conversation_context: dict = None) -> dict:
    """
    Parse a natural language query into a structured intent dictionary.

    Parameters
    ----------
    user_query : str
        The raw natural language query from the user.
    conversation_context : dict, optional
        The current conversation state (active filters, last metric, etc.)
        from conversation_manager.py. Used to resolve follow-up queries.

    Returns
    -------
    dict
        Structured intent dictionary with keys:
        intent, metric, filters, group_by, time_scope,
        comparison_values, assumptions, ambiguous, raw_query
    """
    # Build the prompt
    prompt = _build_prompt(user_query, conversation_context)

    # Call Gemini
    raw_response = _call_gemini(prompt)

    # Parse and validate the JSON response
    parsed = _parse_response(raw_response, user_query)

    # Post-process: normalise values against VALID_VALUES
    parsed = _normalise_entities(parsed)

    return parsed


def _build_prompt(user_query: str, context: dict = None) -> str:
    """
    Build the full prompt sent to Gemini.
    Injects conversation context if available to handle follow-up queries.
    """
    context_block = ""
    if context and context.get("last_metric"):
        context_block = f"""
CONVERSATION CONTEXT (use this to resolve follow-up queries):
- Last metric discussed: {context.get('last_metric')}
- Last segment discussed: {context.get('last_segment')}
- Active filters from previous turn: {json.dumps(context.get('active_filters', {}))}

If the current query is a follow-up (e.g. "break that down by state", "compare with weekends",
"now look at only P2M"), inherit the relevant context from above.
"""

    return f"""{_SYSTEM_PROMPT}

{context_block}

USER QUERY: {user_query}

Return only the JSON object. No other text.
"""


def _call_gemini(prompt: str) -> str:
    """
    Send prompt to Gemini and return the raw text response.
    Handles API errors gracefully.
    """
    try:
        response = _client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        raise RuntimeError(f"Gemini API call failed: {e}")


def _parse_response(raw_response: str, original_query: str) -> dict:
    """
    Extract and parse JSON from Gemini's response.
    Handles cases where the model accidentally wraps output in markdown fences.
    """
    # Strip markdown code fences if present (```json ... ```)
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw_response).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        # If parsing fails, return a safe fallback with the error noted
        return _fallback_intent(original_query, error=str(e))

    # Ensure raw_query is always set
    if "raw_query" not in parsed:
        parsed["raw_query"] = original_query

    # Ensure assumptions is always a list
    if "assumptions" not in parsed or parsed["assumptions"] is None:
        parsed["assumptions"] = []

    return parsed


def _normalise_entities(parsed: dict) -> dict:
    """
    Validate extracted entities against VALID_VALUES.
    Corrects minor capitalisation issues and flags unrecognised values.
    """
    filters = parsed.get("filters", {}) or {}
    warnings = []

    # Build a case-insensitive lookup for each valid values list
    lookups = {
        col: {v.lower(): v for v in vals}
        for col, vals in VALID_VALUES.items()
    }

    for key, value in list(filters.items()):
        if key not in lookups:
            continue  # Not a categorical column — skip

        if isinstance(value, list):
            normalised = []
            for v in value:
                match = lookups[key].get(str(v).lower())
                if match:
                    normalised.append(match)
                else:
                    warnings.append(f"Unrecognised value '{v}' for '{key}' — removed")
            filters[key] = normalised if normalised else None
        else:
            match = lookups[key].get(str(value).lower())
            if match:
                filters[key] = match
            else:
                warnings.append(f"Unrecognised value '{value}' for '{key}' — removed")
                filters[key] = None

    parsed["filters"] = filters

    if warnings:
        parsed["assumptions"] = parsed.get("assumptions", []) + warnings

    return parsed


def _fallback_intent(original_query: str, error: str = "") -> dict:
    """
    Return a safe fallback intent when parsing fails completely.
    The analytics engine checks for intent == 'unknown' and
    returns a graceful error message to the user.
    """
    return {
        "intent": "unknown",
        "metric": None,
        "filters": {},
        "group_by": None,
        "time_scope": None,
        "comparison_values": None,
        "assumptions": [f"Query could not be parsed: {error}"],
        "ambiguous": True,
        "raw_query": original_query,
    }


# ---------------------------------------------------------------------------
# UTILITY: pretty-print a parsed intent (useful for debugging)
# ---------------------------------------------------------------------------
def explain_parse(parsed: dict) -> str:
    """
    Return a human-readable explanation of what was parsed.
    Used in notebooks and during development to verify parser output.
    """
    lines = [
        f"Query    : {parsed.get('raw_query')}",
        f"Intent   : {parsed.get('intent')}",
        f"Metric   : {parsed.get('metric')}",
        f"Filters  : {json.dumps(parsed.get('filters', {}), indent=2)}",
        f"Group by : {parsed.get('group_by')}",
        f"Time     : {parsed.get('time_scope')}",
        f"Compare  : {parsed.get('comparison_values')}",
        f"Ambiguous: {parsed.get('ambiguous')}",
    ]
    if parsed.get("assumptions"):
        lines.append("Assumptions:")
        for a in parsed["assumptions"]:
            lines.append(f"  → {a}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_queries = [
        # IMPORTANT:Only one is left uncommented to avoid hitting API limits during development 
        # — add more as needed!

        #"What is the failure rate for P2M transactions on weekends?",
        #"Which transaction type has the highest failure rate?",
       # "Compare failure rates for HDFC vs SBI on weekends",
        "What are the peak transaction hours for food delivery?",
       #"Which age group uses P2P most frequently on weekends?",
        #"What percentage of high-value transactions are flagged for review?",
        #"Is there a relationship between network type and transaction success?",
    ]

    for q in test_queries:
        print("\n" + "="*60)
        result = parse_query(q)
        print(explain_parse(result))