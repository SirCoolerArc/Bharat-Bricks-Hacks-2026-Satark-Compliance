"""
PII masking utilities for SATARK.
All masking is SHA-256 HMAC with a pepper. Amounts are bucketed.
Import this in any script that handles raw PII.
"""

import hashlib
import hmac
import os


def get_pepper() -> str:
    """
    Retrieve the masking pepper.
    On Databricks: reads from Databricks Secrets.
    Locally: reads from SATARK_PEPPER environment variable.
    Falls back to a hardcoded dev-only string — never use this in production.
    """
    try:
        # Databricks environment
        from dbutils import secrets  # noqa: F401 — only available in Databricks
        import dbutils as _dbutils
        return _dbutils.secrets.get(scope="satark", key="pii-pepper")
    except Exception:
        pass

    env_pepper = os.environ.get("SATARK_PEPPER")
    if env_pepper:
        return env_pepper

    # Dev fallback — clearly labeled, never used in production
    return "DEV_ONLY_PEPPER_DO_NOT_USE_IN_PROD_abc123xyz"


PEPPER = get_pepper()


def mask(value: str) -> str:
    """
    Returns the first 16 hex characters of HMAC-SHA256(pepper, value).
    Deterministic: same input always produces same output.
    Not reversible without the pepper.
    """
    if not value or not isinstance(value, str):
        return "UNKNOWN"
    canonical = value.lower().strip()
    h = hmac.new(PEPPER.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256)
    return h.hexdigest()[:16]


def bucket_amount(amount: float) -> str:
    """
    Converts a raw rupee amount into a risk bucket.
    XS < 500, S < 2000, M < 10000, L < 50000, XL >= 50000.
    Raw amounts are never stored beyond the Bronze landing zone.
    """
    if amount < 500:
        return "XS"
    if amount < 2000:
        return "S"
    if amount < 10000:
        return "M"
    if amount < 50000:
        return "L"
    return "XL"


def bucket_to_numeric(bucket: str) -> float:
    """
    Returns the midpoint value of an amount bucket.
    Used for z-score computation in feature engineering.
    """
    mapping = {"XS": 250.0, "S": 1250.0, "M": 6000.0, "L": 30000.0, "XL": 100000.0}
    return mapping.get(bucket, 6000.0)