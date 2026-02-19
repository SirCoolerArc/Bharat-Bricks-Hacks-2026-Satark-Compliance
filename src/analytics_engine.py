"""
analytics_engine.py — InsightX Analytics Engine
================================================
Responsible for all deterministic computations on the dataset.
Receives a parsed intent dict from query_parser.py and returns
a structured result dict with computed numbers.

The LLM never touches this layer. All numbers come from pandas.

Entry point:
    from src.analytics_engine import run_query
    result = run_query(parsed_intent)

Result dict structure:
    {
        "success": bool,
        "intent": str,
        "metric": str,
        "data": dict or pd.DataFrame,
        "summary": dict,          # key numbers for narrative generation
        "warning": str or None,   # low sample size or other cautions
        "assumption": str or None # e.g. high-value threshold disclosure
        "error": str or None
    }
"""

import pandas as pd
import numpy as np

try:
    from src.data_loader import get_dataframe, CONSTANTS, sample_size_warning
except ModuleNotFoundError:
    from data_loader import get_dataframe, CONSTANTS, sample_size_warning

# ---------------------------------------------------------------------------
# SECTION 0: ENTRY POINT
# ---------------------------------------------------------------------------

def run_query(parsed_intent: dict) -> dict:
    """
    Main entry point. Dispatches to the correct compute function
    based on the intent type in the parsed_intent dict.

    Parameters
    ----------
    parsed_intent : dict
        Output from query_parser.parse_query()

    Returns
    -------
    dict
        Structured result with computed data, summary, and metadata.
    """
    intent = parsed_intent.get("intent", "unknown")

    if intent == "unknown":
        return _error_result(
            parsed_intent,
            "I couldn't understand that query. Could you rephrase it?"
        )

    dispatch = {
        "descriptive":   _compute_descriptive,
        "comparative":   _compute_comparative,
        "temporal":      _compute_temporal,
        "segmentation":  _compute_segmentation,
        "correlation":   _compute_correlation,
        "risk":          _compute_risk,
    }

    handler = dispatch.get(intent)
    if not handler:
        return _error_result(parsed_intent, f"Unrecognised intent type: '{intent}'")

    try:
        return handler(parsed_intent)
    except Exception as e:
        return _error_result(parsed_intent, f"Computation error: {str(e)}")


# ---------------------------------------------------------------------------
# SECTION 1: DESCRIPTIVE
# "What is the average amount for bill payments?"
# "How many transactions failed on weekends?"
# ---------------------------------------------------------------------------

def _compute_descriptive(parsed: dict) -> dict:
    df = _apply_filters(parsed)
    metric = parsed.get("metric")
    n = len(df)

    warning = sample_size_warning(n)
    assumption = _high_value_assumption(parsed)

    if n == 0:
        return _error_result(parsed, "No transactions match the specified filters.")

    if metric == "failure_rate":
        value = _failure_rate(df)
        return _build_result(parsed, {
            "metric_value": value,
            "metric_label": "Failure Rate",
            "unit": "%",
            "total": n,
            "failed": int(df["is_failed"].sum()),
        }, warning=warning, assumption=assumption)

    elif metric == "success_rate":
        value = round(100 - _failure_rate(df), 2)
        return _build_result(parsed, {
            "metric_value": value,
            "metric_label": "Success Rate",
            "unit": "%",
            "total": n,
            "successful": int((df["transaction_status"] == "SUCCESS").sum()),
        }, warning=warning, assumption=assumption)

    elif metric == "average_amount":
        value = round(df["amount_inr"].mean(), 2)
        median = round(df["amount_inr"].median(), 2)
        return _build_result(parsed, {
            "metric_value": value,
            "metric_label": "Average Transaction Amount",
            "unit": "INR",
            "median": median,
            "total": n,
        }, warning=warning, assumption=assumption)

    elif metric == "median_amount":
        value = round(df["amount_inr"].median(), 2)
        return _build_result(parsed, {
            "metric_value": value,
            "metric_label": "Median Transaction Amount",
            "unit": "INR",
            "mean": round(df["amount_inr"].mean(), 2),
            "total": n,
        }, warning=warning, assumption=assumption)

    elif metric == "transaction_count":
        total_txns = len(get_dataframe())
        share = round(n / total_txns * 100, 2)
        return _build_result(parsed, {
            "metric_value": n,
            "metric_label": "Transaction Count",
            "unit": "transactions",
            "volume_share_pct": share,
        }, warning=warning, assumption=assumption)

    elif metric == "fraud_flag_rate":
        value = _flag_rate(df)
        return _build_result(parsed, {
            "metric_value": value,
            "metric_label": "Fraud Flag Rate",
            "unit": "%",
            "total": n,
            "flagged": int(df["fraud_flag"].sum()),
            "baseline_flag_rate": CONSTANTS["OVERALL_FLAG_RATE"],
        }, warning=warning, assumption=assumption)

    elif metric == "total_volume":
        value = round(df["amount_inr"].sum(), 2)
        return _build_result(parsed, {
            "metric_value": value,
            "metric_label": "Total Transaction Volume",
            "unit": "INR",
            "total": n,
            "average": round(df["amount_inr"].mean(), 2),
        }, warning=warning, assumption=assumption)

    else:
        # Default: return general stats
        return _compute_general_stats(df, parsed, warning, assumption)


