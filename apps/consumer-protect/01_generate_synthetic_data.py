"""
SATARK Synthetic Dataset Generator
Produces four datasets:
  1. transactions_raw.json      — 150,000 UPI transaction events
  2. vpa_registry.csv           — 50,000 virtual payment address records
  3. device_sessions.json       — 150,000 device/session records
  4. complaints.csv             — 5,000 post-fraud complaint records

Run locally: python 01_generate_synthetic_data.py
Output directory: ./satark_data/
Upload satark_data/ to dbfs:/satark/landing/ after generation.

Dependencies: pandas, numpy, faker
Install: pip install pandas numpy faker
"""

import json
import os
import random
import sys
import uuid
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.pii_masking import mask, bucket_amount, bucket_to_numeric
from utils.remark_corpus import (
    LEGITIMATE,
    SCAM_CORPUS,
    FRAUD_TYPE_WEIGHTS,
    ALL_FRAUD_TYPES,
    NOISE_SUFFIXES,
    NOISE_PREFIXES,
)

try:
    from faker import Faker
except ImportError:
    print("ERROR: faker is not installed. Run: pip install faker")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Configuration — change these if you want different volumes
# ---------------------------------------------------------------------------

RANDOM_SEED = 42
N_TRANSACTIONS = 150_000
N_VPA_RECORDS = 50_000
N_COMPLAINTS = 5_000

FRAUD_RATE = 0.07               # 7% of transactions are fraud
N_MULE_VPAS = 5_000             # how many VPAs in the fraud pool
N_LEGIT_VPAS = N_VPA_RECORDS - N_MULE_VPAS

OUTPUT_DIR = "./satark_data"

# Indian state weights (proportional to approximate UPI transaction volume)
STATE_NAMES = [
    "Maharashtra", "Karnataka", "Tamil Nadu", "Telangana", "Gujarat",
    "Delhi", "Uttar Pradesh", "West Bengal", "Rajasthan", "Madhya Pradesh",
    "Andhra Pradesh", "Haryana", "Punjab", "Kerala", "Bihar",
    "Jharkhand", "Odisha", "Assam", "Chhattisgarh", "Uttarakhand",
    "Himachal Pradesh", "Goa", "Tripura", "Meghalaya", "Manipur",
    "Nagaland", "Arunachal Pradesh", "Mizoram",
]

STATE_WEIGHTS = [
    0.16, 0.10, 0.09, 0.08, 0.08,
    0.07, 0.07, 0.06, 0.05, 0.04,
    0.04, 0.03, 0.03, 0.03, 0.02,
    0.02, 0.02, 0.01, 0.01, 0.01,
    0.01, 0.005, 0.005, 0.005, 0.005,
    0.005, 0.005, 0.005,
]

# Normalize state weights in case of floating point drift
_total = sum(STATE_WEIGHTS)
STATE_WEIGHTS = [w / _total for w in STATE_WEIGHTS]

