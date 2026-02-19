"""
data_loader.py — InsightX Analytics Engine
==========================================
Responsible for:
  - Loading and caching the dataset
  - Cleaning column names (handles spaces in raw CSV headers)
  - Parsing timestamps
  - Defining all system-wide constants derived from EDA
  - Providing a clean, validated DataFrame to all other modules

All other modules should import via:
    from data_loader import get_dataframe, CONSTANTS
"""

import pandas as pd
import os

# ---------------------------------------------------------------------------
# DATASET PATH
# ---------------------------------------------------------------------------
# Update this path if running locally vs Kaggle
DATASET_PATH = os.environ.get(
    "INSIGHTX_DATA_PATH",
    "C:\\Users\\Rishabh Kumar\\insightx\\data\\raw\\upi_transactions_2024.csv"
)

# ---------------------------------------------------------------------------
# COLUMN NAME MAPPING
# Raw CSV has spaces and special characters in some column names.
# We normalise everything here so all downstream code uses clean names.
# ---------------------------------------------------------------------------
COLUMN_RENAME_MAP = {
    "transaction id":   "transaction_id",
    "transaction type": "transaction_type",
    "amount (INR)":     "amount_inr",
    # All other columns are already clean — listed here for documentation
    # "timestamp", "merchant_category", "transaction_status",
    # "sender_age_group", "receiver_age_group", "sender_state",
    # "sender_bank", "receiver_bank", "device_type", "network_type",
    # "fraud_flag", "hour_of_day", "day_of_week", "is_weekend"
}

# ---------------------------------------------------------------------------
# SYSTEM-WIDE CONSTANTS (derived from EDA — do not change without re-running EDA)
# ---------------------------------------------------------------------------
CONSTANTS = {
    # Amount thresholds
    "HIGH_VALUE_THRESHOLD":     3236.00,   # P90 of amount_inr
    "P25_AMOUNT":                288.00,
    "P50_AMOUNT":                629.00,
    "P75_AMOUNT":               1596.00,
    "P95_AMOUNT":               4687.05,
    "P99_AMOUNT":               9003.01,
    "MEAN_AMOUNT":              1311.76,

    # Baseline failure rates (%) — used for anchoring all comparisons
    "OVERALL_FAILURE_RATE":        4.95,
    "FAILURE_RATE_P2P":            4.96,
    "FAILURE_RATE_P2M":            4.95,
    "FAILURE_RATE_BILL_PAYMENT":   4.88,
    "FAILURE_RATE_RECHARGE":       5.09,

    # Fraud flag baselines
    "OVERALL_FLAG_RATE":           0.19,   # % of all transactions
    "HIGH_VALUE_FLAG_RATE":        0.25,   # % of P90+ transactions
    "FLAGGED_FAILURE_RATE":        4.38,   # failure rate *within* flagged txns

    # Volume
    "TOTAL_TRANSACTIONS":       250000,
    "TOTAL_FAILED":              12376,
    "TOTAL_FLAGGED":               480,

    # Temporal
    "PEAK_HOUR":                    19,    # 19:00 has highest transaction volume
    "WEEKEND_FAILURE_RATE":        5.09,
    "WEEKDAY_FAILURE_RATE":        4.89,

    # Low-sample warning threshold
    "MIN_SAMPLE_SIZE":             200,    # segments below this get a confidence warning
}

# ---------------------------------------------------------------------------
# VALID CATEGORICAL VALUES
# Used by query_parser.py to validate extracted entities
# ---------------------------------------------------------------------------
VALID_VALUES = {
    "transaction_type":    ["P2P", "P2M", "Bill Payment", "Recharge"],
    "merchant_category":   ["Food", "Grocery", "Fuel", "Entertainment",
                            "Shopping", "Healthcare", "Education",
                            "Transport", "Utilities", "Other"],
    "transaction_status":  ["SUCCESS", "FAILED"],
    "sender_age_group":    ["18-25", "26-35", "36-45", "46-55", "56+"],
    "receiver_age_group":  ["18-25", "26-35", "36-45", "46-55", "56+"],
    "sender_state":        ["Delhi", "Maharashtra", "Karnataka", "Tamil Nadu",
                            "Uttar Pradesh", "Gujarat", "Rajasthan",
                            "Telangana", "West Bengal", "Andhra Pradesh"],
    "sender_bank":         ["SBI", "HDFC", "ICICI", "Axis", "PNB",
                            "Kotak", "IndusInd", "Yes Bank"],
    "receiver_bank":       ["SBI", "HDFC", "ICICI", "Axis", "PNB",
                            "Kotak", "IndusInd", "Yes Bank"],
    "device_type":         ["Android", "iOS", "Web"],
    "network_type":        ["4G", "5G", "WiFi", "3G"],
    "day_of_week":         ["Monday", "Tuesday", "Wednesday", "Thursday",
                            "Friday", "Saturday", "Sunday"],
}

# ---------------------------------------------------------------------------
# MODULE-LEVEL CACHE
# The DataFrame is loaded once and reused across all calls.
# ---------------------------------------------------------------------------
_df_cache = None