def _compute_general_stats(df, parsed, warning, assumption):
    """Fallback for descriptive queries without a specific metric."""
    return _build_result(parsed, {
        "total": len(df),
        "failure_rate": _failure_rate(df),
        "avg_amount": round(df["amount_inr"].mean(), 2),
        "median_amount": round(df["amount_inr"].median(), 2),
        "fraud_flag_rate": _flag_rate(df),
        "metric_label": "General Statistics",
    }, warning=warning, assumption=assumption)


# ---------------------------------------------------------------------------
# SECTION 2: COMPARATIVE
# "Compare failure rates for HDFC vs SBI on weekends"
# "Which transaction type has the highest failure rate?"
# ---------------------------------------------------------------------------

def _compute_comparative(parsed: dict) -> dict:
    df = _apply_filters(parsed, exclude_comparison_filter=True)
    metric = parsed.get("metric")
    group_by = parsed.get("group_by")
    comparison_values = parsed.get("comparison_values")

    if not group_by:
        return _error_result(parsed, "Could not determine what to compare. Please specify (e.g. 'compare banks' or 'compare transaction types').")

    # If specific values given, filter to just those
    if comparison_values:
        df = df[df[group_by].isin(comparison_values)]

    if len(df) == 0:
        return _error_result(parsed, "No transactions match the comparison filters.")

    assumption = _high_value_assumption(parsed)

    if metric == "failure_rate":
        result_df = _grouped_failure_rate(df, group_by)
    elif metric == "success_rate":
        result_df = _grouped_failure_rate(df, group_by)
        result_df["success_rate_pct"] = (100 - result_df["failure_rate_pct"]).round(2)
    elif metric in ("average_amount", "median_amount"):
        result_df = df.groupby(group_by)["amount_inr"].agg(
            total="count",
            average_amount=("mean"),
            median_amount=("median")
        ).round(2).reset_index()
        result_df = result_df.sort_values("average_amount", ascending=False)
    elif metric == "fraud_flag_rate":
        result_df = _grouped_flag_rate(df, group_by)
    elif metric == "transaction_count":
        result_df = df.groupby(group_by).size().reset_index(name="count")
        result_df["volume_share_pct"] = (result_df["count"] / len(get_dataframe()) * 100).round(2)
        result_df = result_df.sort_values("count", ascending=False)
    else:
        result_df = _grouped_failure_rate(df, group_by)

    # Attach low-sample warnings per group
    warnings = _group_warnings(result_df, group_by)

    # Build summary: highest and lowest
    summary = _comparative_summary(result_df, group_by, metric)
    summary["baseline"] = CONSTANTS["OVERALL_FAILURE_RATE"] if metric == "failure_rate" else None
    summary["group_by"] = group_by

    return _build_result(parsed, summary,
                         data=result_df,
                         warning=warnings,
                         assumption=assumption)


