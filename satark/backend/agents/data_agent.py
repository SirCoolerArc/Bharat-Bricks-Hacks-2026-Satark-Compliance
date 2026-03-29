"""
Layer 2A — Data Agent
Provides structured data context from gold tables for DATA and HYBRID queries.
Performs lightweight filtering to provide only relevant table subsets.
"""

import json
from data.gold_tables import (
    GEO_HEATMAP,
    RISK_DISTRIBUTION,
    SCAM_TAXONOMY,
    ALERT_EFFECTIVENESS,
    HOURLY_FRAUD_PATTERN,
    get_full_data_context,
)


def _detect_relevant_tables(query: str) -> list[str]:
    """Determine which gold tables are most relevant to the query."""
    q = query.lower()
    tables = []

    # Geographic / state-related
    state_keywords = [
        "state", "geographic", "map", "maharashtra", "arunachal",
        "manipur", "meghalaya", "assam", "bihar", "region", "northeast",
    ]
    if any(kw in q for kw in state_keywords):
        tables.append("geo_heatmap")

    # Risk distribution
    risk_keywords = ["risk", "high risk", "medium risk", "low risk", "tier", "model"]
    if any(kw in q for kw in risk_keywords):
        tables.append("risk_distribution")

    # Scam taxonomy
    scam_keywords = [
        "scam", "lottery", "impersonation", "investment", "kyc",
        "tech_support", "emergency", "job", "fraud type", "scam type",
        "loss", "category",
    ]
    if any(kw in q for kw in scam_keywords):
        tables.append("scam_taxonomy")

    # Alert effectiveness / complaints
    complaint_keywords = [
        "complaint", "resolution", "resolved", "escalated", "open",
        "sla", "bank", "performance", "effectiveness", "alert",
        "breach", "days",
    ]
    if any(kw in q for kw in complaint_keywords):
        tables.append("alert_effectiveness")

    # Temporal patterns
    time_keywords = [
        "hour", "time", "peak", "weekend", "sunday", "evening",
        "night", "pattern", "temporal", "when",
    ]
    if any(kw in q for kw in time_keywords):
        tables.append("hourly_fraud_pattern")

    # If nothing matched, return all tables (comprehensive context)
    if not tables:
        tables = [
            "geo_heatmap", "risk_distribution", "scam_taxonomy",
            "alert_effectiveness", "hourly_fraud_pattern",
        ]

    return tables


def get_data_context(query: str) -> tuple[str, list[str]]:
    """
    Return relevant slices of gold table data and the list of tables used.
    """
    relevant = _detect_relevant_tables(query)

    table_map = {
        "geo_heatmap": GEO_HEATMAP,
        "risk_distribution": RISK_DISTRIBUTION,
        "scam_taxonomy": SCAM_TAXONOMY,
        "alert_effectiveness": ALERT_EFFECTIVENESS,
        "hourly_fraud_pattern": HOURLY_FRAUD_PATTERN,
    }

    # If most tables are relevant, return full context
    if len(relevant) >= 4:
        return get_full_data_context(), list(table_map.keys())

    context = {k: table_map[k] for k in relevant}
    return json.dumps(context, indent=2), relevant
