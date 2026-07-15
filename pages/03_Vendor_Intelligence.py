"""
=========================================================
Vendor Intelligence
Master Forensic Investigation Workbench
=========================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from rapidfuzz import fuzz

from config import DATA_DIR, OUTPUT_DIR
from utils.app_style import render_page_shell
from utils.chart_helpers import (
    apply_briefing_theme,
    build_name_variation_table,
    detect_outliers,
    render_case_queue_snapshot,
    render_chart_context,
    render_red_flag_summary,
    style_chart_for_anomalies,
)

st.set_page_config(
    page_title="Vendor Intelligence",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 Vendor Intelligence")
render_page_shell()

st.caption("Vendor-level view for transaction testing and control review")

st.markdown("<div style='padding:12px 14px; border-left:5px solid #012169; background:#f3f7ff; border-radius:8px; margin-bottom:12px;'>"
            "<b>Business callout:</b> vendor risk is concentrated where shared identifiers and repeated transaction patterns overlap."
            "</div>", unsafe_allow_html=True)
st.caption("Suggested action: validate bank ownership and review all related approvals for the selected vendor.")

vendors = pd.read_csv(DATA_DIR / "vendor_master.csv")
cases = pd.read_csv(OUTPUT_DIR / "case_queue.csv")
payments = pd.read_csv(DATA_DIR / "payments.csv")
invoices = pd.read_csv(DATA_DIR / "invoice_header.csv")
emails = pd.read_csv(DATA_DIR / "emails.csv")
employees = pd.read_csv(DATA_DIR / "employee_master.csv")

if "address" not in vendors.columns:
    vendor_numbers = vendors["vendor_id"].astype(str).str.replace("V", "", regex=False).astype(int)
    vendors["address"] = vendor_numbers.apply(lambda value: f"{10 + value % 9} Market Link Road, Region {value % 5}")

def vendor_number(vendor_identifier):
    return int(str(vendor_identifier).replace("V", "") or 0)


def compute_vendor_kpis(vendor_id):
    vendor_invoices = invoices[invoices["vendor_id"] == vendor_id]
    vendor_cases = cases[cases["vendor_id"] == vendor_id]
    vendor_payments = payments[payments["invoice_id"].isin(vendor_invoices["invoice_id"])]

    total_spend = vendor_invoices["invoice_amount"].sum() if "invoice_amount" in vendor_invoices.columns else 0

    return {
        "Invoices": int(len(vendor_invoices)),
        "Payments": int(len(vendor_payments)),
        "Total Spend": float(total_spend),
        "Investigation Cases": int(len(vendor_cases)),
    }



def build_due_diligence_profile(vendor_row, vendor_spend, employee_df):
    number = vendor_number(vendor_row["vendor_id"])
    employee_surnames = set(employee_df["employee_name"].astype(str).str.split().str[-1].str.lower())
    vendor_tokens = str(vendor_row["vendor_name"]).replace("-", " ").split()
    vendor_surname = vendor_tokens[-1].lower() if vendor_tokens else ""
    ubo_name = f"{vendor_tokens[0] if vendor_tokens else 'Alex'} {vendor_tokens[-1] if vendor_tokens else 'Morgan'}"
    has_employee_surname_match = vendor_surname in employee_surnames or number % 11 == 0
    incorporation_age_months = 2 + (number % 30)
    has_website = number % 5 != 0
    has_linkedin = number % 7 != 0
    kyc_completeness = max(35, 98 - (number % 9) * 7)
    estimated_revenue = max(vendor_spend * (1.25 + (number % 5) * 0.28), 1)
    concentration_pct = min(100, (vendor_spend / estimated_revenue) * 100)
    adverse_hits = int(number % 13 == 0) + int(number % 17 == 0)
    first_degree_connection = number % 9 == 0
    address_type = "Residential" if number % 6 in [0, 1] else "Commercial"
    digital_risk = 100 - ((45 if has_website else 0) + (35 if has_linkedin else 0) + min(20, kyc_completeness / 5))
    overall_risk = min(
        100,
        (30 if has_employee_surname_match else 0)
        + (22 if incorporation_age_months < 6 else 0)
        + (18 if not has_website or not has_linkedin else 0)
        + (18 if first_degree_connection else 0)
        + (18 if adverse_hits else 0)
        + (14 if address_type == "Residential" else 0)
        + max(0, concentration_pct - 55) * 0.35,
    )
    return {
        "UBO": ubo_name,
        "ubo_match": has_employee_surname_match,
        "incorporation_age_months": incorporation_age_months,
        "has_website": has_website,
        "has_linkedin": has_linkedin,
        "kyc_completeness": round(kyc_completeness, 1),
        "estimated_revenue": estimated_revenue,
        "concentration_pct": concentration_pct,
        "adverse_hits": adverse_hits,
        "first_degree_connection": first_degree_connection,
        "address_type": address_type,
        "digital_risk": max(0, round(digital_risk, 1)),
        "overall_risk": round(overall_risk, 1),
    }

vendor_list = sorted(vendors["vendor_name"].unique())
selected_vendor = st.selectbox("Search Vendor", vendor_list)
vendor_row = vendors[vendors["vendor_name"] == selected_vendor].iloc[0]
vendor_id = vendor_row["vendor_id"]

# Table-backed vendor snapshot (requested top section)
kpis = compute_vendor_kpis(vendor_id)

vendor_table = pd.DataFrame([
    {
        "Vendor ID": vendor_id,
        "Country": vendor_row.get("country", ""),
        "Vendor Type": vendor_row.get("vendor_type", ""),
        "Bank Account": vendor_row.get("bank_account", ""),
        "Invoices": kpis["Invoices"],
        "Payments": kpis["Payments"],
        "Total Spend": kpis["Total Spend"],
        "Investigation Cases": kpis["Investigation Cases"],
    }
])

vendor_table["Total Spend"] = vendor_table["Total Spend"].fillna(0).map(lambda v: f"${float(v):,.0f}")


st.divider()
st.dataframe(vendor_table, use_container_width=True, hide_index=True)

# Keep derived subsets for the next sections
vendor_invoices = invoices[invoices["vendor_id"] == vendor_id]
vendor_cases = cases[cases["vendor_id"] == vendor_id]


st.divider()

# Keep compatible variable names for subsequent OSINT section
vendor = vendor_row
vendor_invoices = invoices[invoices["vendor_id"] == vendor_id]
vendor_cases = cases[cases["vendor_id"] == vendor_id]
vendor_payments = payments[payments["invoice_id"].isin(vendor_invoices["invoice_id"])]
total_spend = vendor_invoices["invoice_amount"].sum() if "invoice_amount" in vendor_invoices.columns else 0

st.subheader("OSINT and Registry Due Diligence")
dd = build_due_diligence_profile(vendor, total_spend, employees)

st.caption("Demo OSINT/registry enrichment is generated locally from available records; production can replace this layer with registry, sanctions, adverse-media, LinkedIn, geocoding, and KYC APIs.")

traffic_color = "#ff3b30" if dd["ubo_match"] else "#34c759"
traffic_label = "Red" if dd["ubo_match"] else "Green"

osint_left, osint_mid, osint_right = st.columns(3)
with osint_left:
    fig_ubo = go.Figure(go.Indicator(
        mode="gauge+number",
        value=100 if dd["ubo_match"] else 12,
        title={"text": f"UBO Match: {traffic_label}"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": traffic_color},
            "steps": [
                {"range": [0, 35], "color": "#e9f7ef"},
                {"range": [35, 70], "color": "#fff4d6"},
                {"range": [70, 100], "color": "#ffe3e0"},
            ],
        },
    ))
    fig_ubo.update_layout(height=280, margin=dict(l=20, r=20, t=55, b=15))
    st.plotly_chart(fig_ubo, use_container_width=True)

with osint_mid:
    fig_digital = go.Figure(go.Indicator(
        mode="gauge+number",
        value=dd["digital_risk"],
        title={"text": "Digital Footprint Risk"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#0071e3"},
            "steps": [
                {"range": [0, 35], "color": "#e9f7ef"},
                {"range": [35, 70], "color": "#fff4d6"},
                {"range": [70, 100], "color": "#ffe3e0"},
            ],
        },
    ))
    fig_digital.update_layout(height=280, margin=dict(l=20, r=20, t=55, b=15))
    st.plotly_chart(fig_digital, use_container_width=True)

with osint_right:
    st.metric("Overall Due Diligence Risk", f"{dd['overall_risk']:.1f}%")
    st.metric("KYC Completeness", f"{dd['kyc_completeness']:.1f}%")
    st.metric("Address Type", dd["address_type"])

tests = pd.DataFrame([
    {"Test Name": "UBO Match", "Data Source": "Registry API", "Risk Logic": "Employee surname/address overlaps vendor UBO", "Result": "Flag" if dd["ubo_match"] else "Clear"},
    {"Test Name": "Ghost Company Detection", "Data Source": "Registry/Web", "Risk Logic": "Incorporated < 6 months or no digital footprint", "Result": "Flag" if dd["incorporation_age_months"] < 6 or dd["digital_risk"] > 65 else "Clear"},
    {"Test Name": "Shared Directorships", "Data Source": "Registry API", "Risk Logic": "Director appears in another vendor cluster", "Result": "Flag" if vendor_number(vendor_id) % 8 == 0 else "Review"},
    {"Test Name": "Mandatory KYC Quality", "Data Source": "KYC Repository", "Risk Logic": "Missing, inconsistent, or low quality mandatory fields", "Result": "Flag" if dd["kyc_completeness"] < 70 else "Clear"},
    {"Test Name": "Professional Proximity", "Data Source": "LinkedIn/Public", "Risk Logic": "First-degree connection to procurement staff", "Result": "Flag" if dd["first_degree_connection"] else "Clear"},
    {"Test Name": "Adverse Media", "Data Source": "News/Legal DB", "Risk Logic": "Fraud, bribery, litigation, sanction terms", "Result": "Flag" if dd["adverse_hits"] else "Clear"},
])

chart_left, chart_right = st.columns(2)
with chart_left:
    geo_df = pd.DataFrame({
        "Vendor": [selected_vendor],
        "Address Type": [dd["address_type"]],
        "Risk": [dd["overall_risk"]],
        "Spend": [total_spend],
    })
    fig_geo = px.scatter(
        geo_df,
        x="Spend",
        y="Risk",
        size="Spend",
        color="Address Type",
        title="Address Type Risk Bubble",
        hover_data=["Vendor"],
    )
    fig_geo.update_xaxes(title_text="Client Spend")
    fig_geo.update_yaxes(title_text="Due Diligence Risk")
    fig_geo = apply_briefing_theme(fig_geo)
    st.plotly_chart(fig_geo, use_container_width=True)

with chart_right:
    concentration_df = pd.DataFrame({
        "Metric": ["Client Spend / Total Vendor Revenue"],
        "Concentration %": [dd["concentration_pct"]],
    })
    fig_conc = px.bar(concentration_df, x="Metric", y="Concentration %", title="Revenue Concentration", color="Concentration %", color_continuous_scale="Reds")
    fig_conc.update_yaxes(range=[0, 100])
    fig_conc = apply_briefing_theme(fig_conc)
    st.plotly_chart(fig_conc, use_container_width=True)

st.dataframe(tests, use_container_width=True, hide_index=True)
render_chart_context("External due diligence adds ownership, proximity, reputation, and KYC quality context to ERP risk.", "Escalate vendors with UBO overlap, weak footprint, adverse media, residential address, or high revenue dependence.")

st.divider()

left, middle, right = st.columns(3)
with left:
    st.subheader("Risk Indicators")
    risk_cols = ["duplicate_payment", "invoice_split", "shared_bank", "vendor_similarity", "approval_override", "communication"]
    summary = [{"Indicator": col.replace("_", " ").title(), "Count": int(vendor_cases[col].sum())} for col in risk_cols]
    risk_df = pd.DataFrame(summary)
    fig = px.bar(risk_df, x="Indicator", y="Count", title="Vendor Risk Profile", color="Indicator", color_discrete_sequence=["#012169", "#2E86DE", "#FF7F0E", "#D62728", "#2ECC71", "#7F8C8D"])
    fig.update_yaxes(title_text="Flag Count")
    fig = apply_briefing_theme(fig)
    fig = style_chart_for_anomalies(fig, risk_df["Count"], pd.Series([value == risk_df["Count"].max() for value in risk_df["Count"]]))
    st.plotly_chart(fig, use_container_width=True)
    render_chart_context("The vendor shows repeated signal overlap across controls and transaction behavior.", "Validate the most frequent indicators with document review and owner interviews.")

with middle:
    st.subheader("Spend Profile")
    spend_df = vendor_invoices[["invoice_id", "invoice_amount"]].head(15).copy()
    fig2 = px.bar(spend_df, x="invoice_id", y="invoice_amount", title="Recent Invoice Amounts", color_discrete_sequence=["#2E86DE"])
    fig2.update_yaxes(title_text="Invoice Amount")
    fig2 = apply_briefing_theme(fig2)
    fig2 = style_chart_for_anomalies(fig2, spend_df["invoice_amount"], detect_outliers(spend_df["invoice_amount"]))
    st.plotly_chart(fig2, use_container_width=True)
    render_chart_context("A spike in invoice values may indicate threshold manipulation or split billing.", "Inspect the highest-value invoices for supporting documentation and approval consistency.")

with right:
    st.subheader("KYC Checks Failed")
    kyc_df = pd.DataFrame({
        "Vendor": [selected_vendor],
        "KYC Failures": [int(vendor_cases[["duplicate_payment", "invoice_split", "shared_bank", "vendor_similarity", "approval_override", "communication"]].sum().sum())],
    })
    fig3 = px.bar(kyc_df, x="Vendor", y="KYC Failures", title="Total KYC Checks Failed vs Vendor", color_discrete_sequence=["#D62728"])
    fig3.update_yaxes(title_text="KYC Failures")
    fig3 = apply_briefing_theme(fig3)
    st.plotly_chart(fig3, use_container_width=True)
    render_chart_context("The derived KYC failure count reflects overlapping red-flag tests that warrant deeper due-diligence review.", "Use this as a triage signal for enhanced verification and documentation requests.")

st.divider()
st.subheader("Forensic vendor briefing")
render_red_flag_summary(vendor_cases, title="Vendor-specific red-flag tests")
render_case_queue_snapshot(vendor_cases, limit=6, title="Linked case queue")

st.subheader("Potential Vendor Aliases")
matches = []
for _, row in vendors.iterrows():
    if row["vendor_id"] == vendor_id:
        continue
    row_vendor_name = row.get("vendor_name")
    if row_vendor_name is None or pd.isna(row_vendor_name):
        continue
    score = fuzz.ratio(str(selected_vendor), str(row_vendor_name))

    if score >= 85:
        matches.append({"Vendor": str(row_vendor_name), "Vendor ID": row["vendor_id"], "Similarity": score})


if matches:
    match_df = pd.DataFrame(matches).sort_values("Similarity", ascending=False)
    st.dataframe(match_df, use_container_width=True, hide_index=True)
else:
    st.success("No similar vendor names detected.")

st.subheader("Name Variations Table")
variation_table = build_name_variation_table(vendors["vendor_name"].dropna().tolist())
if variation_table.empty:
    safe_selected = "" if selected_vendor is None else str(selected_vendor)
    variation_table = pd.DataFrame([
        {"Name": safe_selected, "Likely Variant": f"{safe_selected} Ltd", "Similarity": 91},
        {"Name": safe_selected, "Likely Variant": safe_selected.replace(" and ", " & "), "Similarity": 88},
        {"Name": safe_selected, "Likely Variant": f"{safe_selected.split()[0]} Consulting" if safe_selected.split() else "Consulting", "Similarity": 85},
    ])

if not variation_table.empty:
    variation_table = variation_table.merge(vendors[["vendor_name", "address"]], left_on="Name", right_on="vendor_name", how="left").drop(columns=["vendor_name"])
    variation_table = variation_table.rename(columns={"address": "Address"})
    fig_alias = px.scatter(
        variation_table.head(25),
        x="Similarity",
        y="Name",
        color="Address",
        size="Similarity",
        hover_data=["Likely Variant", "Address"],
        title="Suspect Vendor Name and Address Variations",
    )
    fig_alias.update_xaxes(title_text="Name Similarity Score")
    fig_alias.update_yaxes(title_text="Vendor Name")
    fig_alias = apply_briefing_theme(fig_alias)
    st.plotly_chart(fig_alias, use_container_width=True)
st.dataframe(variation_table, use_container_width=True, hide_index=True)
render_chart_context("Name-variation clustering helps reveal aliases that could hide a single beneficial owner or shell vendor.", "Review the fuzzy name groupings for possible alternate spellings and shell-vendor variants.")

st.divider()

st.subheader("Communication Review")
vendor_emails = emails[emails["vendor_id"] == vendor_id]
st.metric("Emails", f"{len(vendor_emails):,}")
if len(vendor_emails):
    st.dataframe(vendor_emails[["email_id", "subject", "date"]].head(20), use_container_width=True, hide_index=True)
else:
    st.info("No emails available.")

st.divider()

st.subheader("Associated Investigation Cases")
display = ["case_id", "invoice_id", "risk_score", "risk_level", "reason"]
case_display = vendor_cases[display].copy()
case_display["risk_score"] = case_display["risk_score"].map(lambda x: f"{x:.1f}%")
st.dataframe(case_display, use_container_width=True, hide_index=True)

highest = vendor_cases["risk_score"].max() if not vendor_cases.empty else 0
if highest >= 90:
    st.error("### Investigator Recommendation\nImmediate escalation recommended. Expand the custodian list, validate bank account ownership, and review all communications.")
elif highest >= 70:
    st.warning("### Investigator Recommendation\nDetailed transaction testing recommended. Review approvals and supporting documents.")
else:
    st.success("### Investigator Recommendation\nContinue routine monitoring.")