# ---------------------------------------------------------------------------
# SECTION 3: TEMPORAL
# "What are peak transaction hours?"
# "How do failure rates differ across days of the week?"
# "Is there a difference between weekend and weekday volumes?"
# ---------------------------------------------------------------------------

def _compute_temporal(parsed: dict) -> dict:
    df = _apply_filters(parsed)
    metric = parsed.get("metric")
    time_scope = parsed.get("time_scope")
    assumption = _high_value_assumption(parsed)

    if len(df) == 0:
        return _error_result(parsed, "No transactions match the specified filters.")

    # Determine time column
    if time_scope == "hourly" or metric == "peak_hours":
        time_col = "hour_of_day"
    elif time_scope == "daily":
        time_col = "day_of_week"
    elif time_scope == "weekend_vs_weekday":
        time_col = "is_weekend"
    else:
        # Default: use hour_of_day
        time_col = "hour_of_day"

    if metric == "peak_hours" or time_col == "hour_of_day":
        result_df = _grouped_failure_rate(df, time_col)
        result_df = result_df.sort_values(time_col)

        # Identify top 5 peak hours by volume
        peak_hours = result_df.nlargest(5, "total")[time_col].tolist()
        peak_hour_top = result_df.loc[result_df["total"].idxmax(), time_col]

        summary = {
            "metric_label": "Hourly Transaction Pattern",
            "peak_hour": int(peak_hour_top),
            "peak_cluster": peak_hours,
            "peak_volume": int(result_df["total"].max()),
            "peak_failure_rate": float(result_df.loc[result_df["total"].idxmax(), "failure_rate_pct"]),
            "lowest_volume_hour": int(result_df.loc[result_df["total"].idxmin(), time_col]),
            "baseline_failure_rate": CONSTANTS["OVERALL_FAILURE_RATE"],
        }

    elif time_col == "day_of_week":
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        result_df = _grouped_failure_rate(df, time_col)
        existing = [d for d in day_order if d in result_df[time_col].values]
        result_df[time_col] = pd.Categorical(result_df[time_col], categories=existing, ordered=True)
        result_df = result_df.sort_values(time_col)

        highest_day = result_df.loc[result_df["failure_rate_pct"].idxmax(), time_col]
        lowest_day = result_df.loc[result_df["failure_rate_pct"].idxmin(), time_col]

        summary = {
            "metric_label": "Day of Week Pattern",
            "highest_failure_day": str(highest_day),
            "lowest_failure_day": str(lowest_day),
            "weekend_failure_rate": CONSTANTS["WEEKEND_FAILURE_RATE"],
            "weekday_failure_rate": CONSTANTS["WEEKDAY_FAILURE_RATE"],
            "baseline_failure_rate": CONSTANTS["OVERALL_FAILURE_RATE"],
        }

    elif time_col == "is_weekend":
        result_df = _grouped_failure_rate(df, time_col)
        result_df["period"] = result_df["is_weekend"].map({0: "Weekday", 1: "Weekend"})

        weekend_row = result_df[result_df["is_weekend"] == 1]
        weekday_row = result_df[result_df["is_weekend"] == 0]

        summary = {
            "metric_label": "Weekend vs Weekday",
            "weekend_failure_rate": float(weekend_row["failure_rate_pct"].values[0]) if len(weekend_row) else None,
            "weekday_failure_rate": float(weekday_row["failure_rate_pct"].values[0]) if len(weekday_row) else None,
            "weekend_volume": int(weekend_row["total"].values[0]) if len(weekend_row) else None,
            "weekday_volume": int(weekday_row["total"].values[0]) if len(weekday_row) else None,
            "baseline_failure_rate": CONSTANTS["OVERALL_FAILURE_RATE"],
        }
    else:
        result_df = _grouped_failure_rate(df, time_col)
        summary = {"metric_label": "Temporal Analysis"}

    return _build_result(parsed, summary, data=result_df, assumption=assumption)


# ---------------------------------------------------------------------------
# SECTION 4: SEGMENTATION
# "Which age group uses P2P most frequently?"
# "Break down failure rates by merchant category"
# ---------------------------------------------------------------------------