def get_dataframe(path: str = DATASET_PATH, force_reload: bool = False) -> pd.DataFrame:
    """
    Load, clean, and return the transactions DataFrame.

    Uses module-level caching so the CSV is only read once per session.
    Pass force_reload=True to re-read from disk (useful in notebooks).

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame with normalised column names, parsed timestamp,
        and a derived `is_failed` boolean column.
    """
    global _df_cache

    if _df_cache is not None and not force_reload:
        return _df_cache

    # --- Load ---
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Dataset not found at: {path}\n"
            f"Set the INSIGHTX_DATA_PATH environment variable to override."
        )

    df = pd.read_csv(path)

    # --- Rename columns ---
    df = df.rename(columns=COLUMN_RENAME_MAP)

    # --- Parse timestamp ---
    # Raw format: "08-10-2024 15.17" (DD-MM-YYYY HH.MM)
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="%d-%m-%Y %H.%M")

    # --- Derived convenience columns ---
    # is_failed makes failure-rate computations cleaner downstream
    df["is_failed"] = (df["transaction_status"] == "FAILED").astype(int)

    # --- Basic integrity check ---
    _validate(df)

    _df_cache = df
    return df


def _validate(df: pd.DataFrame) -> None:
    """
    Run lightweight integrity checks after loading.
    Raises ValueError if anything looks wrong.
    Prints a summary if all checks pass.
    """
    errors = []

    # Check expected columns exist
    expected_cols = [
        "transaction_id", "timestamp", "transaction_type", "merchant_category",
        "amount_inr", "transaction_status", "sender_age_group", "receiver_age_group",
        "sender_state", "sender_bank", "receiver_bank", "device_type", "network_type",
        "fraud_flag", "hour_of_day", "day_of_week", "is_weekend"
    ]
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        errors.append(f"Missing expected columns after rename: {missing}")

    # No duplicate transaction IDs
    dupes = df["transaction_id"].duplicated().sum()
    if dupes > 0:
        errors.append(f"Found {dupes} duplicate transaction_ids")

    # No negative or zero amounts
    bad_amounts = (df["amount_inr"] <= 0).sum()
    if bad_amounts > 0:
        errors.append(f"Found {bad_amounts} transactions with amount <= 0")

    # fraud_flag should only be 0 or 1
    bad_flags = (~df["fraud_flag"].isin([0, 1])).sum()
    if bad_flags > 0:
        errors.append(f"Found {bad_flags} rows with unexpected fraud_flag values")

    # transaction_status should only be SUCCESS or FAILED
    bad_status = (~df["transaction_status"].isin(["SUCCESS", "FAILED"])).sum()
    if bad_status > 0:
        errors.append(f"Found {bad_status} rows with unexpected transaction_status values")

    if errors:
        raise ValueError("Data validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    print(f"[data_loader] ✓ Dataset loaded: {len(df):,} rows, {len(df.columns)} columns")
    print(f"[data_loader] ✓ All validation checks passed")


def get_constants() -> dict:
    """Return the EDA-derived system constants."""
    return CONSTANTS


def get_valid_values() -> dict:
    """Return valid categorical values for entity validation."""
    return VALID_VALUES


def get_high_value_df() -> pd.DataFrame:
    """Return only transactions above the P90 high-value threshold."""
    df = get_dataframe()
    return df[df["amount_inr"] >= CONSTANTS["HIGH_VALUE_THRESHOLD"]].copy()


def get_subset(
    transaction_type: str = None,
    sender_bank: str = None,
    receiver_bank: str = None,
    device_type: str = None,
    network_type: str = None,
    sender_age_group: str = None,
    sender_state: str = None,
    merchant_category: str = None,
    is_weekend: int = None,
    hour_of_day: int = None,
    transaction_status: str = None,
) -> pd.DataFrame:
    """
    Return a filtered subset of the DataFrame based on any combination of filters.

    This is a convenience function used by analytics_engine.py to apply
    filters from the parsed query intent before running aggregations.

    All parameters are optional. Passing None skips that filter.

    Returns
    -------
    pd.DataFrame
        Filtered copy of the main DataFrame.
    """
    df = get_dataframe()
    mask = pd.Series([True] * len(df), index=df.index)

    if transaction_type is not None:
        mask &= df["transaction_type"] == transaction_type
    if sender_bank is not None:
        mask &= df["sender_bank"] == sender_bank
    if receiver_bank is not None:
        mask &= df["receiver_bank"] == receiver_bank
    if device_type is not None:
        mask &= df["device_type"] == device_type
    if network_type is not None:
        mask &= df["network_type"] == network_type
    if sender_age_group is not None:
        mask &= df["sender_age_group"] == sender_age_group
    if sender_state is not None:
        mask &= df["sender_state"] == sender_state
    if merchant_category is not None:
        mask &= df["merchant_category"] == merchant_category
    if is_weekend is not None:
        mask &= df["is_weekend"] == is_weekend
    if hour_of_day is not None:
        mask &= df["hour_of_day"] == hour_of_day
    if transaction_status is not None:
        mask &= df["transaction_status"] == transaction_status

    return df[mask].copy()


def sample_size_warning(n: int) -> str | None:
    """
    Return a warning string if sample size is below the minimum threshold.
    Returns None if sample size is adequate.

    Used by analytics_engine.py to attach confidence notes to responses.
    """
    if n < CONSTANTS["MIN_SAMPLE_SIZE"]:
        return (
            f"⚠️ Low sample size ({n} transactions). "
            f"Interpret this result with caution."
        )
    return None


# ---------------------------------------------------------------------------
# Quick self-test — run this file directly to verify loading works
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    df = get_dataframe()
    print(f"\nColumn names: {list(df.columns)}")
    print(f"\nFirst row:\n{df.iloc[0]}")
    print(f"\nHIGH_VALUE_THRESHOLD: ₹{CONSTANTS['HIGH_VALUE_THRESHOLD']:,.2f}")
    print(f"OVERALL_FAILURE_RATE: {CONSTANTS['OVERALL_FAILURE_RATE']}%")