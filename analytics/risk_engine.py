"""
=========================================================
Risk Scoring Engine
Deloitte Forensic Investigation Workbench
=========================================================
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pathlib import Path
import pandas as pd
from rapidfuzz import fuzz

from config import DATA_DIR, OUTPUT_DIR, APPROVAL_THRESHOLD, RISK_WEIGHTS

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------
# Load Data
# --------------------------------------------------------

vendors = pd.read_csv(DATA_DIR / "vendor_master.csv")
invoices = pd.read_csv(DATA_DIR / "invoice_header.csv")
payments = pd.read_csv(DATA_DIR / "payments.csv")
approvals = pd.read_csv(DATA_DIR / "approval_logs.csv")
emails = pd.read_csv(DATA_DIR / "emails.csv")


# --------------------------------------------------------
# Helper
# --------------------------------------------------------

def initialise_case_table(df):
    result = df.copy()

    result["duplicate_payment"] = 0
    result["invoice_split"] = 0
    result["shared_bank"] = 0
    result["vendor_similarity"] = 0
    result["approval_override"] = 0
    result["communication"] = 0

    result["risk_score"] = 0
    result["risk_level"] = "Low"
    result["reason"] = ""

    return result


cases = initialise_case_table(invoices)


# --------------------------------------------------------
# Rule 1
# Duplicate Payments
# --------------------------------------------------------

duplicate = payments.groupby(
    ["payment_amount"]
).filter(lambda x: len(x) > 1)

dup_invoice_ids = duplicate.invoice_id.unique()

cases.loc[
    cases.invoice_id.isin(dup_invoice_ids),
    "duplicate_payment"
] = 1


# --------------------------------------------------------
# Rule 2
# Invoice Splitting
# --------------------------------------------------------

cases.loc[
    cases.invoice_amount.between(
        APPROVAL_THRESHOLD - 3000,
        APPROVAL_THRESHOLD
    ),
    "invoice_split"
] = 1


# --------------------------------------------------------
# Rule 3
# Shared Bank Accounts
# --------------------------------------------------------

bank_counts = vendors.groupby(
    "bank_account"
).vendor_id.count()

shared = bank_counts[
    bank_counts > 1
].index

shared_vendors = vendors[
    vendors.bank_account.isin(shared)
].vendor_id

cases = cases.merge(
    vendors[["vendor_id", "bank_account"]],
    on="vendor_id",
    how="left"
)

cases.loc[
    cases.vendor_id.isin(shared_vendors),
    "shared_bank"
] = 1


# --------------------------------------------------------
# Rule 4
# Vendor Similarity
# --------------------------------------------------------

similar = set()

names = vendors.vendor_name.tolist()

for i in range(len(names)):

    for j in range(i + 1, len(names)):

        score = fuzz.ratio(names[i], names[j])

        if score >= 92:

            similar.add(names[i])
            similar.add(names[j])

vendor_ids = vendors[
    vendors.vendor_name.isin(similar)
].vendor_id

cases.loc[
    cases.vendor_id.isin(vendor_ids),
    "vendor_similarity"
] = 1


# --------------------------------------------------------
# Rule 5
# Communication Review
# --------------------------------------------------------

keywords = [
    "urgent",
    "approval",
    "bank",
    "invoice",
    "threshold",
    "payment"
]

flagged = emails[
    emails.body.str.contains(
        "|".join(keywords),
        case=False,
        na=False
    )
]

flag_vendor = flagged.vendor_id.unique()

cases.loc[
    cases.vendor_id.isin(flag_vendor),
    "communication"
] = 1


# --------------------------------------------------------
# Rule 6
# Approval Override
# --------------------------------------------------------

merged = approvals.merge(
    invoices,
    on="invoice_id"
)

override = merged[
    merged.invoice_amount > APPROVAL_THRESHOLD
]

cases.loc[
    cases.invoice_id.isin(
        override.invoice_id
    ),
    "approval_override"
] = 1


# --------------------------------------------------------
# Risk Score
# --------------------------------------------------------

cases["risk_score"] = (

    cases.duplicate_payment *
    RISK_WEIGHTS["duplicate_payment"]

    +

    cases.invoice_split *
    RISK_WEIGHTS["invoice_split"]

    +

    cases.shared_bank *
    RISK_WEIGHTS["shared_bank"]

    +

    cases.vendor_similarity *
    RISK_WEIGHTS["vendor_similarity"]

    +

    cases.communication *
    RISK_WEIGHTS["communication"]

    +

    cases.approval_override *
    RISK_WEIGHTS["approval_override"]

)


# --------------------------------------------------------
# Risk Level
# --------------------------------------------------------

def level(score):

    if score >= 90:
        return "Critical"

    if score >= 70:
        return "High"

    if score >= 40:
        return "Medium"

    return "Low"


cases["risk_level"] = cases.risk_score.apply(level)


# --------------------------------------------------------
# Investigation Reason
# --------------------------------------------------------

def build_reason(r):

    reasons = []

    if r.duplicate_payment:
        reasons.append("Duplicate Payment")

    if r.invoice_split:
        reasons.append("Invoice Splitting")

    if r.shared_bank:
        reasons.append("Shared Bank")

    if r.vendor_similarity:
        reasons.append("Vendor Alias")

    if r.communication:
        reasons.append("Communication")

    if r.approval_override:
        reasons.append("Approval Override")

    return ", ".join(reasons)


cases["reason"] = cases.apply(build_reason, axis=1)


# --------------------------------------------------------
# Ranking
# --------------------------------------------------------

cases = cases.sort_values(
    "risk_score",
    ascending=False
)

cases["case_id"] = [

    f"CASE{i:05}"

    for i in range(1, len(cases) + 1)

]


# --------------------------------------------------------
# Save
# --------------------------------------------------------

cases.to_csv(
    OUTPUT_DIR / "case_queue.csv",
    index=False
)

print("Risk Engine Completed")

print(
    cases[
        [
            "case_id",
            "invoice_id",
            "risk_score",
            "risk_level",
            "reason"
        ]
    ].head(20)
)