def _compute_segmentation(parsed: dict) -> dict:
    df = _apply_filters(parsed)
    metric = parsed.get("metric")
    group_by = parsed.get("group_by")
    assumption = _high_value_assumption(parsed)

    if not group_by:
        return _error_result(parsed, "Could not determine the segmentation dimension. Please specify (e.g. 'by age group' or 'by state').")

    if len(df) == 0:
        return _error_result(parsed, "No transactions match the specified filters.")

    if metric == "transaction_count":
        result_df = df.groupby(group_by).size().reset_index(name="count")
        result_df["volume_share_pct"] = (result_df["count"] / len(df) * 100).round(2)
        result_df = result_df.sort_values("count", ascending=False)
        top_segment = result_df.iloc[0][group_by]
        top_share = result_df.iloc[0]["volume_share_pct"]
        summary = {
            "metric_label": f"Transaction Volume by {group_by}",
            "top_segment": str(top_segment),
            "top_segment_share_pct": float(top_share),
            "group_by": group_by,
            "total_transactions": len(df),
        }

    elif metric in ("average_amount", "median_amount"):
        result_df = df.groupby(group_by)["amount_inr"].agg(
            count="count",
            average_amount="mean",
            median_amount="median"
        ).round(2).reset_index()
        result_df = result_df.sort_values("average_amount", ascending=False)
        top_segment = result_df.iloc[0][group_by]
        summary = {
            "metric_label": f"Amount by {group_by}",
            "top_segment": str(top_segment),
            "top_avg_amount": float(result_df.iloc[0]["average_amount"]),
            "overall_avg": round(df["amount_inr"].mean(), 2),
            "group_by": group_by,
        }

    elif metric == "fraud_flag_rate":
        result_df = _grouped_flag_rate(df, group_by)
        top_segment = result_df.iloc[0][group_by]
        summary = {
            "metric_label": f"Fraud Flag Rate by {group_by}",
            "top_segment": str(top_segment),
            "top_flag_rate": float(result_df.iloc[0]["flag_rate_pct"]),
            "baseline_flag_rate": CONSTANTS["OVERALL_FLAG_RATE"],
            "group_by": group_by,
            "caution": "Only 480 total flagged transactions — sub-segment counts are small.",
        }

    else:
        # Default: failure rate segmentation
        result_df = _grouped_failure_rate(df, group_by)
        top_segment = result_df.iloc[0][group_by]
        bottom_segment = result_df.iloc[-1][group_by]
        summary = {
            "metric_label": f"Failure Rate by {group_by}",
            "highest_segment": str(top_segment),
            "highest_rate": float(result_df.iloc[0]["failure_rate_pct"]),
            "lowest_segment": str(bottom_segment),
            "lowest_rate": float(result_df.iloc[-1]["failure_rate_pct"]),
            "baseline_failure_rate": CONSTANTS["OVERALL_FAILURE_RATE"],
            "group_by": group_by,
        }

    warnings = _group_warnings(result_df, group_by)

    return _build_result(parsed, summary, data=result_df,
                         warning=warnings, assumption=assumption)


# ---------------------------------------------------------------------------
# SECTION 5: CORRELATION
# "Is there a relationship between network type and transaction success?"
# "Does device type affect failure rate?"
# ---------------------------------------------------------------------------

