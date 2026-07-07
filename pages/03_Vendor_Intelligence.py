"""
=========================================================
Vendor Intelligence
Deloitte Forensic Investigation Workbench
=========================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from rapidfuzz import fuzz

from config import DATA_DIR, OUTPUT_DIR

st.set_page_config(
    page_title="Vendor Intelligence",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 Vendor Intelligence")

# -------------------------------------------------------
# Load Data
# -------------------------------------------------------

vendors = pd.read_csv(DATA_DIR / "vendor_master.csv")
cases = pd.read_csv(OUTPUT_DIR / "case_queue.csv")
payments = pd.read_csv(DATA_DIR / "payments.csv")
invoices = pd.read_csv(DATA_DIR / "invoice_header.csv")
emails = pd.read_csv(DATA_DIR / "emails.csv")

# -------------------------------------------------------
# Search
# -------------------------------------------------------

vendor_list = sorted(vendors["vendor_name"].unique())

selected_vendor = st.selectbox(
    "Search Vendor",
    vendor_list
)

vendor = vendors[vendors["vendor_name"] == selected_vendor].iloc[0]
vendor_id = vendor["vendor_id"]

st.divider()

# -------------------------------------------------------
# Vendor Profile
# -------------------------------------------------------

c1, c2, c3, c4 = st.columns(4)

c1.metric("Vendor ID", vendor_id)
c2.metric("Country", vendor["country"])
c3.metric("Vendor Type", vendor["vendor_type"])
c4.metric("Bank Account", vendor["bank_account"])

st.divider()

# -------------------------------------------------------
# Transactions
# -------------------------------------------------------

vendor_invoices = invoices[invoices["vendor_id"] == vendor_id]

vendor_cases = cases[cases["vendor_id"] == vendor_id]

vendor_payments = payments[
    payments["invoice_id"].isin(
        vendor_invoices["invoice_id"]
    )
]

total_spend = vendor_invoices["invoice_amount"].sum()

left, right = st.columns(2)

with left:

    st.metric(
        "Invoices",
        len(vendor_invoices)
    )

    st.metric(
        "Payments",
        len(vendor_payments)
    )

with right:

    st.metric(
        "Total Spend",
        f"${total_spend:,.0f}"
    )

    st.metric(
        "Investigation Cases",
        len(vendor_cases)
    )

st.divider()

# -------------------------------------------------------
# Risk Indicators
# -------------------------------------------------------

st.subheader("Risk Indicators")

risk_cols = [
    "duplicate_payment",
    "invoice_split",
    "shared_bank",
    "vendor_similarity",
    "approval_override",
    "communication"
]

summary = []

for col in risk_cols:

    summary.append({
        "Indicator": col.replace("_", " ").title(),
        "Count": vendor_cases[col].sum()
    })

risk_df = pd.DataFrame(summary)

fig = px.bar(
    risk_df,
    x="Indicator",
    y="Count",
    title="Vendor Risk Profile"
)

st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------------
# Similar Vendor Names
# -------------------------------------------------------

st.subheader("Potential Vendor Aliases")

matches = []

for _, row in vendors.iterrows():

    if row["vendor_id"] == vendor_id:
        continue

    score = fuzz.ratio(
        selected_vendor,
        row["vendor_name"]
    )

    if score >= 85:

        matches.append({
            "Vendor": row["vendor_name"],
            "Vendor ID": row["vendor_id"],
            "Similarity": score
        })

if matches:

    st.dataframe(
        pd.DataFrame(matches)
        .sort_values(
            "Similarity",
            ascending=False
        ),
        use_container_width=True,
        hide_index=True
    )

else:

    st.success("No similar vendor names detected.")

st.divider()

# -------------------------------------------------------
# Communication Summary
# -------------------------------------------------------

st.subheader("Communication Review")

vendor_emails = emails[
    emails["vendor_id"] == vendor_id
]

st.metric(
    "Emails",
    len(vendor_emails)
)

if len(vendor_emails):

    st.dataframe(
        vendor_emails[
            [
                "email_id",
                "subject",
                "date"
            ]
        ].head(20),
        use_container_width=True,
        hide_index=True
    )

else:

    st.info("No emails available.")

st.divider()

# -------------------------------------------------------
# Investigation Cases
# -------------------------------------------------------

st.subheader("Associated Investigation Cases")

display = [
    "case_id",
    "invoice_id",
    "risk_score",
    "risk_level",
    "reason"
]

st.dataframe(
    vendor_cases[display],
    use_container_width=True,
    hide_index=True
)

# -------------------------------------------------------
# Investigator Assessment
# -------------------------------------------------------

highest = (
    vendor_cases["risk_score"].max()
    if not vendor_cases.empty else 0
)

if highest >= 90:

    st.error("""
### Investigator Recommendation

Immediate escalation recommended.

Expand custodian list.

Review vendor onboarding.

Validate bank account ownership.

Review all communications.
""")

elif highest >= 70:

    st.warning("""
### Investigator Recommendation

Detailed transaction testing recommended.

Review approvals and supporting documents.
""")

else:

    st.success("""
### Investigator Recommendation

Continue routine monitoring.
""")