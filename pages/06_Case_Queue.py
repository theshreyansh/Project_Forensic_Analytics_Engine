"""
=========================================================
Case Queue
Deloitte Forensic Investigation Workbench
=========================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

from config import OUTPUT_DIR

st.set_page_config(
    page_title="Case Queue",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Investigation Case Queue")

# -------------------------------------------------------
# Load Cases
# -------------------------------------------------------

CASE_FILE = OUTPUT_DIR / "case_queue.csv"

if not CASE_FILE.exists():
    st.error("Case queue not found.")
    st.info("Run analytics/risk_engine.py first.")
    st.stop()

cases = pd.read_csv(CASE_FILE)

# -------------------------------------------------------
# Initialize Workflow Columns (Demo)
# -------------------------------------------------------

if "status" not in cases.columns:
    cases["status"] = "Open"

if "owner" not in cases.columns:
    cases["owner"] = "Unassigned"

if "priority" not in cases.columns:
    cases["priority"] = cases["risk_level"].map({
        "Critical": "P1",
        "High": "P2",
        "Medium": "P3",
        "Low": "P4"
    })

# -------------------------------------------------------
# Sidebar Filters
# -------------------------------------------------------

st.sidebar.header("Filters")

risk_filter = st.sidebar.multiselect(
    "Risk Level",
    options=sorted(cases["risk_level"].unique()),
    default=sorted(cases["risk_level"].unique())
)

status_filter = st.sidebar.multiselect(
    "Status",
    options=sorted(cases["status"].unique()),
    default=sorted(cases["status"].unique())
)

priority_filter = st.sidebar.multiselect(
    "Priority",
    options=["P1","P2","P3","P4"],
    default=["P1","P2","P3","P4"]
)

filtered = cases[
    (cases["risk_level"].isin(risk_filter)) &
    (cases["status"].isin(status_filter)) &
    (cases["priority"].isin(priority_filter))
]

# -------------------------------------------------------
# KPIs
# -------------------------------------------------------

c1,c2,c3,c4 = st.columns(4)

c1.metric("Open Cases", len(filtered))
c2.metric("Critical", len(filtered[filtered["risk_level"]=="Critical"]))
c3.metric("Average Risk", round(filtered["risk_score"].mean(),1))
c4.metric("Unassigned", len(filtered[filtered["owner"]=="Unassigned"]))

st.divider()

# -------------------------------------------------------
# Case Distribution
# -------------------------------------------------------

left,right = st.columns(2)

with left:

    fig = px.bar(
        filtered.groupby("priority")
        .size()
        .reset_index(name="Cases"),
        x="priority",
        y="Cases",
        title="Cases by Priority"
    )

    st.plotly_chart(fig, use_container_width=True)

with right:

    fig = px.pie(
        filtered,
        names="risk_level",
        title="Risk Distribution"
    )

    st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------------
# Investigator Queue
# -------------------------------------------------------

st.subheader("Investigation Queue")

display_cols = [
    "case_id",
    "vendor_id",
    "invoice_id",
    "risk_score",
    "risk_level",
    "priority",
    "status",
    "owner",
    "reason"
]

st.dataframe(
    filtered[display_cols],
    use_container_width=True,
    hide_index=True
)

# -------------------------------------------------------
# Drill Down
# -------------------------------------------------------

st.divider()

st.subheader("Case Details")

selected_case = st.selectbox(
    "Select Case",
    filtered["case_id"].tolist()
)

case = filtered[
    filtered["case_id"] == selected_case
].iloc[0]

col1,col2 = st.columns([1,2])

with col1:

    st.metric("Risk Score", case["risk_score"])
    st.metric("Priority", case["priority"])
    st.metric("Status", case["status"])

with col2:

    st.markdown("### Investigation Drivers")

    reasons = case["reason"].split(",")

    for reason in reasons:
        st.write(f"✅ {reason.strip()}")

st.divider()

# -------------------------------------------------------
# Workflow Management
# -------------------------------------------------------

st.subheader("Workflow")

owner = st.selectbox(
    "Assign Investigator",
    [
        "Unassigned",
        "Alice",
        "Bob",
        "Charlie",
        "Deloitte Team"
    ]
)

status = st.selectbox(
    "Update Status",
    [
        "Open",
        "In Progress",
        "Pending Legal",
        "Closed"
    ]
)

notes = st.text_area(
    "Investigator Notes"
)

if st.button("Save Workflow (Demo)"):

    st.success(
        "Case updated successfully (demo)."
    )

# -------------------------------------------------------
# Recommended Actions
# -------------------------------------------------------

st.divider()

st.subheader("Recommended Next Steps")

if case["risk_level"] == "Critical":

    st.error("""
1. Notify Legal Counsel

2. Preserve communications

3. Expand custodian scope

4. Review vendor onboarding

5. Validate bank ownership

6. Prepare evidence pack
""")

elif case["risk_level"] == "High":

    st.warning("""
1. Review approvals

2. Verify supporting documents

3. Interview approver

4. Expand transaction testing
""")

else:

    st.info("""
Continue monitoring and perform targeted sampling.
""")

# -------------------------------------------------------
# Export
# -------------------------------------------------------

st.download_button(
    "⬇ Export Case Queue",
    data=filtered.to_csv(index=False),
    file_name="case_queue.csv",
    mime="text/csv"
)