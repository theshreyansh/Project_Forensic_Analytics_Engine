"""
=========================================================
Executive Dashboard
Deloitte Forensic Investigation Workbench
=========================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

from config import OUTPUT_DIR

st.set_page_config(
    page_title="Executive Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Executive Investigation Dashboard")
st.caption("Procurement Fraud Investigation Accelerator")

CASE_FILE = OUTPUT_DIR / "case_queue.csv"

if not CASE_FILE.exists():
    st.error("Risk engine has not been executed.")
    st.info("Run analytics/risk_engine.py first.")
    st.stop()

cases = pd.read_csv(CASE_FILE)

# --------------------------------------------------
# KPIs
# --------------------------------------------------

critical = len(cases[cases.risk_level == "Critical"])
high = len(cases[cases.risk_level == "High"])
medium = len(cases[cases.risk_level == "Medium"])
low = len(cases[cases.risk_level == "Low"])

avg_score = round(cases.risk_score.mean(), 1)

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Cases", len(cases))
col2.metric("Critical", critical)
col3.metric("High", high)
col4.metric("Medium", medium)
col5.metric("Average Risk", avg_score)

st.divider()

# --------------------------------------------------
# Charts
# --------------------------------------------------

left, right = st.columns(2)

with left:

    fig = px.histogram(
        cases,
        x="risk_score",
        nbins=20,
        title="Risk Score Distribution"
    )

    st.plotly_chart(fig, use_container_width=True)

with right:

    summary = (
        cases.groupby("risk_level")
        .size()
        .reset_index(name="Cases")
    )

    fig = px.bar(
        summary,
        x="risk_level",
        y="Cases",
        title="Cases by Risk Level"
    )

    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# Top Cases
# --------------------------------------------------

st.subheader("Top Investigation Cases")

display_cols = [
    "case_id",
    "invoice_id",
    "vendor_id",
    "risk_score",
    "risk_level",
    "reason"
]

st.dataframe(
    cases[display_cols].head(20),
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# Executive Summary
# --------------------------------------------------

st.subheader("Executive Summary")

critical_pct = round((critical / len(cases)) * 100, 1)

st.success(f"""
• Total investigation cases identified: **{len(cases)}**

• Critical risk cases: **{critical} ({critical_pct}%)**

• Average composite risk score: **{avg_score}**

• Highest priority indicators include:
  - Duplicate payments
  - Shared bank accounts
  - Invoice splitting
  - Vendor aliases
  - Suspicious communications

**Recommendation**

Proceed with immediate legal review of Critical cases and
expand communication review to associated custodians.
""")