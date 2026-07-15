"""
=========================================================
Executive Dashboard
Master Forensic Investigation Workbench
=========================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from config import OUTPUT_DIR
from utils.app_style import render_page_shell
from utils.chart_helpers import (
    apply_briefing_theme,
    detect_outliers,
    render_case_queue_snapshot,
    render_chart_context,
    render_red_flag_summary,
    style_chart_for_anomalies,
)

st.set_page_config(
    page_title="Executive Dashboard",
    page_icon="📊",
    layout="wide"
)

render_page_shell()

st.title("📊 Executive Investigation Dashboard")
st.caption("Procurement Fraud Investigation Accelerator")

st.markdown("<div style='padding:12px 14px; border-left:5px solid #012169; background:#f3f7ff; border-radius:8px; margin-bottom:16px;'>"
            "<b>Business callout:</b> ERP and communications signals indicate concentrated vendor risk and potential control circumvention."
            "</div>", unsafe_allow_html=True)

st.caption("Suggested action: prioritize legal preservation, threshold-band invoice testing, and shared-identifier review for the highest-risk vendors.")

CASE_FILE = OUTPUT_DIR / "case_queue.csv"

if not CASE_FILE.exists():
    st.error("Risk engine has not been executed.")
    st.info("Run analytics/risk_engine.py first.")
    st.stop()

cases = pd.read_csv(CASE_FILE)

critical = len(cases[cases.risk_level == "Critical"])
high = len(cases[cases.risk_level == "High"])
medium = len(cases[cases.risk_level == "Medium"])
low = len(cases[cases.risk_level == "Low"])

avg_score = round(cases.risk_score.mean(), 1)
critical_pct = round((critical / len(cases)) * 100, 1)

st.subheader("Executive Summary")
st.markdown("<div style='padding:14px; border-radius:10px; background:#ecfdf3; border:1px solid #8fe3a5;'>"
            f"<b>Executive summary:</b> {len(cases):,} cases are under review, with {critical} critical matters representing {critical_pct:.1f}% of the queue. "
            f"The average composite risk score is {avg_score:.1f}%. Recommended next steps include immediate legal review of critical matters and expansion of custodial review for shared-identifier clusters.</div>", unsafe_allow_html=True)

st.markdown("---")

# --------------------------------------------------
# KPIs
# --------------------------------------------------

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Cases", f"{len(cases):,}")
col2.metric("Critical", f"{critical:,}")
col3.metric("High", f"{high:,}")
col4.metric("Medium", f"{medium:,}")
col5.metric("Average Risk", f"{avg_score:.1f}%")

st.markdown("---")

st.divider()

# --------------------------------------------------
# Charts
# --------------------------------------------------

col_a, col_b = st.columns(2)
with col_a:
    fig = px.histogram(
        cases,
        x="risk_score",
        nbins=20,
        title="Risk Score Distribution",
        color_discrete_sequence=["#012169"]
    )
    fig.update_xaxes(title_text="Risk Score (%)")
    fig.update_yaxes(title_text="Case Count")
    fig = apply_briefing_theme(fig)
    anomaly_mask = detect_outliers(cases["risk_score"])
    fig = style_chart_for_anomalies(fig, cases["risk_score"], anomaly_mask)
    st.plotly_chart(fig, use_container_width=True)
    render_chart_context("Critical cases cluster at the upper tail of the score distribution.", "Prioritize legal preservation and targeted evidence collection for the highest-scoring queues.")

with col_b:
    summary = cases.groupby("risk_level").size().reset_index(name="Cases")
    fig = px.bar(
        summary,
        x="risk_level",
        y="Cases",
        title="Cases by Risk Level",
        color="risk_level",
        color_discrete_map={"Critical":"#D62728","High":"#FF7F0E","Medium":"#F1C40F","Low":"#2ECC71"}
    )
    fig.update_yaxes(title_text="Case Count")
    fig = apply_briefing_theme(fig)
    fig = style_chart_for_anomalies(fig, summary["Cases"], pd.Series([summary["Cases"].max() == value for value in summary["Cases"]]))
    st.plotly_chart(fig, use_container_width=True)
    render_chart_context("The highest-risk bucket is concentrated in Critical and High cases.", "Allocate investigation capacity to the most severe risk bands first.")

col_c, col_d = st.columns(2)
with col_c:
    amount_series = cases.sort_values("risk_score")["invoice_amount"].head(20)
    line_df = pd.DataFrame({"Case Rank": range(1, len(amount_series) + 1), "Invoice Amount": amount_series.values})
    fig = px.line(line_df, x="Case Rank", y="Invoice Amount", title="Invoice Amount Trend Across Ranked Cases")
    fig = apply_briefing_theme(fig)
    fig.update_yaxes(title_text="Invoice Amount")
    st.plotly_chart(fig, use_container_width=True)
    render_chart_context("A small number of invoices materially exceed the typical case pattern.", "Validate large-value invoices for split billing or duplicate payment behavior.")

with col_d:
    scatter_df = cases[["risk_score", "invoice_amount"]].copy()
    fig = px.scatter(scatter_df, x="risk_score", y="invoice_amount", title="Risk vs Invoice Amount", color="invoice_amount", color_continuous_scale="Viridis")
    fig = apply_briefing_theme(fig)
    fig.update_xaxes(title_text="Risk Score (%)")
    fig.update_yaxes(title_text="Invoice Amount")
    st.plotly_chart(fig, use_container_width=True)
    render_chart_context("Higher-risk cases are associated with larger invoice values and potential control bypass.", "Test the largest-value transactions for policy exceptions and unusual approvals.")

# --------------------------------------------------
# Top Cases
# --------------------------------------------------

st.subheader("Forensic Briefing Pack")
render_red_flag_summary(cases, title="Red-flag test density")
render_case_queue_snapshot(cases, limit=10, title="Priority case queue")

with st.expander("Compact case summary", expanded=True):
    display_cols = [
        "case_id",
        "invoice_id",
        "vendor_id",
        "risk_score",
        "risk_level",
        "reason"
    ]

    display_cases = cases[display_cols].copy()
    display_cases["risk_score"] = display_cases["risk_score"].map(lambda x: f"{x:.1f}%")

    st.dataframe(
        display_cases.head(20),
        use_container_width=True,
        hide_index=True
    )

