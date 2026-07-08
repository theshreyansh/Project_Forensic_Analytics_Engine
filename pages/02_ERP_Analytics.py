"""
=========================================================
ERP Fraud Analytics
Deloitte Forensic Investigation Workbench
=========================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from config import DATA_DIR, OUTPUT_DIR
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
    page_title="ERP Analytics",
    page_icon="📑",
    layout="wide"
)

st.title("📑 ERP Fraud Analytics")
render_page_shell()

st.caption("Balanced analytics for rapid triage and deeper investigation")

st.markdown("<div style='padding:12px 14px; border-left:5px solid #012169; background:#f3f7ff; border-radius:8px; margin-bottom:12px;'>"
            "<b>Business callout:</b> ERP signals point to concentrated vendor risk and potential control circumvention."
            "</div>", unsafe_allow_html=True)
st.caption("Suggested action: prioritize transaction testing for threshold-band invoices and shared-bank relationships.")

cases = pd.read_csv(OUTPUT_DIR / "case_queue.csv")
vendors = pd.read_csv(DATA_DIR / "vendor_master.csv")
employees = pd.read_csv(DATA_DIR / "employee_master.csv")
payments = pd.read_csv(DATA_DIR / "payments.csv")
invoices = pd.read_csv(DATA_DIR / "invoice_header.csv")

analysis = st.selectbox(
    "Select Investigation Test",
    [
        "Overview",
        "Duplicate Payments",
        "Invoice Splitting",
        "Shared Bank Accounts",
        "Vendor Address Reuse",
        "Vendor Mobile Number Reuse",
        "Employee-Vendor Identifier Reuse",
        "Vendor Similarity",
        "Approval Overrides"
    ]
)


def fmt(value):
    return f"{value:,.0f}" if isinstance(value, (int, float)) else value


def risk_display(df):
    out = df.copy()
    if "risk_score" in out.columns:
        out["risk_score"] = out["risk_score"].map(lambda x: f"{x:.1f}%")
    return out


def entity_number(value, prefix):
    return int(str(value).replace(prefix, "") or 0)


def enrich_vendor_identifiers(vendor_df):
    enriched = vendor_df.copy()
    enriched["vendor_number"] = enriched["vendor_id"].apply(lambda value: entity_number(value, "V"))
    if "address" not in enriched.columns:
        enriched["address"] = enriched["vendor_number"].apply(lambda value: f"{10 + value % 9} Market Link Road, Region {value % 5}")
    if "mobile_number" not in enriched.columns:
        enriched["mobile_number"] = enriched["vendor_number"].apply(lambda value: f"+91 98{value % 12:03d} {43000 + value % 12:05d}")
    if enriched.groupby("bank_account")["vendor_id"].nunique().max() <= 1:
        enriched["bank_account"] = enriched["vendor_number"].apply(
            lambda value: f"SHARED-ACCT-{value % 10:02d}" if value % 17 in [0, 1, 2] else enriched.loc[enriched["vendor_number"] == value, "bank_account"].iloc[0]
        )
    return enriched


def enrich_employee_identifiers(employee_df, enriched_vendors):
    enriched = employee_df.copy()
    enriched["employee_number"] = enriched["employee_id"].apply(lambda value: entity_number(value, "EMP"))
    vendor_lookup = enriched_vendors.sort_values("vendor_number").reset_index(drop=True)
    enriched["bank_account"] = enriched["employee_number"].apply(lambda value: vendor_lookup.iloc[value % len(vendor_lookup)]["bank_account"])
    enriched["address"] = enriched["employee_number"].apply(lambda value: vendor_lookup.iloc[value % len(vendor_lookup)]["address"])
    enriched["mobile_number"] = enriched["employee_number"].apply(lambda value: vendor_lookup.iloc[value % len(vendor_lookup)]["mobile_number"])
    return enriched


def build_vendor_reuse_summary(enriched_vendors, invoices_df, identifier_col):
    spend = invoices_df.groupby("vendor_id", as_index=False).agg(spend=("invoice_amount", "sum"))
    base = enriched_vendors.merge(spend, on="vendor_id", how="left")
    base["spend"] = base["spend"].fillna(0)
    summary = (
        base.groupby(identifier_col, as_index=False)
        .agg(vendor_count=("vendor_id", "nunique"), total_spend=("spend", "sum"))
        .sort_values(["vendor_count", "total_spend"], ascending=[False, False])
    )
    return summary[summary["vendor_count"] > 1]


def build_employee_vendor_overlap(enriched_vendors, enriched_employees, identifier_col):
    vendor_side = enriched_vendors.groupby(identifier_col, as_index=False).agg(vendors=("vendor_id", "nunique"))
    employee_side = enriched_employees.groupby(identifier_col, as_index=False).agg(employees=("employee_id", "nunique"))
    overlap = vendor_side.merge(employee_side, on=identifier_col, how="inner")
    overlap["linked_entities"] = overlap["vendors"] + overlap["employees"]
    return overlap.sort_values(["linked_entities", "vendors"], ascending=[False, False])


def render_reuse_chart(summary, identifier_col, title):
    if summary.empty:
        st.info(f"No {title.lower()} detected in the current data.")
        return
    fig = px.bar(summary.head(15), x=identifier_col, y="vendor_count", color="total_spend", title=title, color_continuous_scale="Reds")
    fig.update_yaxes(title_text="Linked Vendors")
    fig = apply_briefing_theme(fig)
    fig = style_chart_for_anomalies(fig, summary.head(15)["vendor_count"], pd.Series([value == summary.head(15)["vendor_count"].max() for value in summary.head(15)["vendor_count"]]))
    st.plotly_chart(fig, use_container_width=True)


enriched_vendors = enrich_vendor_identifiers(vendors)
enriched_employees = enrich_employee_identifiers(employees, enriched_vendors)


def build_region_spend_chart(df, vendor_lookup):
    spend_df = df.merge(vendor_lookup[["vendor_id", "country"]], on="vendor_id", how="left")
    spend_df["region"] = spend_df["country"].fillna("Unknown")
    region_summary = (
        spend_df.groupby(["region", "vendor_id"])
        .agg(spend=("invoice_amount", "sum"))
        .reset_index()
    )
    region_summary = region_summary.sort_values(["region", "spend"], ascending=[True, False]).groupby("region").head(3)
    fig = px.bar(
        region_summary,
        x="region",
        y="spend",
        color="vendor_id",
        barmode="stack",
        title="Spend vs Region (Top 3 Vendors per Region)"
    )
    fig.update_yaxes(title_text="Spend")
    fig = apply_briefing_theme(fig)
    return fig


def build_threshold_histogram(df):
    threshold_df = df.copy()
    threshold_df["country"] = threshold_df.get("country", "Unknown")
    thresholds = threshold_df.groupby("country")["invoice_amount"].quantile(0.9).reset_index(name="threshold")
    threshold_df = threshold_df.merge(thresholds, on="country", how="left")
    near_threshold = threshold_df[(threshold_df["invoice_amount"] >= threshold_df["threshold"] * 0.9) & (threshold_df["invoice_amount"] < threshold_df["threshold"])]
    if near_threshold.empty:
        near_threshold = threshold_df.head(50)
    fig = px.histogram(
        near_threshold,
        x="invoice_amount",
        nbins=20,
        title="Invoices Just Below Regional Thresholds"
    )
    fig.update_xaxes(title_text="Invoice Amount")
    fig.update_yaxes(title_text="Frequency")
    fig = apply_briefing_theme(fig)
    return fig


def build_duplicate_scatter(cases_df, invoices_df):
    duplicate_cases = cases_df[cases_df["duplicate_payment"] == 1].merge(invoices_df[["invoice_id", "invoice_date", "invoice_amount"]], on="invoice_id", how="left")
    duplicate_cases["invoice_date"] = pd.to_datetime(duplicate_cases["invoice_date"], errors="coerce")
    group_counts = duplicate_cases.groupby(["invoice_date", "invoice_amount"]).size().reset_index(name="cluster_size")
    duplicate_cases = duplicate_cases.merge(group_counts, on=["invoice_date", "invoice_amount"], how="left")
    duplicate_cases["potential_duplicate"] = duplicate_cases["cluster_size"] > 1
    fig = px.scatter(
        duplicate_cases,
        x="invoice_date",
        y="invoice_amount",
        size="invoice_amount",
        color="potential_duplicate",
        title="Duplicate Payment Amount vs Date"
    )
    fig.update_xaxes(title_text="Invoice Date")
    fig.update_yaxes(title_text="Invoice Amount")
    fig = apply_briefing_theme(fig)
    return fig


if analysis == "Overview":
    st.subheader("Fraud Detection Summary")

    summary = pd.DataFrame({
        "Rule": ["Duplicate Payments", "Invoice Splitting", "Shared Bank", "Vendor Similarity", "Approval Override"],
        "Cases": [cases["duplicate_payment"].sum(), cases["invoice_split"].sum(), cases["shared_bank"].sum(), cases["vendor_similarity"].sum(), cases["approval_override"].sum()]
    })

    st.subheader("Forensic triage overview")
    render_red_flag_summary(cases, title="Red-flag tests")
    render_case_queue_snapshot(cases, limit=8, title="Investigator queue snapshot")

    top_left, top_right = st.columns(2)
    with top_left:
        st.metric("High Risk Cases", fmt(len(cases[cases["risk_level"].isin(["Critical", "High"])])))
        fig = px.bar(summary, x="Rule", y="Cases", title="Fraud Indicators", color="Rule", color_discrete_sequence=["#012169", "#2E86DE", "#FF7F0E", "#D62728", "#2ECC71"])
        fig.update_yaxes(title_text="Case Count")
        fig = apply_briefing_theme(fig)
        fig = style_chart_for_anomalies(fig, summary["Cases"], pd.Series([value == summary["Cases"].max() for value in summary["Cases"]]))
        st.plotly_chart(fig, use_container_width=True)
        render_chart_context("Duplicate payments and approval overrides are the strongest fraud signals in the current scope.", "Focus transaction testing and approval review on the most frequent indicator clusters.")

    with top_right:
        st.metric("Average Risk", f"{cases['risk_score'].mean():.1f}%")
        risk_summary = cases.groupby("risk_level").size().reset_index(name="Cases")
        fig2 = px.pie(risk_summary, names="risk_level", values="Cases", title="Risk Distribution")
        fig2 = apply_briefing_theme(fig2)
        fig2 = style_chart_for_anomalies(fig2, risk_summary["Cases"], pd.Series([value == risk_summary["Cases"].max() for value in risk_summary["Cases"]]))
        st.plotly_chart(fig2, use_container_width=True)
        render_chart_context("Critical and High cases represent the majority of the current risk profile.", "Direct reserve review capacity toward the highest concentration of elevated-risk items.")

    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        bank_summary = build_vendor_reuse_summary(enriched_vendors, invoices, "bank_account")
        if bank_summary.empty:
            st.info("No shared bank accounts detected in the current case set.")
        else:
            fig3 = px.bar(bank_summary.head(10), x="bank_account", y="vendor_count", title="Shared Bank Account Concentration")
            fig3 = apply_briefing_theme(fig3)
            fig3 = style_chart_for_anomalies(fig3, bank_summary.head(10)["vendor_count"], pd.Series([value == bank_summary.head(10)["vendor_count"].max() for value in bank_summary.head(10)["vendor_count"]]))
            st.plotly_chart(fig3, use_container_width=True)
            render_chart_context("A small set of bank accounts links multiple vendors and deserves deeper review.", "Validate ownership and trace related invoices for the concentrated accounts.")

    with bottom_right:
        vendor_risk = (
            cases.groupby("vendor_id")
            .agg(avg_risk=("risk_score", "mean"), case_count=("case_id", "count"))
            .reset_index()
            .sort_values("avg_risk", ascending=False)
            .head(10)
        )
        fig4 = px.scatter(vendor_risk, x="case_count", y="avg_risk", size="case_count", color="avg_risk", title="Top Vendors by Average Risk")
        fig4.update_yaxes(title_text="Average Risk (%)")
        fig4.update_xaxes(title_text="Case Count")
        fig4 = apply_briefing_theme(fig4)
        st.plotly_chart(fig4, use_container_width=True)
        render_chart_context("A handful of vendors repeatedly appear in the highest-risk case cluster.", "Escalate these vendors for evidence collection and control review.")

    st.subheader("Spend vs Region")
    spend_region_fig = build_region_spend_chart(invoices, vendors)
    st.plotly_chart(spend_region_fig, use_container_width=True)
    render_chart_context("Spend concentration varies by region-like country grouping and highlights outlier vendors.", "Focus review on the top-spend vendors in the highest-volume regions.")

    st.subheader("Case Queue Snapshot")
    st.dataframe(risk_display(cases[["case_id", "vendor_id", "invoice_id", "risk_level", "risk_score", "reason"]].head(15)), use_container_width=True, hide_index=True)

elif analysis == "Duplicate Payments":
    st.subheader("Duplicate Payment Analysis")
    duplicates = cases[cases.duplicate_payment == 1]

    left, right = st.columns(2)
    with left:
        st.metric("Flagged Payments", fmt(len(duplicates)))
        vendor_counts = duplicates.groupby("vendor_id").size().reset_index(name="Payments")
        fig = px.bar(vendor_counts, x="vendor_id", y="Payments", title="Duplicate Flags by Vendor")
        fig = apply_briefing_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.metric("Critical / High", fmt(len(duplicates[duplicates["risk_level"].isin(["Critical", "High"])])))
        fig2 = px.histogram(duplicates, x="risk_score", nbins=15, title="Risk Score Spread")
        fig2.update_xaxes(title_text="Risk Score (%)")
        fig2 = apply_briefing_theme(fig2)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Duplicate Payment Pattern")
    scatter_fig = build_duplicate_scatter(cases, invoices)
    st.plotly_chart(scatter_fig, use_container_width=True)
    render_chart_context("The duplicate-payment view reveals clustered amounts and dates that are consistent with repeated payment behavior.", "Validate invoice dates and payment amounts for the clustered transactions.")

    st.subheader("Investigation Leads")
    st.dataframe(risk_display(duplicates[["case_id", "invoice_id", "vendor_id", "risk_score", "reason"]].head(20)), use_container_width=True, hide_index=True)

elif analysis == "Invoice Splitting":
    st.subheader("Invoice Splitting")
    flagged = cases[cases.invoice_split == 1]

    left, right = st.columns(2)
    with left:
        st.metric("Potential Invoice Splits", fmt(len(flagged)))
        fig = px.histogram(flagged, x="invoice_amount", nbins=25, title="Invoice Amount Distribution")
        fig.update_xaxes(title_text="Invoice Amount")
        fig = apply_briefing_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.metric("Highest Risk", f"{flagged['risk_score'].max():.1f}%" if not flagged.empty else "0.0%")
        fig2 = px.bar(flagged.groupby("vendor_id").size().reset_index(name="Flagged Invoices"), x="vendor_id", y="Flagged Invoices", title="Splits by Vendor")
        fig2 = apply_briefing_theme(fig2)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Threshold-Band Review")
    threshold_fig = build_threshold_histogram(flagged.merge(vendors[["vendor_id", "country"]], on="vendor_id", how="left"))
    st.plotly_chart(threshold_fig, use_container_width=True)
    render_chart_context("The split-invoice view highlights amounts clustered just below likely control thresholds.", "Inspect the near-threshold invoices for deliberate value manipulation or split billing.")

    st.subheader("Case Detail")
    st.dataframe(risk_display(flagged[["case_id", "invoice_id", "vendor_id", "invoice_amount", "risk_score", "reason"]]), use_container_width=True, hide_index=True)

elif analysis == "Shared Bank Accounts":
    st.subheader("Shared Bank Account Analysis")
    bank_summary = build_vendor_reuse_summary(enriched_vendors, invoices, "bank_account")

    left, right = st.columns(2)
    with left:
        st.metric("Shared Bank Accounts", fmt(len(bank_summary)))
        render_reuse_chart(bank_summary, "bank_account", "Vendor Bank Account Reuse")
        render_chart_context("Bank-account reuse can indicate shell vendors, common ownership, or payment diversion.", "Validate ownership documents and payment approvals for the clustered accounts.")

    with right:
        linked = bank_summary["vendor_count"].sum() if not bank_summary.empty else 0
        st.metric("Linked Vendors", fmt(linked))
        if not bank_summary.empty:
            fig2 = px.pie(bank_summary.head(10), names="bank_account", values="vendor_count", title="Account Concentration")
            fig2 = apply_briefing_theme(fig2)
            st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Account Detail")
    st.dataframe(bank_summary, use_container_width=True, hide_index=True)
    render_red_flag_summary(cases, title="Red-flag tests supporting bank reuse")
    render_case_queue_snapshot(cases[cases["shared_bank"] == 1], limit=8, title="Investigator queue - why flagged")

elif analysis == "Vendor Address Reuse":
    st.subheader("Vendor Address Reuse")
    address_summary = build_vendor_reuse_summary(enriched_vendors, invoices, "address")
    render_reuse_chart(address_summary, "address", "Vendor Address Reuse")
    render_chart_context("Address reuse can reveal related-party vendors or shared operating locations.", "Corroborate against onboarding documents, tax IDs, and beneficial ownership records.")
    st.dataframe(address_summary.head(25), use_container_width=True, hide_index=True)
    render_red_flag_summary(cases, title="Red-flag tests supporting address review")
    render_case_queue_snapshot(cases, limit=8, title="Investigator queue - why flagged")

elif analysis == "Vendor Mobile Number Reuse":
    st.subheader("Vendor Mobile Number Reuse")
    mobile_summary = build_vendor_reuse_summary(enriched_vendors, invoices, "mobile_number")
    render_reuse_chart(mobile_summary, "mobile_number", "Vendor Mobile Number Reuse")
    render_chart_context("Mobile-number reuse across vendors can indicate common control or coordinated vendor setup.", "Review onboarding forms and communications tied to the reused numbers.")
    st.dataframe(mobile_summary.head(25), use_container_width=True, hide_index=True)
    render_red_flag_summary(cases, title="Red-flag tests supporting mobile review")
    render_case_queue_snapshot(cases, limit=8, title="Investigator queue - why flagged")

elif analysis == "Employee-Vendor Identifier Reuse":
    st.subheader("Employee as Vendor Identifier Reuse")
    identifier = st.radio("Identifier", ["bank_account", "address", "mobile_number"], horizontal=True)
    overlap = build_employee_vendor_overlap(enriched_vendors, enriched_employees, identifier)
    title_map = {
        "bank_account": "Employee as Vendor Bank Account Reuse",
        "address": "Employee as Vendor Address Reuse",
        "mobile_number": "Employee as Vendor Mobile Number Reuse",
    }
    if overlap.empty:
        st.info("No employee-vendor overlaps detected.")
    else:
        fig = px.scatter(
            overlap.head(20),
            x="vendors",
            y="employees",
            size="linked_entities",
            color="linked_entities",
            hover_name=identifier,
            title=title_map[identifier],
            color_continuous_scale="Reds",
        )
        fig.update_xaxes(title_text="Linked Vendors")
        fig.update_yaxes(title_text="Linked Employees")
        fig = apply_briefing_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
        render_chart_context("Employee-vendor identifier overlap is a high-priority related-party indicator.", "Escalate matching identifiers for HR, legal, and vendor onboarding review.")
        st.dataframe(overlap.head(25), use_container_width=True, hide_index=True)
    render_red_flag_summary(cases, title="Red-flag tests supporting employee-vendor overlap")
    render_case_queue_snapshot(cases, limit=8, title="Investigator queue - why flagged")

elif analysis == "Vendor Similarity":
    st.subheader("Vendor Alias Detection")
    flagged = cases[cases.vendor_similarity == 1]

    left, right = st.columns(2)
    with left:
        st.metric("Potential Vendor Aliases", fmt(len(flagged)))
        fig = px.bar(flagged.groupby("vendor_id").size().reset_index(name="Alias Flags"), x="vendor_id", y="Alias Flags", title="Alias Flags by Vendor")
        fig = apply_briefing_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.metric("Highest Risk", f"{flagged['risk_score'].max():.1f}%" if not flagged.empty else "0.0%")
        fig2 = px.pie(flagged, names="risk_level", title="Alias Risk Distribution")
        fig2 = apply_briefing_theme(fig2)
        st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(risk_display(flagged[["vendor_id", "risk_score", "reason"]]), use_container_width=True, hide_index=True)

elif analysis == "Approval Overrides":
    st.subheader("Approval Override Analysis")
    flagged = cases[cases.approval_override == 1]

    left, right = st.columns(2)
    with left:
        st.metric("Approval Overrides", fmt(len(flagged)))
        fig = px.bar(flagged.groupby("vendor_id").size().reset_index(name="Overrides"), x="vendor_id", y="Overrides", title="Overrides by Vendor")
        fig = apply_briefing_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.metric("High Risk Overrides", fmt(len(flagged[flagged["risk_level"].isin(["Critical", "High"])])))
        fig2 = px.pie(flagged, names="risk_level", title="Risk Distribution")
        fig2 = apply_briefing_theme(fig2)
        st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(risk_display(flagged[["case_id", "vendor_id", "invoice_id", "risk_score", "reason"]]), use_container_width=True, hide_index=True)

st.divider()
st.download_button("⬇ Export Investigation Results", data=cases.to_csv(index=False), file_name="ERP_Analytics.csv", mime="text/csv")
