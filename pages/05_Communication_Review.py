"""
=========================================================
Communication Review
Deloitte Forensic Investigation Workbench
=========================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

try:
    from wordcloud import WordCloud
except ImportError:
    WordCloud = None

from config import DATA_DIR
from utils.chart_helpers import (
    apply_briefing_theme,
    detect_outliers,
    render_case_queue_snapshot,
    render_chart_context,
    render_red_flag_summary,
    style_chart_for_anomalies,
)

st.set_page_config(
    page_title="Communication Review",
    page_icon="📧",
    layout="wide"
)

from utils.app_style import render_page_shell

render_page_shell()

# Active tab highlight
try:
    st.query_params["tab"] = "Communication Review"
except Exception:
    pass

st.title("📧 Communication Review (Mock RAG)")

st.caption("Defensible review of preserved communications with human oversight")

st.markdown("<div style='padding:12px 14px; border-left:5px solid #012169; background:#f3f7ff; border-radius:8px; margin-bottom:12px;'>"
            "<b>Business callout:</b> communications strengthen the ERP story when they reference urgency, bypasses, shared bank details, or vendor coordination."
            "</div>", unsafe_allow_html=True)
st.caption("Suggested action: preserve and review the custodians linked to the highest-risk cases.")

EMAIL_FILE = DATA_DIR / "emails.csv"
if not EMAIL_FILE.exists():
    st.error("emails.csv not found")
    st.stop()

emails = pd.read_csv(EMAIL_FILE)

st.sidebar.header("Search")
keyword = st.sidebar.text_input("Keyword", value="approval")
vendor = st.sidebar.text_input("Vendor ID (optional)")
top_k = st.sidebar.slider("Top Results", 1, 20, 5)

filtered = emails.copy()
if keyword:
    filtered = filtered[filtered["body"].str.contains(keyword, case=False, na=False)]
if vendor:
    filtered = filtered[filtered["vendor_id"] == vendor]
filtered = filtered.head(top_k)

left, right = st.columns(2)
with left:
    st.metric("Retrieved Documents", len(filtered))
with right:
    st.metric("Linked Vendors", len(filtered["vendor_id"].dropna().unique()))

st.subheader("Forensic communication briefing")
render_red_flag_summary(pd.DataFrame({"duplicate_payment": [0], "invoice_split": [0], "shared_bank": [0], "vendor_similarity": [0], "approval_override": [0], "communication": [len(filtered)]}), title="Communication-driven red flags")
render_case_queue_snapshot(pd.DataFrame({"case_id": [f"COMM{i:03}" for i in range(1, min(len(filtered), 6) + 1)], "vendor_id": filtered["vendor_id"].dropna().tolist()[:6], "invoice_id": ["" for _ in range(min(len(filtered), 6))], "risk_score": [85] * min(len(filtered), 6), "risk_level": ["High"] * min(len(filtered), 6), "reason": ["Communication"] * min(len(filtered), 6)}), limit=6, title="Communication-linked queue")

st.divider()

upper_left, upper_right = st.columns(2)
with upper_left:
    st.subheader("Review Coverage")
    theme_counts = pd.Series(filtered["subject"].astype(str).str.lower().tolist()).value_counts().head(8)
    fig = px.bar(theme_counts.reset_index(), x="index", y=theme_counts.values, title="Top Retrieved Subjects", color_discrete_sequence=["#012169"])
    fig = apply_briefing_theme(fig)
    fig = style_chart_for_anomalies(fig, theme_counts.values, pd.Series([value == theme_counts.max() for value in theme_counts.values]))
    st.plotly_chart(fig, use_container_width=True)
    render_chart_context("The retrieved evidence concentrates on a few recurring themes that can support the ERP findings.", "Use these themes to guide additional custodian review and document preservation.")

with upper_right:
    st.subheader("Risk Themes")
    theme_labels = ["approval", "urgent payment", "bank details", "invoice", "policy exception"]
    counts = []
    for label in theme_labels:
        counts.append(int(filtered["body"].str.contains(label, case=False, na=False).sum()))
    theme_df = pd.DataFrame({"Theme": theme_labels, "Count": counts})
    fig2 = px.bar(theme_df, x="Theme", y="Count", title="Theme Hits in Retrieved Evidence", color="Theme", color_discrete_sequence=["#2E86DE", "#FF7F0E", "#D62728", "#2ECC71", "#7F8C8D"])
    fig2 = apply_briefing_theme(fig2)
    fig2 = style_chart_for_anomalies(fig2, theme_df["Count"], pd.Series([value == theme_df["Count"].max() for value in theme_df["Count"]]))
    st.plotly_chart(fig2, use_container_width=True)
    render_chart_context("Urgency and approval language appear repeatedly across the evidence set.", "Prioritize review of the most frequently recurring communication themes.")

st.subheader("Concealment Language")
concealment_terms = ["urgent", "split", "off-book", "private", "confidential"]
term_counts = []
for term in concealment_terms:
    count = int(filtered["body"].str.contains(term, case=False, na=False).sum())
    term_counts.append((term, count))
term_df = pd.DataFrame(term_counts, columns=["Term", "Count"])
if not term_df.empty:
    if WordCloud is not None:
        cloud_text = " ".join([term for term, count in term_counts for _ in range(max(count, 1))])
        wordcloud = WordCloud(width=800, height=400, background_color="white", colormap="Blues").generate(cloud_text)
        buffer = BytesIO()
        wordcloud.to_image().save(buffer, format="PNG")
        st.image(buffer.getvalue(), use_container_width=True)
    else:
        fig_terms = px.bar(term_df, x="Term", y="Count", title="Concealment Term Hits", color="Term")
        fig_terms = apply_briefing_theme(fig_terms)
        st.plotly_chart(fig_terms, use_container_width=True)
    st.dataframe(term_df, use_container_width=True, hide_index=True)
    render_chart_context("Concealment-style wording appears in the retrieved communications and may indicate intent to mask activity.", "Prioritize review of these communications for evidence preservation and custodian escalation.")
else:
    st.info("No concealment language detected in the current results.")

st.subheader("Retrieved Documents")
for _, row in filtered.iterrows():
    with st.expander(f"{row['email_id']} | {row['subject']}"):
        st.write(f"**Vendor:** {row['vendor_id']}")
        st.write(f"**Date:** {row['date']}")
        st.write(row["body"])

st.divider()
st.subheader("AI Investigation Summary")
if len(filtered):
    vendors_list = filtered["vendor_id"].dropna().unique().tolist()
    summary = f"""
