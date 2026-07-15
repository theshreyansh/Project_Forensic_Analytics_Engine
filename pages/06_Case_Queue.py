"""
=========================================================
Case Queue
Master Forensic Investigation Workbench
=========================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from config import OUTPUT_DIR
from utils.chart_helpers import detect_outliers, render_chart_context, style_chart_for_anomalies

st.set_page_config(page_title="Case Queue", page_icon="⚖️", layout="wide")

from utils.app_style import render_page_shell

render_page_shell()

# Active tab highlight
try:
    st.query_params["tab"] = "Case Queue"
except Exception:
    pass

st.title("⚖️ Investigation Case Queue")

st.caption("Operational view of investigation leads, owner assignment, and escalation decisions")

st.markdown("<div style='padding:12px 14px; border-left:5px solid #012169; background:#f3f7ff; border-radius:8px; margin-bottom:12px;'>"
            "<b>Business callout:</b> the highest-risk cases should be advanced for legal preservation and targeted evidence collection."
            "</div>", unsafe_allow_html=True)
st.caption("Suggested action: assign the critical cases to the legal-ready review track immediately.")

CASE_FILE = OUTPUT_DIR / "case_queue.csv"
if not CASE_FILE.exists():
    st.error("Case queue not found.")
    st.info("Run analytics/risk_engine.py first.")
    st.stop()

cases = pd.read_csv(CASE_FILE)
if "status" not in cases.columns:
    cases["status"] = "Open"
if "owner" not in cases.columns:
    cases["owner"] = "Unassigned"
if "priority" not in cases.columns:
    cases["priority"] = cases["risk_level"].map({"Critical": "P1", "High": "P2", "Medium": "P3", "Low": "P4"})

st.sidebar.header("Filters")
risk_filter = st.sidebar.multiselect("Risk Level", options=sorted(cases["risk_level"].unique()), default=sorted(cases["risk_level"].unique()))
status_filter = st.sidebar.multiselect("Status", options=sorted(cases["status"].unique()), default=sorted(cases["status"].unique()))
priority_filter = st.sidebar.multiselect("Priority", options=["P1", "P2", "P3", "P4"], default=["P1", "P2", "P3", "P4"])
filtered = cases[(cases["risk_level"].isin(risk_filter)) & (cases["status"].isin(status_filter)) & (cases["priority"].isin(priority_filter))]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Open Cases", f"{len(filtered):,}")
c2.metric("Critical", f"{len(filtered[filtered['risk_level'] == 'Critical']):,}")
c3.metric("Average Risk", f"{filtered['risk_score'].mean():.1f}%")
c4.metric("Unassigned", f"{len(filtered[filtered['owner'] == 'Unassigned']):,}")

st.divider()

left, right = st.columns(2)
with left:
    queue_summary = filtered.groupby("priority").size().reset_index(name="Cases")
    fig = px.bar(queue_summary, x="priority", y="Cases", title="Cases by Priority", color_discrete_sequence=["#012169"])
    fig.update_yaxes(title_text="Case Count")
    fig.update_layout(template="plotly_white")
    fig = style_chart_for_anomalies(fig, queue_summary["Cases"], pd.Series([value == queue_summary["Cases"].max() for value in queue_summary["Cases"]]))
    st.plotly_chart(fig, use_container_width=True)
    render_chart_context("P1 and P2 cases dominate the current queue and should be escalated first.", "Assign a legal-ready triage path to the largest priority bands and monitor aging.")
with right:
    risk_summary = filtered.groupby("risk_level").size().reset_index(name="Cases")
    fig2 = px.pie(risk_summary, names="risk_level", values="Cases", title="Risk Distribution")
    fig2.update_layout(template="plotly_white")
    fig2 = style_chart_for_anomalies(fig2, risk_summary["Cases"], pd.Series([value == risk_summary["Cases"].max() for value in risk_summary["Cases"]]))
    st.plotly_chart(fig2, use_container_width=True)
    render_chart_context("The queue is skewed toward higher-risk categories rather than routine monitoring.", "Reserve analyst capacity for the most serious queue segments.")

st.subheader("Investigation Queue")
display_cols = ["case_id", "vendor_id", "invoice_id", "risk_score", "risk_level", "priority", "status", "owner", "reason"]
queue_display = filtered[display_cols].copy()
queue_display["risk_score"] = queue_display["risk_score"].map(lambda x: f"{x:.1f}%")
st.dataframe(queue_display, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Case Details")
selected_case = st.selectbox("Select Case", filtered["case_id"].tolist())
case = filtered[filtered["case_id"] == selected_case].iloc[0]

col1, col2 = st.columns([1, 2])
with col1:
    st.metric("Risk Score", f"{case['risk_score']:.1f}%")
    st.metric("Priority", case["priority"])
    st.metric("Status", case["status"])
with col2:
    st.markdown("### Investigation Drivers")
    for reason in case["reason"].split(","):
        st.write(f"✅ {reason.strip()}")

st.divider()
st.subheader("Workflow")
owner = st.selectbox("Assign Investigator", ["Unassigned", "Alice", "Bob", "Charlie", "Master Team"])
status = st.selectbox("Update Status", ["Open", "In Progress", "Pending Legal", "Closed"])
notes = st.text_area("Investigator Notes")
if st.button("Save Workflow (Demo)"):
    st.success("Case updated successfully (demo).")

st.divider()
st.subheader("Recommended Next Steps")
if case["risk_level"] == "Critical":
    st.error("1. Notify Legal Counsel\n2. Preserve communications\n3. Expand custodian scope\n4. Review vendor onboarding\n5. Validate bank ownership\n6. Prepare evidence pack")
elif case["risk_level"] == "High":
    st.warning("1. Review approvals\n2. Verify supporting documents\n3. Interview approver\n4. Expand transaction testing")
else:
    st.info("Continue monitoring and perform targeted sampling.")

st.download_button("⬇ Export Case Queue", data=filtered.to_csv(index=False), file_name="case_queue.csv", mime="text/csv")
