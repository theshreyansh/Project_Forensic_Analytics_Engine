"""
=========================================================
Din
LLM-style Investigation Assistant
=========================================================
"""

import re

import pandas as pd
import streamlit as st

from config import DATA_DIR, OUTPUT_DIR
from utils.app_style import render_page_shell


st.set_page_config(
    page_title="Din",
    page_icon="D",
    layout="wide",
)

render_page_shell()

# Active tab highlight
try:
    st.query_params["tab"] = "Din"
except Exception:
    pass


st.title("Din")
st.caption("Ask brief investigation questions grounded in the available ERP, vendor, case, and communications data.")


BACKGROUND = """
You are supporting a forensic technology investigation following a whistleblower report.
The allegation concerns procurement misconduct, duplicate or irregular payments,
invoice splitting under approval thresholds, vendor bank-account reuse, possible employee-vendor
relationships, and coordination or concealment in email or Teams communications.
The expected posture is defensible: explain assumptions, cite data tables used, avoid concluding fraud,
and recommend practical next steps for CFO, Legal, Compliance, and investigators.
"""


@st.cache_data
def load_data():
    data = {}
    data["cases"] = pd.read_csv(OUTPUT_DIR / "case_queue.csv")
    data["vendors"] = pd.read_csv(DATA_DIR / "vendor_master.csv")
    data["invoices"] = pd.read_csv(DATA_DIR / "invoice_header.csv")
    data["payments"] = pd.read_csv(DATA_DIR / "payments.csv")
    data["employees"] = pd.read_csv(DATA_DIR / "employee_master.csv")
    data["emails"] = pd.read_csv(DATA_DIR / "emails.csv")
    return data


def money(value):
    return f"${float(value):,.0f}"


def summarize_cases(cases):
    risk_counts = cases["risk_level"].value_counts().to_dict()
    top_reasons = (
        cases["reason"]
        .astype(str)
        .str.get_dummies(sep=", ")
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .to_dict()
    )
    return risk_counts, top_reasons


def answer_question(question, data):
    q = question.lower().strip()
    cases = data["cases"]
    vendors = data["vendors"]
    invoices = data["invoices"]
    emails = data["emails"]

    risk_counts, top_reasons = summarize_cases(cases)
    total_spend = invoices["invoice_amount"].sum()
    critical = int((cases["risk_level"] == "Critical").sum())
    high = int((cases["risk_level"] == "High").sum())

    if any(term in q for term in ["overview", "summary", "triage", "10 day", "10-day"]):
        return (
            f"Rapid triage view: {len(cases):,} case items are in the queue, including "
            f"{critical:,} Critical and {high:,} High matters. Total invoice spend in scope is {money(total_spend)}. "
            f"The strongest red-flag themes are {', '.join([f'{k} ({v})' for k, v in top_reasons.items()])}. "
            "Recommended next step: prioritize Critical/High cases, preserve communications for linked custodians, "
            "and validate bank ownership, approvals, and supporting invoices before making findings."
        )

    if any(term in q for term in ["duplicate", "irregular payment", "double payment"]):
        flagged = cases[cases["duplicate_payment"] == 1]
        top_vendor = flagged["vendor_id"].value_counts().idxmax() if not flagged.empty else "N/A"
        return (
            f"Duplicate-payment signal: {len(flagged):,} queued cases carry the duplicate payment flag. "
            f"The most frequent vendor in this subset is {top_vendor}. Treat this as a lead, not proof: "
            "compare invoice number, date, amount, payment reference, and reversal/credit activity."
        )

    if any(term in q for term in ["split", "threshold", "circumvention", "approval"]):
        flagged = cases[(cases["invoice_split"] == 1) | (cases["approval_override"] == 1)]
        avg_amount = flagged["invoice_amount"].mean() if not flagged.empty else 0
        return (
            f"Approval circumvention view: {len(flagged):,} cases show invoice-splitting or approval-override indicators. "
            f"Average invoice amount in that subset is {money(avg_amount)}. Focus on near-threshold invoices, repeated "
            "same-vendor/same-period billing, and approver changes outside normal workflow."
        )

    if any(term in q for term in ["bank", "mobile", "address", "relationship", "ubo", "employee"]):
        shared_bank = int(cases["shared_bank"].sum()) if "shared_bank" in cases.columns else 0
        return (
            f"Relationship-risk view: {shared_bank:,} case rows are flagged for shared-bank indicators. "
            "The app also adds demo address/mobile and employee-vendor identifier overlap tests for investigation targeting. "
            "Next step: corroborate against registry/KYC records, employee directory, vendor onboarding forms, and bank letters."
        )

    if any(term in q for term in ["email", "teams", "communication", "conceal", "rag", "nlp", "genai", "ai"]):
        keyword_hits = {}
        for term in ["urgent", "approval", "bank details", "invoice", "vendor"]:
            keyword_hits[term] = int(emails["body"].str.contains(term, case=False, na=False).sum())
        return (
            "Communications review should be RAG-based and human-reviewed. Current keyword hit counts are "
            + ", ".join([f"{k}: {v}" for k, v in keyword_hits.items()])
            + ". Use retrieved excerpts with email IDs/dates as citations, then require investigator validation before escalation."
        )

    vendor_match = re.search(r"v\d{5}", q)
    if vendor_match:
        vendor_id = vendor_match.group(0).upper()
        vendor_cases = cases[cases["vendor_id"] == vendor_id]
        vendor_row = vendors[vendors["vendor_id"] == vendor_id]
        if vendor_row.empty:
            return f"I could not find vendor {vendor_id} in the current vendor master."
        name = vendor_row.iloc[0]["vendor_name"]
        spend = invoices[invoices["vendor_id"] == vendor_id]["invoice_amount"].sum()
        return (
            f"{vendor_id} ({name}) has {len(vendor_cases):,} linked case rows and total invoice spend of {money(spend)}. "
            f"Key case reasons: {', '.join(vendor_cases['reason'].astype(str).head(3).tolist()) or 'none in queue'}. "
            "Recommended review: validate vendor master, KYC, approvals, payments, and communications."
        )

    return (
        f"Based on the current data, there are {len(cases):,} case rows across {cases['vendor_id'].nunique():,} vendors. "
        f"Risk distribution is {risk_counts}. Ask about duplicate payments, approval circumvention, vendor relationships, "
        "communications/RAG, a specific vendor ID, or the 10-day triage plan for a more targeted answer."
    )


data = load_data()

st.markdown(
    "<div class='apple-callout'><b>Prompt policy:</b> Din answers from local investigation data and the case background. "
    "It keeps answers brief, flags assumptions, and avoids making a final fraud conclusion.</div>",
    unsafe_allow_html=True,
)

question = st.text_area(
    "Question",
    placeholder="Example: What are the early signals for approval circumvention?",
    height=110,
)

if st.button("Run", use_container_width=True):
    if not question.strip():
        st.warning("Enter a question first.")
    else:
        with st.spinner("Din is reviewing the investigation context..."):
            st.subheader("Answer")
            st.write(answer_question(question, data))
            with st.expander("Context used"):
                st.write(BACKGROUND)
                st.write("Data tables: case_queue.csv, vendor_master.csv, invoice_header.csv, payments.csv, employee_master.csv, emails.csv.")
