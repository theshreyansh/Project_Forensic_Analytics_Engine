"""
=========================================================
Evidence Pack Generator
Deloitte Forensic Investigation Workbench
=========================================================
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from config import OUTPUT_DIR

st.set_page_config(
    page_title="Evidence Pack",
    page_icon="📁",
    layout="wide"
)

st.title("📁 Evidence Pack Generator")

CASE_FILE = OUTPUT_DIR / "case_queue.csv"

if not CASE_FILE.exists():
    st.error("Run the risk engine first.")
    st.stop()

cases = pd.read_csv(CASE_FILE)

case_id = st.selectbox(
    "Select Investigation Case",
    cases["case_id"]
)

case = cases[cases["case_id"] == case_id].iloc[0]

st.subheader("Case Summary")

col1, col2, col3 = st.columns(3)

col1.metric("Risk Score", case["risk_score"])
col2.metric("Risk Level", case["risk_level"])
col3.metric("Priority", "P1" if case["risk_level"]=="Critical" else "P2")

st.write("### Investigation Drivers")
for reason in case["reason"].split(","):
    st.write(f"• {reason.strip()}")

st.write("### Executive Summary")
st.info(
    "This case has been prioritised based on the composite risk "
    "score generated from ERP analytics. Findings require human "
    "validation and should not be interpreted as proof of fraud."
)

def generate_pdf(selected_case):
    report_path = OUTPUT_DIR / f"{selected_case['case_id']}_Evidence_Pack.pdf"

    doc = SimpleDocTemplate(str(report_path))
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(
        "<b>Deloitte Forensic Investigation Evidence Pack</b>",
        styles["Title"]
    ))

    story.append(Spacer(1,12))

    story.append(Paragraph(
        f"<b>Case ID:</b> {selected_case['case_id']}",
        styles["Normal"]
    ))

    story.append(Paragraph(
        f"<b>Invoice:</b> {selected_case['invoice_id']}",
        styles["Normal"]
    ))

    story.append(Paragraph(
        f"<b>Vendor:</b> {selected_case['vendor_id']}",
        styles["Normal"]
    ))

    story.append(Paragraph(
        f"<b>Risk Score:</b> {selected_case['risk_score']}",
        styles["Normal"]
    ))

    story.append(Paragraph(
        f"<b>Risk Level:</b> {selected_case['risk_level']}",
        styles["Normal"]
    ))

    story.append(Spacer(1,18))

    story.append(
        Paragraph(
            "<b>Investigation Drivers</b>",
            styles["Heading2"]
        )
    )

    table = Table(
        [["Indicator"]] +
        [[r.strip()] for r in selected_case["reason"].split(",")]
    )

    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),
        ("GRID",(0,0),(-1,-1),0.5,colors.grey),
        ("BOTTOMPADDING",(0,0),(-1,0),8),
    ]))

    story.append(table)
    story.append(Spacer(1,18))

    story.append(
        Paragraph(
            "<b>Investigator Assessment</b>",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            "The identified indicators represent investigative "
            "leads generated through automated analytics. "
            "They require corroboration through supporting "
            "documentation, communication review, and interviews.",
            styles["BodyText"]
        )
    )

    story.append(Spacer(1,18))

    story.append(
        Paragraph(
            "<b>AI Governance</b>",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            "Any AI-assisted summaries used during this "
            "investigation were grounded in retrieved "
            "documents, include citations, and were "
            "validated by human investigators.",
            styles["BodyText"]
        )
    )

    story.append(Spacer(1,18))

    story.append(
        Paragraph(
            "<b>Confidential</b><br/>"
            "Prepared for internal investigative purposes only.",
            styles["Italic"]
        )
    )

    doc.build(story)

    return report_path

if st.button("Generate Evidence Pack"):

    pdf_path = generate_pdf(case)

    st.success("Evidence Pack generated successfully.")

    with open(pdf_path, "rb") as f:
        st.download_button(
            "⬇ Download PDF",
            data=f,
            file_name=pdf_path.name,
            mime="application/pdf"
        )

st.divider()

st.subheader("Evidence Pack Contents")

st.markdown("""
- Executive Summary
- Case Metadata
- Vendor Information
- Invoice Details
- Composite Risk Score
- Investigation Drivers
- AI Governance Statement
- Investigator Assessment
- Confidentiality Notice
""")