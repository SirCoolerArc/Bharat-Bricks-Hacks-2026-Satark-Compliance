"""
Layer 1 — Query Router
Classifies incoming queries into DATA, REGULATORY, or HYBRID.
Uses keyword heuristics + fallback pattern matching (no LLM call needed).
"""

from enum import Enum


class QueryType(str, Enum):
    DATA = "DATA"
    REGULATORY = "REGULATORY"
    HYBRID = "HYBRID"


# Keywords that indicate data/statistics questions
DATA_KEYWORDS = [
    "fraud rate", "fraud volume", "transactions", "states", "state",
    "scam type", "lottery", "impersonation", "investment", "kyc",
    "tech_support", "emergency", "job", "complaints", "resolution",
    "resolved", "escalated", "open", "average", "highest", "lowest",
    "peak", "heatmap", "hourly", "weekend", "sunday", "bank",
    "trend", "count", "total", "risk", "high risk", "medium risk",
    "low risk", "sla", "breach", "days", "volume", "amount",
    "maharashtra", "arunachal", "manipur", "meghalaya", "assam",
    "bihar", "jharkhand", "nagaland", "himachal", "tripura", "sikkim",
    "how many", "what is", "which", "top", "bottom", "compare",
    "percentage", "rate", "distribution", "breakdown",
]

# Keywords that indicate regulatory/compliance questions
REGULATORY_KEYWORDS = [
    "rbi", "npci", "regulation", "circular", "guideline", "compliance",
    "compliant", "direction", "master direction", "kyc norms",
    "reporting requirement", "mandate", "penalty", "notice",
    "show cause", "directive", "rule", "framework", "policy",
    "act", "section", "clause", "requirement", "obligation",
    "threshold", "limit", "prescribed", "stipulated", "per rbi",
    "as per", "according to", "legally", "regulatory",
    "permitted", "prohibited", "allowed", "required",
    "entitled", "entitlement", "reversal", "settlement", "compensation",
    "liability", "refund", "time limit", "tat", "turnaround",
    "merchant", "customer", "dispute", "resolution", "legal",
]


def classify_query(query: str) -> QueryType:
    """
    Classify a natural language query into DATA, REGULATORY, or HYBRID.
    Uses keyword overlap scoring — no LLM call needed for routing.
    """
    q = query.lower().strip()

    data_score = sum(1 for kw in DATA_KEYWORDS if kw in q)
    reg_score = sum(1 for kw in REGULATORY_KEYWORDS if kw in q)

    has_data = data_score >= 1
    has_reg = reg_score >= 1

    if has_data and has_reg:
        return QueryType.HYBRID
    elif has_reg:
        return QueryType.REGULATORY
    elif has_data:
        return QueryType.DATA

    # Fallback: if the query contains a question mark and mentions numbers/statistics
    if any(char.isdigit() for char in q) or "%" in q:
        return QueryType.DATA

    # Default to DATA for general questions (most compliance officer queries)
    return QueryType.DATA
