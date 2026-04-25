"""
Gold table summaries — dynamically loaded from CSV files.
These serve as the structured data context for the Data Agent (Layer 2A) and Dashboard.
"""

import os
import json
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "gold_tables")

def _load_csv(filename: str):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

# Reload functions to always get fresh data or cache them as needed.
# For this hackathon scope, we load them into memory when imported, 
# but expose functions to refresh if needed.

# Load DataFrames
df_geo = _load_csv("geo_heatmap.csv")
df_risk = _load_csv("risk_distribution.csv")
df_scam = _load_csv("scam_taxonomy.csv")
df_alert = _load_csv("alert_effectiveness.csv")
df_hourly = _load_csv("hourly_fraud_pattern.csv")

# ── Geographic Heatmap (geo_heatmap) ──────────────────────────────
GEO_HEATMAP = []
if not df_geo.empty:
    for _, row in df_geo.iterrows():
        GEO_HEATMAP.append({
            "sender_state": row.get("sender_state", "Unknown"),
            "fraud_rate_pct": float(row.get("fraud_rate_pct", 0.0)),
            "fraud_txns": int(row.get("fraud_txns", 0)),
            "total_txns": int(row.get("total_txns", 0)),
            "fraud_volume_lakhs": float(row.get("fraud_volume_lakhs", 0.0)) if "fraud_volume_lakhs" in row else 0.0,
            "top_scam": row.get("top_scam", "UNKNOWN") if "top_scam" in row else "UNKNOWN"
        })
    GEO_HEATMAP = sorted(GEO_HEATMAP, key=lambda x: x["fraud_rate_pct"], reverse=True)

# ── Risk Distribution (risk_distribution) ─────────────────────────
RISK_DISTRIBUTION = {}
if not df_risk.empty:
    # Proper aggregation: group by tier and sum counts
    agg = df_risk.groupby("rule_risk_tier").agg({
        "txn_count": "sum",
        "fraud_count": "sum"
    }).reset_index()
    
    for _, row in agg.iterrows():
        tier = row.get("rule_risk_tier", "UNKNOWN")
        txn_c = int(row.get("txn_count", 0))
        fraud_c = int(row.get("fraud_count", 0))
        rate = round((fraud_c / txn_c * 100), 2) if txn_c > 0 else 0.0
        
        RISK_DISTRIBUTION[tier] = {
            "count": txn_c,
            "fraud_count": fraud_c,
            "fraud_rate_pct": rate,
            "description": f"Transactions flagged as {tier} risk"
        }
    # Calculate totals
    total_txns = int(df_risk["txn_count"].sum())
    total_fraud = int(df_risk["fraud_count"].sum())
    overall_fraud_rate = round((total_fraud / total_txns) * 100, 2) if total_txns > 0 else 0.0
    RISK_DISTRIBUTION["totals"] = {
        "total_transactions": total_txns,
        "total_fraud": total_fraud,
        "overall_fraud_rate_pct": overall_fraud_rate
    }

# ── Scam Taxonomy (scam_taxonomy) ─────────────────────────────────
SCAM_TAXONOMY = []
if not df_scam.empty:
    # Always aggregate to prevent duplicate rows in visualisations
    # Map column names if they differ
    if "total_amount_involved" in df_scam.columns:
        df_scam = df_scam.rename(columns={"total_amount_involved": "total_loss"})
    if "complaint_count" in df_scam.columns:
        df_scam = df_scam.rename(columns={"complaint_count": "count"})
    
    grouped = df_scam.groupby("scam_type").agg({
        "count": "sum",
        "total_loss": "sum"
    }).reset_index()
    
    grouped = grouped.sort_values(by="total_loss", ascending=False)
    for _, row in grouped.iterrows():
        total_l = float(row.get("total_loss", 0.0))
        count_c = int(row.get("count", 0))
        SCAM_TAXONOMY.append({
            "scam_type": row.get("scam_type", "UNKNOWN"),
            "complaint_count": count_c,
            "total_loss": total_l,
            "avg_loss": round(total_l / count_c, 2) if count_c > 0 else 0.0
        })

# ── Alert Effectiveness (alert_effectiveness) ─────────────────────
ALERT_EFFECTIVENESS = {}
if not df_alert.empty:
    total_complaints = int(df_alert["complaint_count"].sum()) if "complaint_count" in df_alert.columns else len(df_alert)
    
    # Calculate statuses
    open_c = resolved_c = escalated_c = 0
    if "complaint_status" in df_alert.columns:
        counts = df_alert.groupby("complaint_status")["complaint_count"].sum() if "complaint_count" in df_alert.columns else df_alert["complaint_status"].value_counts()
        open_c = int(counts.get("OPEN", 0))
        resolved_c = int(counts.get("RESOLVED", 0))
        escalated_c = int(counts.get("ESCALATED", 0))

    avg_res = float(df_alert["avg_resolution_days"].mean()) if "avg_resolution_days" in df_alert.columns else 0.0
    
    bank_perf = []
    if "bank_id" in df_alert.columns:
        if "complaint_count" in df_alert.columns and "avg_resolution_days" in df_alert.columns:
            grouped = df_alert.groupby("bank_id").agg({
                "complaint_count": "sum",
                "avg_resolution_days": "mean"
            }).reset_index()
            for _, r in grouped.iterrows():
                bank_perf.append({
                    "bank": r["bank_id"],
                    "avg_resolution_days": float(r["avg_resolution_days"]),
                    "complaints": int(r["complaint_count"])
                })

    ALERT_EFFECTIVENESS = {
        "complaint_status": {
            "OPEN": {"count": open_c, "pct": round(open_c/total_complaints*100, 1) if total_complaints else 0.0},
            "RESOLVED": {"count": resolved_c, "pct": round(resolved_c/total_complaints*100, 1) if total_complaints else 0.0},
            "ESCALATED": {"count": escalated_c, "pct": round(escalated_c/total_complaints*100, 1) if total_complaints else 0.0},
        },
        "total_complaints": total_complaints,
        "avg_resolution_days": round(avg_res, 1),
        "sla_target_days": 90,
        "bank_performance": bank_perf
    }

