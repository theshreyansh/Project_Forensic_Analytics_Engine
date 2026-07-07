"""
=========================================================
ERP Fraud Analytics
Deloitte Forensic Investigation Workbench
=========================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

from config import DATA_DIR, OUTPUT_DIR

st.set_page_config(
    page_title="ERP Analytics",
    page_icon="📑",
    layout="wide"
)

st.title("📑 ERP Fraud Analytics")

# ---------------------------------------------------
# Load Data
# ---------------------------------------------------

cases = pd.read_csv(OUTPUT_DIR / "case_queue.csv")
vendors = pd.read_csv(DATA_DIR / "vendor_master.csv")
payments = pd.read_csv(DATA_DIR / "payments.csv")
invoices = pd.read_csv(DATA_DIR / "invoice_header.csv")

analysis = st.sidebar.selectbox(
    "Select Investigation Test",
    [
        "Overview",
        "Duplicate Payments",
        "Invoice Splitting",
        "Shared Bank Accounts",
        "Vendor Similarity",
        "Approval Overrides"
    ]
)

# ===================================================
# Overview
# ===================================================

if analysis == "Overview":

    st.subheader("Fraud Detection Summary")

    summary = pd.DataFrame({
        "Rule":[
            "Duplicate Payments",
            "Invoice Splitting",
            "Shared Bank",
            "Vendor Similarity",
            "Approval Override"
        ],
        "Cases":[
            cases["duplicate_payment"].sum(),
            cases["invoice_split"].sum(),
            cases["shared_bank"].sum(),
            cases["vendor_similarity"].sum(),
            cases["approval_override"].sum()
        ]
    })

    fig = px.bar(
        summary,
        x="Rule",
        y="Cases",
        title="Fraud Indicators"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(summary, use_container_width=True)

# ===================================================
# Duplicate Payments
# ===================================================

elif analysis == "Duplicate Payments":

    st.subheader("Duplicate Payment Analysis")

    st.info("""
Business Rule

Payments with identical amount and repeated occurrence
should be investigated.
""")

    duplicates = cases[cases.duplicate_payment == 1]

    st.metric("Flagged Payments", len(duplicates))

    st.dataframe(
        duplicates[
            [
                "case_id",
                "invoice_id",
                "vendor_id",
                "risk_score",
                "reason"
            ]
        ],
        use_container_width=True
    )

# ===================================================
# Invoice Splitting
# ===================================================

elif analysis == "Invoice Splitting":

    st.subheader("Invoice Splitting")

    flagged = cases[cases.invoice_split == 1]

    st.metric("Potential Invoice Splits", len(flagged))

    fig = px.histogram(
        flagged,
        x="invoice_amount",
        nbins=30,
        title="Invoice Amount Distribution"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(flagged, use_container_width=True)

# ===================================================
# Shared Bank Accounts
# ===================================================

elif analysis == "Shared Bank Accounts":

    st.subheader("Shared Bank Account Analysis")

    bank_summary = (
        vendors
        .groupby("bank_account")
        .size()
        .reset_index(name="Vendor Count")
    )

    bank_summary = bank_summary[
        bank_summary["Vendor Count"] > 1
    ]

    st.metric(
        "Shared Bank Accounts",
        len(bank_summary)
    )

    st.dataframe(
        bank_summary,
        use_container_width=True
    )

# ===================================================
# Vendor Similarity
# ===================================================

elif analysis == "Vendor Similarity":

    st.subheader("Vendor Alias Detection")

    flagged = cases[
        cases.vendor_similarity == 1
    ]

    st.metric(
        "Potential Vendor Aliases",
        len(flagged)
    )

    st.dataframe(
        flagged[
            [
                "vendor_id",
                "risk_score",
                "reason"
            ]
        ],
        use_container_width=True
    )

# ===================================================
# Approval Overrides
# ===================================================

elif analysis == "Approval Overrides":

    st.subheader("Approval Override Analysis")

    flagged = cases[
        cases.approval_override == 1
    ]

    st.metric(
        "Approval Overrides",
        len(flagged)
    )

    fig = px.pie(
        flagged,
        names="risk_level",
        title="Risk Distribution"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.dataframe(
        flagged,
        use_container_width=True
    )

# ---------------------------------------------------
# Export
# ---------------------------------------------------

st.divider()

st.download_button(
    "⬇ Export Investigation Results",
    data=cases.to_csv(index=False),
    file_name="ERP_Analytics.csv",
    mime="text/csv"
)