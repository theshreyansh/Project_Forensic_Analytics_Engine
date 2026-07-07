"""
=========================================================
Communication Review
Deloitte Forensic Investigation Workbench
=========================================================
"""

import streamlit as st
import pandas as pd
from pathlib import Path

from config import DATA_DIR

st.set_page_config(
    page_title="Communication Review",
    page_icon="📧",
    layout="wide"
)

st.title("📧 Communication Review (Mock RAG)")

EMAIL_FILE = DATA_DIR / "emails.csv"

if not EMAIL_FILE.exists():
    st.error("emails.csv not found")
    st.stop()

emails = pd.read_csv(EMAIL_FILE)

# --------------------------------------------------
# Sidebar
# --------------------------------------------------

st.sidebar.header("Search")

keyword = st.sidebar.text_input(
    "Keyword",
    value="approval"
)

vendor = st.sidebar.text_input(
    "Vendor ID (optional)"
)

top_k = st.sidebar.slider(
    "Top Results",
    1,
    20,
    5
)

# --------------------------------------------------
# Retrieval
# --------------------------------------------------

filtered = emails.copy()

if keyword:

    filtered = filtered[
        filtered["body"].str.contains(
            keyword,
            case=False,
            na=False
        )
    ]

if vendor:

    filtered = filtered[
        filtered["vendor_id"] == vendor
    ]

filtered = filtered.head(top_k)

st.metric(
    "Retrieved Documents",
    len(filtered)
)

st.divider()

# --------------------------------------------------
# Retrieved Evidence
# --------------------------------------------------

st.subheader("Retrieved Documents")

for _, row in filtered.iterrows():

    with st.expander(
        f"{row['email_id']} | {row['subject']}"
    ):

        st.write(f"**Vendor:** {row['vendor_id']}")
        st.write(f"**Date:** {row['date']}")
        st.write(row["body"])

# --------------------------------------------------
# Mock AI Summary
# --------------------------------------------------

st.divider()

st.subheader("AI Investigation Summary")

if len(filtered):

    vendors = (
        filtered["vendor_id"]
        .dropna()
        .unique()
        .tolist()
    )

    summary = f"""
The retrieved communications indicate repeated discussion
around **{keyword}**.

Vendors referenced:

{", ".join(vendors)}

Potential investigation themes:

• Approval discussions

• Payment urgency

• Vendor coordination

• Possible policy exception

This summary is generated from retrieved
documents only and **does not conclude fraud**.
"""

    st.success(summary)

else:

    st.info("No matching communications found.")

# --------------------------------------------------
# Evidence Table
# --------------------------------------------------

st.divider()

st.subheader("Evidence")

display_cols = [
    "email_id",
    "vendor_id",
    "subject",
    "date"
]

st.dataframe(
    filtered[display_cols],
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# Citations
# --------------------------------------------------

st.subheader("Source Citations")

for _, row in filtered.iterrows():

    st.markdown(
        f"- {row['email_id']} ({row['date']})"
    )

# --------------------------------------------------
# Human Review
# --------------------------------------------------

st.divider()

st.subheader("Human Review")

review = st.selectbox(
    "Investigator Decision",
    [
        "Pending",
        "Relevant",
        "Not Relevant",
        "Escalate to Legal"
    ]
)

notes = st.text_area(
    "Investigator Notes"
)

if st.button("Save Review"):

    st.success(
        "Review recorded (demo)."
    )

# --------------------------------------------------
# Governance
# --------------------------------------------------

st.divider()

st.subheader("AI Governance")

st.info("""
• Retrieval precedes summarisation (RAG pattern)

• Summary is limited to retrieved evidence

• Source citations are displayed

• Human review is mandatory

• No automated fraud determination

• Decisions remain with investigators

• All prompts and outputs should be auditable in production
""")