def _compute_correlation(parsed: dict) -> dict:
    df = _apply_filters(parsed)
    group_by = parsed.get("group_by")
    assumption = _high_value_assumption(parsed)

    if len(df) == 0:
        return _error_result(parsed, "No transactions match the specified filters.")

    if not group_by:
        # Generic numeric correlation
        num_cols = ["amount_inr", "fraud_flag", "is_failed", "hour_of_day", "is_weekend"]
        existing = [c for c in num_cols if c in df.columns]
        corr = df[existing].corr().round(4)
        summary = {
            "metric_label": "Numeric Correlation Matrix",
            "note": "Near-zero correlations across all numeric fields — no strong linear relationships in this dataset.",
            "amount_vs_failure": float(corr.loc["amount_inr", "is_failed"]),
            "amount_vs_fraud_flag": float(corr.loc["amount_inr", "fraud_flag"]),
            "weekend_vs_failure": float(corr.loc["is_weekend", "is_failed"]),
        }
        return _build_result(parsed, summary, data=corr, assumption=assumption)

    # Categorical correlation: failure rate across groups
    result_df = _grouped_failure_rate(df, group_by)
    spread = round(result_df["failure_rate_pct"].max() - result_df["failure_rate_pct"].min(), 2)
    baseline = CONSTANTS["OVERALL_FAILURE_RATE"]

    # Interpret strength of relationship
    if spread < 0.3:
        relationship = "negligible"
    elif spread < 0.75:
        relationship = "weak"
    elif spread < 2.0:
        relationship = "moderate"
    else:
        relationship = "strong"

    top = result_df.iloc[0]
    bottom = result_df.iloc[-1]

    summary = {
        "metric_label": f"Relationship between {group_by} and failure rate",
        "relationship_strength": relationship,
        "spread_pp": spread,
        "highest": {"segment": str(top[group_by]), "failure_rate": float(top["failure_rate_pct"])},
        "lowest": {"segment": str(bottom[group_by]), "failure_rate": float(bottom["failure_rate_pct"])},
        "baseline_failure_rate": baseline,
        "interpretation": f"The spread across {group_by} groups is {spread} percentage points, indicating a {relationship} relationship with failure rate.",
    }

    warnings = _group_warnings(result_df, group_by)
    return _build_result(parsed, summary, data=result_df,
                         warning=warnings, assumption=assumption)


# ---------------------------------------------------------------------------
# SECTION 6: RISK
# "What % of high-value transactions are flagged?"
# "Are flagged transactions concentrated by network type?"
# "Which transaction type has the highest fraud flag rate?"
# ---------------------------------------------------------------------------

def _compute_risk(parsed: dict) -> dict:
    df = _apply_filters(parsed)
    group_by = parsed.get("group_by")
    filters = parsed.get("filters", {})
    assumption = _high_value_assumption(parsed)

    # Always add the fraud flag caution note
    fraud_caution = (
        "Note: fraud_flag = 1 indicates transactions flagged for automated review, "
        "NOT confirmed fraud cases. Only 480 of 250,000 transactions (0.19%) are flagged."
    )

    if len(df) == 0:
        return _error_result(parsed, "No transactions match the specified filters.")

    overall_flag_rate = _flag_rate(df)
    total_flagged = int(df["fraud_flag"].sum())
    n = len(df)

    if group_by:
        result_df = _grouped_flag_rate(df, group_by)
        top = result_df.iloc[0]
        bottom = result_df.iloc[-1]

        summary = {
            "metric_label": f"Fraud Flag Rate by {group_by}",
            "overall_flag_rate_in_subset": overall_flag_rate,
            "baseline_flag_rate": CONSTANTS["OVERALL_FLAG_RATE"],
            "total_flagged_in_subset": total_flagged,
            "total_in_subset": n,
            "highest_segment": str(top[group_by]),
            "highest_flag_rate": float(top["flag_rate_pct"]),
            "lowest_segment": str(bottom[group_by]),
            "lowest_flag_rate": float(bottom["flag_rate_pct"]),
            "group_by": group_by,
            "caution": fraud_caution,
        }
        warnings = _group_warnings(result_df, group_by)

    else:
        # High-value analysis or general risk overview
        hv_df = df[df["amount_inr"] >= CONSTANTS["HIGH_VALUE_THRESHOLD"]]
        hv_flag_rate = _flag_rate(hv_df)
        concentration = round(hv_flag_rate / CONSTANTS["OVERALL_FLAG_RATE"], 2) if CONSTANTS["OVERALL_FLAG_RATE"] > 0 else None

        summary = {
            "metric_label": "Risk Overview",
            "overall_flag_rate": overall_flag_rate,
            "high_value_flag_rate": hv_flag_rate,
            "high_value_threshold": CONSTANTS["HIGH_VALUE_THRESHOLD"],
            "concentration_ratio": concentration,
            "total_flagged": total_flagged,
            "total_transactions": n,
            "flagged_failure_rate": _failure_rate(df[df["fraud_flag"] == 1]),
            "unflagged_failure_rate": _failure_rate(df[df["fraud_flag"] == 0]),
            "caution": fraud_caution,
        }
        result_df = None
        warnings = None

    return _build_result(parsed, summary,
                         data=result_df if group_by else None,
                         warning=warnings,
                         assumption=assumption)