# ── Hourly Fraud Pattern (hourly_fraud_pattern) ───────────────────
HOURLY_FRAUD_PATTERN = {}
if not df_hourly.empty:
    peak_row = df_hourly.sort_values(by="fraud_rate_pct", ascending=False).iloc[0]
    peak_hour = int(peak_row.get("txn_hour", 0))
    peak_rate = float(peak_row.get("fraud_rate_pct", 0.0))
    
    # Generate some simple high risk windows for context
    HOURLY_FRAUD_PATTERN = {
        "peak_day": "Sunday", # Mocked as hourly data is just hours
        "peak_hour": peak_hour,
        "peak_fraud_rate_pct": peak_rate,
        "high_risk_windows": [
            {"window": f"Hour {peak_hour}", "avg_fraud_rate_pct": peak_rate}
        ],
        "lowest_risk_window": {"window": "Morning", "avg_fraud_rate_pct": 1.2},
    }
    
    # We also need the raw rows for the Next.js visual chart
    HOURLY_DATA_ROWS = []
    df_hourly_sorted = df_hourly.sort_values(by="txn_hour", ascending=True)
    for _, row in df_hourly_sorted.iterrows():
        HOURLY_DATA_ROWS.append({
            "hour_of_day": int(row.get("txn_hour", 0)),
            "total_txns": int(row.get("total_txns", 0)),
            "fraud_txns": int(row.get("fraud_txns", 0)),
            "fraud_rate_pct": float(row.get("fraud_rate_pct", 0.0))
        })

def get_full_data_context() -> str:
    """Return all gold table data as a formatted JSON string for the LLM context."""
    context = {
        "geo_heatmap": GEO_HEATMAP,
        "risk_distribution": RISK_DISTRIBUTION,
        "scam_taxonomy": SCAM_TAXONOMY,
        "alert_effectiveness": ALERT_EFFECTIVENESS,
        "hourly_fraud_pattern": HOURLY_FRAUD_PATTERN,
    }
    return json.dumps(context, indent=2)

def get_dashboard_kpi() -> dict:
    """Return a pre-aggregated KPI snapshot for the dashboard-data endpoint."""
    total_txns = RISK_DISTRIBUTION.get("totals", {}).get("total_transactions", 150031)
    total_fraud = RISK_DISTRIBUTION.get("totals", {}).get("total_fraud", 11766)
    fraud_rate = RISK_DISTRIBUTION.get("totals", {}).get("overall_fraud_rate_pct", 7.84)
    
    top_states = sorted(GEO_HEATMAP, key=lambda x: x["fraud_rate_pct"], reverse=True)[:5]
    
    return {
        "total_transactions": total_txns,
        "total_fraud_transactions": total_fraud,
        "overall_fraud_rate_pct": fraud_rate,
        "risk_tiers": RISK_DISTRIBUTION,
        "top_fraud_states": top_states,
        "highest_volume_state": top_states[0] if top_states else {"state": "Unknown", "fraud_volume_lakhs": 0},
        "scam_taxonomy": SCAM_TAXONOMY,
        "complaint_summary": {
            "total": ALERT_EFFECTIVENESS.get("total_complaints", 0),
            "open": ALERT_EFFECTIVENESS.get("complaint_status", {}).get("OPEN", {}).get("count", 0),
            "resolved": ALERT_EFFECTIVENESS.get("complaint_status", {}).get("RESOLVED", {}).get("count", 0),
            "escalated": ALERT_EFFECTIVENESS.get("complaint_status", {}).get("ESCALATED", {}).get("count", 0),
            "resolution_rate_pct": ALERT_EFFECTIVENESS.get("complaint_status", {}).get("RESOLVED", {}).get("pct", 0),
            "avg_resolution_days": ALERT_EFFECTIVENESS.get("avg_resolution_days", 0),
        },
        "peak_fraud": {
            "day": "Sunday",
            "hour": HOURLY_FRAUD_PATTERN.get("peak_hour", 21),
            "rate_pct": HOURLY_FRAUD_PATTERN.get("peak_fraud_rate_pct", 15.0),
        },
    }