# Amount distributions by fraud type (min, max, distribution)
# Using log-normal params (mu, sigma) for realistic skew
AMOUNT_PARAMS = {
    "LEGITIMATE":    {"mu": 7.0, "sigma": 1.5, "low": 10,    "high": 200_000},
    "KYC":           {"mu": 7.5, "sigma": 0.8, "low": 500,   "high": 5_000},
    "LOTTERY":       {"mu": 8.5, "sigma": 0.9, "low": 1_000, "high": 25_000},
    "TECH_SUPPORT":  {"mu": 7.8, "sigma": 0.8, "low": 500,   "high": 10_000},
    "IMPERSONATION": {"mu": 9.0, "sigma": 1.0, "low": 2_000, "high": 50_000},
    "JOB":           {"mu": 7.8, "sigma": 0.7, "low": 500,   "high": 8_000},
    "INVESTMENT":    {"mu": 9.5, "sigma": 1.2, "low": 5_000, "high": 100_000},
    "EMERGENCY":     {"mu": 9.2, "sigma": 1.0, "low": 2_000, "high": 50_000},
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

rng = np.random.default_rng(RANDOM_SEED)
random.seed(RANDOM_SEED)
fake = Faker("en_IN")
Faker.seed(RANDOM_SEED)


def make_vpa(name: str, suffix: str = "upi") -> str:
    """Generates a realistic fake VPA string."""
    clean = name.lower().replace(" ", "").replace(".", "")[:10]
    tag = random.randint(1, 999)
    return f"{clean}{tag}@{suffix}"


def make_device_hash(seed_str: str) -> str:
    """Generates a consistent fake device fingerprint hash."""
    return mask(f"device_{seed_str}")


def generate_timestamp(is_fraud: bool, base_date: datetime) -> datetime:
    """
    Generates a transaction timestamp.
    Fraud: skewed toward 8pm–11pm and weekends.
    Legitimate: distributed across business hours.
    """
    days_offset = rng.integers(0, 90)
    ts = base_date + timedelta(days=int(days_offset))

    if is_fraud:
        # 70% chance of being in the 8pm–11pm window
        if rng.random() < 0.70:
            hour = rng.integers(20, 23)
        else:
            hour = rng.integers(6, 23)
    else:
        # Legitimate: mostly business hours with evening peak
        if rng.random() < 0.50:
            hour = rng.integers(18, 22)
        elif rng.random() < 0.80:
            hour = rng.integers(9, 18)
        else:
            hour = rng.integers(6, 9)

    minute = rng.integers(0, 59)
    second = rng.integers(0, 59)
    return ts.replace(hour=int(hour), minute=int(minute), second=int(second))


def generate_amount(fraud_type: str) -> float:
    """Generates a realistic transaction amount for a given fraud type."""
    params = AMOUNT_PARAMS.get(fraud_type, AMOUNT_PARAMS["LEGITIMATE"])
    raw = np.exp(rng.normal(params["mu"], params["sigma"]))
    clipped = float(np.clip(raw, params["low"], params["high"]))

    # Fraud amounts are often round numbers (psychological manipulation)
    fraud_types = set(ALL_FRAUD_TYPES)
    if fraud_type in fraud_types and rng.random() < 0.40:
        clipped = round(clipped / 100) * 100

    return round(clipped, 2)


def pick_remark(fraud_type: str) -> str:
    """
    Picks a remark string from the appropriate corpus.
    Adds noise (prefix/suffix, typos) to ~15% of remarks.
    """
    if fraud_type == "LEGITIMATE":
        base = random.choice(LEGITIMATE)
    else:
        base = random.choice(SCAM_CORPUS[fraud_type])

    # Add noise to make the model harder
    if rng.random() < 0.10:
        base = random.choice(NOISE_PREFIXES) + base
    if rng.random() < 0.12:
        base = base + random.choice(NOISE_SUFFIXES)

    # Introduce a random typo to ~8% of remarks
    if rng.random() < 0.08 and len(base) > 5:
        pos = rng.integers(2, len(base) - 2)
        chars = list(base)
        chars[pos] = random.choice("abcdefghijklmnopqrstuvwxyz")
        base = "".join(chars)

    return base.strip()


def assign_fraud_label(
    remark_category: str,
    recipient_age_days: int,
    recipient_fan_in_7d: int,
    is_new_device: bool,
    amount: float,
) -> bool:
    """
    Rule-based fraud labeling. Used during generation so labels are consistent
    with feature signals — not pure random.
    """
    if remark_category != "LEGITIMATE":
        p = 0.85
        if recipient_age_days < 14:
            p += 0.08
        if recipient_fan_in_7d > 20:
            p += 0.05
        if is_new_device:
            p += 0.04
        return rng.random() < min(p, 0.98)
    else:
        # Hard negative cases: legit remark but fraud
        p = 0.01
        if is_new_device and amount > 10_000:
            p = 0.07
        return rng.random() < p


# ---------------------------------------------------------------------------
# Step 1: Generate VPA Registry
# ---------------------------------------------------------------------------

def generate_vpa_registry() -> pd.DataFrame:
    """
    Generates 50,000 VPA records.
    5,000 are synthetic mule accounts used by fraud transactions.
    45,000 are legitimate recipient VPAs.
    """
    print("  Generating VPA registry...")
    records = []

    # Mule VPAs (fraud recipients)
    mule_suffixes = ["paytm", "upi", "okaxis", "okicici", "oksbi", "okhdfcbank", "ybl"]
    for i in range(N_MULE_VPAS):
        raw_vpa = make_vpa(fake.first_name(), random.choice(mule_suffixes))
        records.append({
            "vpa_hash": mask(raw_vpa),
            "registration_age_days": int(rng.integers(0, 14)),
            "vpa_type": random.choice(["P2P", "P2P", "P2P", "BUSINESS"]),
            "kyc_level": int(rng.choice([0, 1], p=[0.6, 0.4])),
            "cumulative_received_30d": float(round(
                rng.uniform(5_000, 200_000), 2
            )),
            "unique_senders_7d": int(rng.integers(15, 80)),
            "is_synthetic_mule": True,
        })

    # Legitimate VPAs
    legit_suffixes = ["upi", "okaxis", "okicici", "oksbi", "okhdfcbank", "ybl", "paytm", "apl"]
    for i in range(N_LEGIT_VPAS):
        raw_vpa = make_vpa(fake.name(), random.choice(legit_suffixes))
        age = int(rng.choice(
            [30, 90, 180, 365, 730, 1200],
            p=[0.05, 0.10, 0.20, 0.30, 0.25, 0.10]
        ))
        records.append({
            "vpa_hash": mask(raw_vpa),
            "registration_age_days": age,
            "vpa_type": random.choice(["P2P", "P2P", "P2M", "BUSINESS"]),
            "kyc_level": int(rng.choice([0, 1, 2], p=[0.05, 0.30, 0.65])),
            "cumulative_received_30d": float(round(
                np.exp(rng.normal(8.0, 1.5)), 2
            )),
            "unique_senders_7d": int(rng.integers(1, 15)),
            "is_synthetic_mule": False,
        })

    df = pd.DataFrame(records)
    print(f"    VPA registry: {len(df):,} rows | mule VPAs: {N_MULE_VPAS:,}")
    return df


# ---------------------------------------------------------------------------
# Step 2: Generate Transaction Events
# ---------------------------------------------------------------------------

def generate_transactions(vpa_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates 150,000 UPI transaction events with fraud labels.
    Fraud transactions are routed to mule VPAs.
    Legitimate transactions are routed to legitimate VPAs.
    """
    print("  Generating transactions...")

    mule_hashes = vpa_df[vpa_df["is_synthetic_mule"]]["vpa_hash"].tolist()
    legit_hashes = vpa_df[~vpa_df["is_synthetic_mule"]]["vpa_hash"].tolist()

    # Create a lookup for recipient features (needed for label assignment)
    vpa_lookup = (
        vpa_df
        .drop_duplicates(subset=["vpa_hash"])
        .set_index("vpa_hash")[["registration_age_days", "unique_senders_7d"]]
        .to_dict("index")
    )

    n_fraud = int(N_TRANSACTIONS * FRAUD_RATE)
    n_legit = N_TRANSACTIONS - n_fraud

    # Choose fraud types according to real-world distribution
    fraud_type_choices = rng.choice(
        ALL_FRAUD_TYPES,
        size=n_fraud,
        p=list(FRAUD_TYPE_WEIGHTS.values()),
    )

    # Build pool of fake sender VPAs (not in the registry — they are senders)
    sender_pool_size = 10_000
    sender_vpas_raw = [make_vpa(fake.name()) for _ in range(sender_pool_size)]
    sender_hashes = [mask(v) for v in sender_vpas_raw]
    sender_states = rng.choice(STATE_NAMES, size=sender_pool_size, p=STATE_WEIGHTS)
    sender_base_devices = [make_device_hash(f"sender_{i}") for i in range(sender_pool_size)]

    # Precompute device histories per sender (to determine is_new_device)
    # A sender who changes device recently gets is_new_device=True
    sender_device_change_prob = rng.random(sender_pool_size)

    base_date = datetime(2024, 1, 1)
    records = []

    # --- Fraud transactions ---
    print(f"    Generating {n_fraud:,} fraud transactions...")
    for i in range(n_fraud):
        fraud_type = fraud_type_choices[i]
        sender_idx = rng.integers(0, sender_pool_size)
        amount = generate_amount(fraud_type)
        recipient_hash = random.choice(mule_hashes)
        vpa_info = vpa_lookup.get(recipient_hash, {"registration_age_days": 7, "unique_senders_7d": 30})

        is_new_device = bool(sender_device_change_prob[sender_idx] > 0.65)
        # Fraud: higher chance of device mismatch
        if rng.random() < 0.35:
            is_new_device = True

        is_fraud = assign_fraud_label(
            remark_category=fraud_type,
            recipient_age_days=vpa_info["registration_age_days"],
            recipient_fan_in_7d=vpa_info["unique_senders_7d"],
            is_new_device=is_new_device,
            amount=amount,
        )

        sender_state = str(sender_states[sender_idx])
        ip_state_match = bool(rng.random() > 0.25)  # 25% IP mismatch for fraud

        records.append({
            "txn_id": str(uuid.uuid4()),
            "sender_vpa_hash": sender_hashes[sender_idx],
            "recipient_vpa_hash": recipient_hash,
            "amount_bucket": bucket_amount(amount),
            "amount_numeric": amount,
            "upi_remark": pick_remark(fraud_type),
            "txn_timestamp": generate_timestamp(True, base_date).isoformat(),
            "sender_state": sender_state,
            "device_hash": sender_base_devices[sender_idx] if not is_new_device
                           else make_device_hash(f"new_{i}"),
            "is_new_device": is_new_device,
            "ip_state_match": ip_state_match,
            "is_fraud": is_fraud,
            "fraud_type": fraud_type,
        })

    # --- Legitimate transactions ---
    print(f"    Generating {n_legit:,} legitimate transactions...")
    for i in range(n_legit):
        sender_idx = rng.integers(0, sender_pool_size)
        amount = generate_amount("LEGITIMATE")
        recipient_hash = random.choice(legit_hashes)
        vpa_info = vpa_lookup.get(recipient_hash, {"registration_age_days": 400, "unique_senders_7d": 3})

        is_new_device = bool(sender_device_change_prob[sender_idx] > 0.90)
        # Most legit senders use known devices
        sender_state = str(sender_states[sender_idx])

        is_fraud = assign_fraud_label(
            remark_category="LEGITIMATE",
            recipient_age_days=vpa_info["registration_age_days"],
            recipient_fan_in_7d=vpa_info["unique_senders_7d"],
            is_new_device=is_new_device,
            amount=amount,
        )

        records.append({
            "txn_id": str(uuid.uuid4()),
            "sender_vpa_hash": sender_hashes[sender_idx],
            "recipient_vpa_hash": recipient_hash,
            "amount_bucket": bucket_amount(amount),
            "amount_numeric": amount,
            "upi_remark": pick_remark("LEGITIMATE"),
            "txn_timestamp": generate_timestamp(False, base_date).isoformat(),
            "sender_state": sender_state,
            "device_hash": sender_base_devices[sender_idx] if not is_new_device
                           else make_device_hash(f"legit_new_{i}"),
            "is_new_device": is_new_device,
            "ip_state_match": bool(rng.random() > 0.05),
            "is_fraud": is_fraud,
            "fraud_type": "LEGITIMATE",
        })

    df = pd.DataFrame(records)
    df = df.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)

    fraud_count = df["is_fraud"].sum()
    print(f"    Transactions: {len(df):,} rows | actual fraud: {fraud_count:,} ({fraud_count/len(df)*100:.1f}%)")
    print(f"    Fraud type distribution:")
    for ft, count in df[df["is_fraud"]]["fraud_type"].value_counts().items():
        print(f"      {ft}: {count:,}")

    return df


# ---------------------------------------------------------------------------
# Step 3: Generate Device Sessions
# ---------------------------------------------------------------------------

def generate_device_sessions(txn_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates one device session record per transaction.
    Fraud sessions are shorter, more likely to use VPN, and have fewer screen taps.
    """
    print("  Generating device sessions...")
    records = []

    for _, row in txn_df.iterrows():
        is_fraud = row["is_fraud"]

        if is_fraud:
            session_duration = int(rng.integers(20, 120))
            is_vpn = bool(rng.random() < 0.18)
            nav_count = int(rng.integers(2, 6))
        else:
            session_duration = int(rng.integers(60, 600))
            is_vpn = bool(rng.random() < 0.02)
            nav_count = int(rng.integers(5, 25))

        records.append({
            "txn_id": row["txn_id"],
            "session_duration_sec": session_duration,
            "is_vpn_flag": is_vpn,
            "page_navigation_count": nav_count,
            "device_hash": row["device_hash"],
        })

    df = pd.DataFrame(records)
    print(f"    Device sessions: {len(df):,} rows")
    return df


# ---------------------------------------------------------------------------
# Step 4: Generate Complaints
# ---------------------------------------------------------------------------

def generate_complaints(txn_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates 5,000 post-fraud complaint records from a sample of fraud transactions.
    Not every fraud transaction gets a complaint (victims don't always report).
    """
    print("  Generating complaints...")

    fraud_txns = txn_df[txn_df["is_fraud"]].copy()

    if len(fraud_txns) < N_COMPLAINTS:
        print(f"    WARNING: Only {len(fraud_txns):,} fraud rows available; "
              f"generating {len(fraud_txns):,} complaints instead of {N_COMPLAINTS:,}")
        sample = fraud_txns
    else:
        sample = fraud_txns.sample(n=N_COMPLAINTS, random_state=RANDOM_SEED)

    bank_ids = ["SBI001", "HDFC002", "ICICI003", "AXIS004", "KOTAK005",
                "PNB006", "BOB007", "CANARA008", "UNION009", "INDUS010"]

    records = []
    for _, row in sample.iterrows():
        txn_ts = datetime.fromisoformat(row["txn_timestamp"])
        # Complaints filed 1–72 hours after fraud
        delay_hours = float(rng.uniform(1, 72))
        complaint_ts = txn_ts + timedelta(hours=delay_hours)

        # Status distribution: most open, some resolved
        status_roll = rng.random()
        if status_roll < 0.55:
            status = "OPEN"
            resolution_days = None
        elif status_roll < 0.75:
            status = "ESCALATED"
            resolution_days = None
        else:
            status = "RESOLVED"
            resolution_days = int(rng.integers(3, 89))

        records.append({
            "complaint_id": f"SATARK-{str(uuid.uuid4())[:8].upper()}",
            "txn_id": row["txn_id"],
            "sender_vpa_hash": row["sender_vpa_hash"],
            "complaint_ts": complaint_ts.isoformat(),
            "scam_type": row["fraud_type"],
            "amount_bucket": row["amount_bucket"],
            "complaint_status": status,
            "resolution_days": resolution_days,
            "bank_id": random.choice(bank_ids),
        })

    df = pd.DataFrame(records)
    print(f"    Complaints: {len(df):,} rows")
    print(f"    Status breakdown:")
    for status, count in df["complaint_status"].value_counts().items():
        print(f"      {status}: {count:,}")
    return df


# ---------------------------------------------------------------------------
# Step 5: Write outputs
# ---------------------------------------------------------------------------

def write_outputs(
    txn_df: pd.DataFrame,
    vpa_df: pd.DataFrame,
    session_df: pd.DataFrame,
    complaint_df: pd.DataFrame,
) -> None:
    """Writes all four datasets to the output directory."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"  Writing transactions_raw.json ...")
    txn_path = os.path.join(OUTPUT_DIR, "transactions_raw.json")
    txn_df.to_json(txn_path, orient="records", lines=True, date_format="iso")
    size_mb = os.path.getsize(txn_path) / (1024 * 1024)
    print(f"    -> {txn_path} ({size_mb:.1f} MB)")

    print(f"  Writing vpa_registry.csv ...")
    vpa_path = os.path.join(OUTPUT_DIR, "vpa_registry.csv")
    # Drop is_synthetic_mule before export — it's a generation artifact, not a feature
    vpa_export = vpa_df.drop(columns=["is_synthetic_mule"])
    vpa_export.to_csv(vpa_path, index=False)
    size_mb = os.path.getsize(vpa_path) / (1024 * 1024)
    print(f"    -> {vpa_path} ({size_mb:.1f} MB)")

    print(f"  Writing device_sessions.json ...")
    session_path = os.path.join(OUTPUT_DIR, "device_sessions.json")
    session_df.to_json(session_path, orient="records", lines=True)
    size_mb = os.path.getsize(session_path) / (1024 * 1024)
    print(f"    -> {session_path} ({size_mb:.1f} MB)")

    print(f"  Writing complaints.csv ...")
    complaint_path = os.path.join(OUTPUT_DIR, "complaints.csv")
    complaint_df.to_csv(complaint_path, index=False)
    size_mb = os.path.getsize(complaint_path) / (1024 * 1024)
    print(f"    -> {complaint_path} ({size_mb:.1f} MB)")


# ---------------------------------------------------------------------------
# Step 6: Print summary and validation
# ---------------------------------------------------------------------------

def print_summary(txn_df: pd.DataFrame, vpa_df: pd.DataFrame) -> None:
    """Prints a quick sanity-check summary after generation."""
    print("\n" + "=" * 60)
    print("GENERATION SUMMARY")
    print("=" * 60)

    print(f"\nTransactions: {len(txn_df):,}")
    print(f"  Fraud rows: {txn_df['is_fraud'].sum():,} ({txn_df['is_fraud'].mean()*100:.1f}%)")
    print(f"  Unique senders: {txn_df['sender_vpa_hash'].nunique():,}")
    print(f"  Unique recipients: {txn_df['recipient_vpa_hash'].nunique():,}")
    print(f"  Amount bucket distribution:")
    for bucket, count in txn_df["amount_bucket"].value_counts().sort_index().items():
        print(f"    {bucket}: {count:,}")
    print(f"  Date range: {txn_df['txn_timestamp'].min()} to {txn_df['txn_timestamp'].max()}")

    print(f"\nVPA Registry: {len(vpa_df):,}")
    print(f"  Mule VPAs (age < 14 days): {(vpa_df['registration_age_days'] < 14).sum():,}")
    print(f"  KYC level 0 (minimal): {(vpa_df['kyc_level'] == 0).sum():,}")
    print(f"  High fan-in (>20 senders): {(vpa_df['unique_senders_7d'] > 20).sum():,}")

    print(f"\nPII masking check:")
    sample_hash = txn_df["sender_vpa_hash"].iloc[0]
    print(f"  Sample sender_vpa_hash: {sample_hash} (length: {len(sample_hash)})")
    assert len(sample_hash) == 16, "FAIL: VPA hash is not 16 characters"
    assert "@" not in sample_hash, "FAIL: Raw VPA leaked into hash field"
    print(f"  PII masking: PASS")

    print(f"\nOutput directory: {os.path.abspath(OUTPUT_DIR)}")
    total_size = sum(
        os.path.getsize(os.path.join(OUTPUT_DIR, f))
        for f in os.listdir(OUTPUT_DIR)
    ) / (1024 * 1024)
    print(f"Total output size: {total_size:.1f} MB")
    print("=" * 60)
    print("\nNext step: upload satark_data/ to dbfs:/satark/landing/")
    print("  databricks fs cp -r ./satark_data dbfs:/satark/landing/ --overwrite")
    print("  or use the Databricks UI to upload files.")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("SATARK Synthetic Data Generator")
    print("=" * 60)
    print(f"Random seed: {RANDOM_SEED}")
    print(f"Target transactions: {N_TRANSACTIONS:,}")
    print(f"Target VPA records: {N_VPA_RECORDS:,}")
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    print("[1/5] Generating VPA registry...")
    vpa_df = generate_vpa_registry()

    print("\n[2/5] Generating transaction events...")
    txn_df = generate_transactions(vpa_df)

    print("\n[3/5] Generating device sessions...")
    session_df = generate_device_sessions(txn_df)

    print("\n[4/5] Generating complaints...")
    complaint_df = generate_complaints(txn_df)

    print("\n[5/5] Writing output files...")
    write_outputs(txn_df, vpa_df, session_df, complaint_df)

    print_summary(txn_df, vpa_df)


if __name__ == "__main__":
    main()