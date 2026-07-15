"""
=========================================================
Investigation Plan
Master Forensic Investigation Workbench
=========================================================
"""

import streamlit as st

st.set_page_config(
    page_title="Investigation Plan",
    page_icon="🧭",
    layout="wide"
)

st.title("🧭 10-Day Triage and 6-Week Investigation Plan")
st.caption("Defensible procurement misconduct investigation design for CFO, Legal, Compliance, and investigators")

st.markdown("---")

st.markdown("## Slide 1 — Delivery approach & workstreams")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Phase 1", "10 business days")
    st.write("Rapid triage, early signals, prioritized queue, and executive/legal update")

with col2:
    st.metric("Phase 2", "6 weeks")
    st.write("Deep investigation, evidence packs, targeted interviews, and regulatory-ready reporting")

with col3:
    st.metric("Primary objective", "Defensible escalation")
    st.write("Move from ambiguous allegations to a structured, auditable case file")

st.subheader("Workstreams")

workstreams = [
    ("Data intake & preservation", "Confirm legal hold, source inventory, region coverage, and completeness gaps."),
    ("ERP analytics", "Run SQL/Python anomaly tests for duplicate payments, invoice splitting, shared bank accounts, and approval circumvention."),
    ("Unstructured review", "Use Relativity-style review, threading, and keyword/metadata searches across email and Teams exports."),
    ("GenAI/NLP review", "Use RAG-based summarisation and classification with citations and human-in-the-loop safeguards."),
    ("Case management", "Prioritize cases, assign owners, and track evidence, QA gates, and next actions."),
    ("Stakeholder reporting", "Publish CFO, Legal, and Compliance-ready views with clear risk and recommendation language."),
]

for name, description in workstreams:
    st.markdown(f"- **{name}**: {description}")

st.subheader("Governance, risks, and assumptions")

risk_items = [
    ("Data completeness", "Regional systems may be incomplete; treat results as directional until corroborated."),
    ("Custodian coverage", "Email and Teams coverage vary; expand scope only when seeded by structured signals or preserved communications."),
    ("Policy ambiguity", "Thresholds may be in PDFs/emails; verify current policy with procurement and legal."),
    ("False positives", "Alias detection and communication hits require human review before escalation."),
    ("Privilege and privacy", "Use legal review controls and preserve chain-of-custody for all extracted content."),
]

for item, detail in risk_items:
    st.write(f"- **{item}**: {detail}")

st.markdown("---")

st.markdown("## Slide 2 — Workflow design")

st.markdown("### 1. Structured red flags create seeds for communication review")

st.markdown("""
1. Run SQL joins across invoices, payments, approvals, vendor master, and policy thresholds.
2. Generate red-flag tests for duplicate payments, threshold-band invoices, shared bank accounts, vendor alias clusters, approval overrides, quarter-end spikes, and possible employee-vendor relationships.
3. Convert each hit into a case seed with supporting evidence and a risk score.
4. Feed those case seeds into the communications review queue for targeted email/Teams review.
""")

st.markdown("### 2. Unstructured findings feed back into structured targeting")

st.markdown("""
- Findings from communications can create new structured hypotheses: a vendor alias mentioned in an email can trigger a vendor-master match test.
- New custodians or regions can be added when a message references a bank account, approval workaround, or personal relationship.
- Each communication finding is tied back to a transaction or vendor record for cross-correlation and defensibility.
""")

st.markdown("### 3. Defensible GenAI/NLP design")

st.markdown("""
- Use a retrieval-augmented workflow over preserved emails, Teams extracts, and policy documents.
- Retrieve short, cited excerpts rather than generating long narrative summaries from whole datasets.
- Require human review for every classification or summarisation that affects escalation or legal action.
- Maintain an audit trail of prompts, retrieved chunks, reviewer decisions, and versioned outputs.
- Do not use GenAI to replace the evidentiary record; use it to accelerate review and triage only.
""")

st.subheader("Example SQL/Python workflow")

st.code("""
-- Example SQL: identify invoices in the approval threshold band and linked to shared-bank vendors
SELECT i.invoice_id, i.vendor_id, i.invoice_amount, v.bank_account
FROM invoice_header i
JOIN vendor_master v ON i.vendor_id = v.vendor_id
WHERE i.invoice_amount BETWEEN 47000 AND 50000
  AND v.bank_account IN (
      SELECT bank_account FROM vendor_master GROUP BY bank_account HAVING COUNT(*) > 1
  );
""", language="sql")

st.code("""
# Example Python logic
import pandas as pd
from rapidfuzz import fuzz

# 1. Load ERP tables
payments = pd.read_csv('data/payments.csv')
invoices = pd.read_csv('data/invoice_header.csv')
vendors = pd.read_csv('data/vendor_master.csv')

# 2. Create flag tests
# duplicate payments, split invoices, shared bank accounts, alias clusters, communication hits
# 3. Score and rank
# 4. Emit case_queue.csv for dashboard review
""", language="python")

st.markdown("---")

st.markdown("## Slide 3 — Example outputs")

st.subheader("Dashboard wireframe")

st.markdown("""
- KPI cards: total cases, critical/high, average risk, legal hold coverage.
- Risk distribution chart: Critical / High / Medium / Low.
- Case queue table: case ID, vendor, invoice, score, reasons, owner, status.
- Drill-down panel: why flagged, supporting transactions, related communications, recommended next step.
""")

st.subheader("Evidence pack outline")

pack_sections = [
    "Scope and preserved data sources",
    "Chronology of key events",
    "Structured red-flag analysis",
    "Communication excerpts with citations",
    "Entity and relationship analysis",
    "Chain of custody and QA summary",
    "Recommendations and next actions",
]

for section in pack_sections:
    st.write(f"- {section}")

st.subheader("Stakeholder views")

st.write("- CFO: concise risk summary, financial impact, and remediation options")
st.write("- Legal Counsel: privilege posture, preservation status, chain of custody, and escalation triggers")
st.write("- Compliance: policy breach indicators, control failures, and monitoring recommendations")
st.write("- Investigators: queue, evidence links, and directed next steps")

st.markdown("---")

st.markdown("## One-page RAID log + resourcing")

raid = {
    "Risk": [
        "Incomplete ERP coverage by region",
        "Sparse or uneven communications coverage",
        "Potential privilege issues in unstructured review",
        "Risk of over-reliance on AI-generated summaries"
    ],
    "Action": [
        "Use multiple source triangulation and document limitations",
        "Prioritize custodians indicated by structured red flags",
        "Apply legal review gates before production",
        "Use GenAI only for assistance, not final findings"
    ],
    "Owner": ["Analytics lead", "eDiscovery lead", "Legal counsel", "Investigation manager"],
    "Date": ["Day 3", "Day 5", "Day 7", "Weekly"],
}

st.dataframe(raid, use_container_width=True, hide_index=True)

st.subheader("Resourcing approach")

st.markdown("""
- Analytics lead: SQL/Python anomaly engine and case ranking.
- eDiscovery lead: review workflow, custodians, threading, and tagging.
- Legal counsel: preservation, privilege, and escalation decisions.
- Investigator team: transaction testing, document review, and interview preparation.
- QA reviewer: validate rules, evidence pack completeness, and stakeholder reporting.
""")

st.info("This plan is designed to be defensible, auditable, and stakeholder-ready while keeping the process moving quickly.")