# ---------------------------------------------------------------------------
# SECTION 7: SHARED UTILITIES
# ---------------------------------------------------------------------------

def _apply_filters(parsed: dict, exclude_comparison_filter: bool = False) -> pd.DataFrame:
    """
    Apply filters from the parsed intent to the full DataFrame.
    Returns a filtered copy.

    exclude_comparison_filter: if True, skips list-type filters
    (used in comparative queries where we group BY the comparison column
    rather than filtering to specific values beforehand).
    """
    df = get_dataframe()
    filters = parsed.get("filters", {}) or {}
    mask = pd.Series([True] * len(df), index=df.index)

    for key, value in filters.items():
        if value is None:
            continue

        # Handle high-value flag
        if key == "is_high_value" and value:
            mask &= df["amount_inr"] >= CONSTANTS["HIGH_VALUE_THRESHOLD"]
            continue

        if key not in df.columns:
            continue

        if isinstance(value, list):
            if not exclude_comparison_filter:
                mask &= df[key].isin(value)
        else:
            mask &= df[key] == value

    return df[mask].copy()


def _failure_rate(df: pd.DataFrame) -> float:
    """Compute failure rate % for a DataFrame. Returns 0.0 if empty."""
    if len(df) == 0:
        return 0.0
    return round(df["is_failed"].mean() * 100, 2)


def _flag_rate(df: pd.DataFrame) -> float:
    """Compute fraud flag rate % for a DataFrame. Returns 0.0 if empty."""
    if len(df) == 0:
        return 0.0
    return round(df["fraud_flag"].mean() * 100, 2)