The retrieved communications indicate repeated discussion around **{keyword}**.

Vendors referenced: {', '.join(vendors_list)}

Potential investigation themes:
• Approval discussions
• Payment urgency
• Vendor coordination
• Possible policy exception

This summary is generated from retrieved documents only and does not conclude fraud.
"""
    st.success(summary)
else:
    st.info("No matching communications found.")

st.divider()
st.subheader("Defensible RAG Flow")
st.info("Retrieve → Cite → Summarise → Human Review → Escalate")
st.markdown("<div style='padding:12px 14px; border-left:5px solid #012169; background:#f3f7ff; border-radius:8px; margin-top:8px;'>"
            "<b>Governance note:</b> every summary is grounded in retrieved excerpts, preserved with citations, and reviewed by an investigator before any escalation decision.</div>", unsafe_allow_html=True)

pipeline_df = pd.DataFrame({
    "Step": ["Preserve", "Parse", "Retrieve", "Classify", "Summarise", "Human Review", "Escalate"],
    "Control": ["Legal hold", "Chain of custody", "Citations", "Prompt log", "Evidence bound", "Reviewer decision", "Legal sign-off"],
    "Control Strength": [95, 90, 88, 82, 84, 96, 98],
})
fig_flow = px.bar(
    pipeline_df,
    x="Control Strength",
    y="Step",
    color="Control",
    orientation="h",
    title="Model Run Pipeline and Governance Controls",
    text="Control",
)
fig_flow.update_xaxes(title_text="Defensibility Control Coverage")
fig_flow.update_yaxes(categoryorder="array", categoryarray=list(reversed(pipeline_df["Step"])))
fig_flow = apply_briefing_theme(fig_flow)
st.plotly_chart(fig_flow, use_container_width=True)
render_chart_context("The model run is controlled through preservation, retrieval citations, audit logging, and human review.", "Use the control gates as QA checkpoints before any legal or regulatory escalation.")

st.subheader("Evidence")
display_cols = ["email_id", "vendor_id", "subject", "date"]
st.dataframe(filtered[display_cols], use_container_width=True, hide_index=True)

st.subheader("Source Citations")
for _, row in filtered.iterrows():
    st.markdown(f"- {row['email_id']} ({row['date']})")

st.divider()
st.subheader("Human Review")
review = st.selectbox("Investigator Decision", ["Pending", "Relevant", "Not Relevant", "Escalate to Legal"])
notes = st.text_area("Investigator Notes")
if st.button("Save Review"):
    st.success("Review recorded (demo).")

st.divider()
st.subheader("AI Governance")
st.info("• Retrieval precedes summarisation (RAG pattern)\n• Summary is limited to retrieved evidence\n• Source citations are displayed\n• Human review is mandatory\n• No automated fraud determination\n• Decisions remain with investigators\n• All prompts and outputs should be auditable in production")