def _grouped_failure_rate(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """
    Compute failure rate grouped by a column.
    Returns DataFrame sorted by failure_rate_pct descending.
    """
    result = df.groupby(group_col).agg(
        total=(group_col, "count"),
        failed=("is_failed", "sum")
    ).reset_index()
    result["failure_rate_pct"] = (result["failed"] / result["total"] * 100).round(2)
    return result.sort_values("failure_rate_pct", ascending=False).reset_index(drop=True)


def _grouped_flag_rate(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """
    Compute fraud flag rate grouped by a column.
    Returns DataFrame sorted by flag_rate_pct descending.
    """
    result = df.groupby(group_col).agg(
        total=(group_col, "count"),
        flagged=("fraud_flag", "sum")
    ).reset_index()
    result["flag_rate_pct"] = (result["flagged"] / result["total"] * 100).round(2)
    return result.sort_values("flag_rate_pct", ascending=False).reset_index(drop=True)


def _comparative_summary(result_df: pd.DataFrame, group_by: str, metric: str) -> dict:
    """Extract highest/lowest from a comparative result DataFrame."""
    if metric == "fraud_flag_rate" and "flag_rate_pct" in result_df.columns:
        val_col = "flag_rate_pct"
    elif metric in ("average_amount", "median_amount") and "average_amount" in result_df.columns:
        val_col = "average_amount"
    elif "failure_rate_pct" in result_df.columns:
        val_col = "failure_rate_pct"
    elif "count" in result_df.columns:
        val_col = "count"
    else:
        return {}

    top = result_df.loc[result_df[val_col].idxmax()]
    bottom = result_df.loc[result_df[val_col].idxmin()]

    return {
        "metric_label": f"{metric} by {group_by}",
        "highest": {"segment": str(top[group_by]), "value": float(top[val_col])},
        "lowest": {"segment": str(bottom[group_by]), "value": float(bottom[val_col])},
        "spread": round(float(top[val_col]) - float(bottom[val_col]), 2),
        "total_groups": len(result_df),
    }


def _group_warnings(result_df: pd.DataFrame, group_by: str) -> str | None:
    """
    Check each group for low sample size.
    Returns a combined warning string if any groups are below threshold.
    """
    if "total" not in result_df.columns:
        return None
    low = result_df[result_df["total"] < CONSTANTS["MIN_SAMPLE_SIZE"]]
    if low.empty:
        return None
    segments = low[group_by].tolist()
    return (
        f"⚠️ Low sample size for: {', '.join(str(s) for s in segments)}. "
        f"Results for these segments should be interpreted with caution."
    )


def _high_value_assumption(parsed: dict) -> str | None:
    """
    If the query involves high-value transactions, return a disclosure string.
    """
    filters = parsed.get("filters", {}) or {}
    if filters.get("is_high_value"):
        return (
            f"'High value' is defined as transactions above the P90 threshold "
            f"(₹{CONSTANTS['HIGH_VALUE_THRESHOLD']:,.0f}), representing the top 10% by amount."
        )
    return None


def _build_result(parsed: dict, summary: dict,
                  data=None, warning=None, assumption=None) -> dict:
    """Construct the standard result dictionary."""
    return {
        "success": True,
        "intent": parsed.get("intent"),
        "metric": parsed.get("metric"),
        "filters_applied": parsed.get("filters", {}),
        "group_by": parsed.get("group_by"),
        "summary": summary,
        "data": data,
        "warning": warning,
        "assumption": assumption,
        "raw_query": parsed.get("raw_query"),
        "assumptions_from_parser": parsed.get("assumptions", []),
    }


def _error_result(parsed: dict, message: str) -> dict:
    """Construct a standardised error result."""
    return {
        "success": False,
        "intent": parsed.get("intent"),
        "metric": parsed.get("metric"),
        "filters_applied": parsed.get("filters", {}),
        "group_by": parsed.get("group_by"),
        "summary": {},
        "data": None,
        "warning": None,
        "assumption": None,
        "raw_query": parsed.get("raw_query"),
        "error": message,
    }


# ---------------------------------------------------------------------------
# Quick self-test — run from project root: python -m src.analytics_engine
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json

    test_intents = [
        {
            "intent": "comparative",
            "metric": "failure_rate",
            "filters": {},
            "group_by": "transaction_type",
            "comparison_values": ["P2P", "P2M", "Bill Payment", "Recharge"],
            "raw_query": "Which transaction type has the highest failure rate?",
            "assumptions": [],
        },
        {
            "intent": "comparative",
            "metric": "failure_rate",
            "filters": {"sender_bank": ["HDFC", "SBI"], "is_weekend": 1},
            "group_by": "sender_bank",
            "comparison_values": ["HDFC", "SBI"],
            "raw_query": "Compare failure rates for HDFC vs SBI on weekends",
            "assumptions": [],
        },
        {
            "intent": "temporal",
            "metric": "peak_hours",
            "filters": {"transaction_type": "P2M", "merchant_category": "Food"},
            "group_by": None,
            "time_scope": "hourly",
            "raw_query": "What are the peak transaction hours for food delivery?",
            "assumptions": [],
        },
        {
            "intent": "risk",
            "metric": "fraud_flag_rate",
            "filters": {"is_high_value": True},
            "group_by": None,
            "raw_query": "What percentage of high-value transactions are flagged for review?",
            "assumptions": [],
        },
        {
            "intent": "correlation",
            "metric": "success_rate",
            "filters": {},
            "group_by": "network_type",
            "raw_query": "Is there a relationship between network type and transaction success?",
            "assumptions": [],
        },
    ]

    for intent in test_intents:
        print("\n" + "=" * 60)
        print(f"Query: {intent['raw_query']}")
        result = run_query(intent)
        print(f"Success: {result['success']}")
        print(f"Summary: {json.dumps(result['summary'], indent=2)}")
        if result.get("warning"):
            print(f"Warning: {result['warning']}")
        if result.get("assumption"):
            print(f"Assumption: {result['assumption']}")
        if result.get("data") is not None and isinstance(result["data"], pd.DataFrame):
            print(f"Data preview:\n{result['data'].head()}")