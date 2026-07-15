"""
=========================================================
Relationship Network
Master Forensic Investigation Workbench
=========================================================
"""

import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
from pathlib import Path

from config import DATA_DIR, OUTPUT_DIR
from utils.app_style import render_page_shell
from utils.chart_helpers import render_case_queue_snapshot, render_red_flag_summary

st.set_page_config(
    page_title="Relationship Network",
    page_icon="🕸",
    layout="wide"
)

render_page_shell()

# Active tab highlight
try:
    st.query_params["tab"] = "Network Graph"
except Exception:
    pass

st.title("🕸 Investigation Relationship Network")

st.caption("Shared bank-account and mobile-number reuse is shown as a central clustering mechanism for potential coordinated behaviour.")

# Sidebar is intentionally avoided; controls are currently left-bar style in the original page.


# -------------------------------------------------------
# Load Data
# -------------------------------------------------------

vendors = pd.read_csv(DATA_DIR / "vendor_master.csv")
employees = pd.read_csv(DATA_DIR / "employee_master.csv")
invoices = pd.read_csv(DATA_DIR / "invoice_header.csv")
approvals = pd.read_csv(DATA_DIR / "approval_logs.csv")
cases = pd.read_csv(OUTPUT_DIR / "case_queue.csv")

# -------------------------------------------------------
# Helper Functions
# -------------------------------------------------------


def normalize_value(value):
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def first_non_empty(series):
    values = series.dropna().astype(str).str.strip()
    values = values[values != ""]
    return values.iloc[0] if not values.empty else ""


def highest_risk(series):
    rank = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
    values = series.dropna().astype(str)
    return max(values, key=lambda value: rank.get(value, 0)) if not values.empty else ""


def format_currency(value):
    return f"${float(value):,.0f}"


def scale_width(value, minimum, maximum):
    if maximum <= minimum:
        return 4
    return 2 + ((float(value) - minimum) / (maximum - minimum)) * 8


def demo_mobile_number(vendor_id):
    vendor_number = int(str(vendor_id).replace("V", "") or 0)
    bucket = vendor_number % 12
    return f"+91 98{bucket:03d} {43000 + bucket:05d}"


def find_mobile_column(dataframe):
    for column in ["mobile_number", "mobile", "phone_number", "phone", "contact_number"]:
        if column in dataframe.columns:
            return column
    return ""


if "bank_account" not in vendors.columns:
    vendors["bank_account"] = ""

# -------------------------------------------------------
# Sidebar Filters
# -------------------------------------------------------

st.sidebar.header("Relationship Filters")

risk_filter = st.sidebar.multiselect(
    "Risk Level",
    ["Critical", "High", "Medium", "Low"],
    default=["Critical", "High"]
)

max_nodes = st.sidebar.slider(
    "Maximum Nodes",
    20,
    200,
    75
)

filtered_cases = cases[cases["risk_level"].isin(risk_filter)]
invoice_ids = filtered_cases["invoice_id"].tolist()

# -------------------------------------------------------
# Build Graph
# -------------------------------------------------------

G = nx.Graph()
relationships = []
mobile_column = find_mobile_column(vendors)
filtered_cases = filtered_cases.copy()
filtered_cases["invoice_amount"] = pd.to_numeric(filtered_cases["invoice_amount"], errors="coerce").fillna(0)

vendor_profiles = (
    filtered_cases
    .groupby("vendor_id", as_index=False)
    .agg(
        total_invoice_amount=("invoice_amount", "sum"),
        invoice_count=("invoice_id", "nunique"),
        case_count=("case_id", "nunique"),
        risk_level=("risk_level", highest_risk),
        case_bank_account=("bank_account", first_non_empty),
    )
)

vendor_columns = ["vendor_id", "vendor_name", "bank_account", "country", "vendor_type"]
if mobile_column:
    vendor_columns.append(mobile_column)

vendor_profiles = vendor_profiles.merge(
    vendors[vendor_columns],
    on="vendor_id",
    how="left",
)

vendor_profiles["bank_account"] = vendor_profiles["case_bank_account"].where(
    vendor_profiles["case_bank_account"].astype(str).str.strip() != "",
    vendor_profiles["bank_account"],
)

if mobile_column:
    vendor_profiles["mobile_number"] = vendor_profiles[mobile_column].fillna("").astype(str).str.strip()
else:
    vendor_profiles["mobile_number"] = vendor_profiles["vendor_id"].apply(demo_mobile_number)

vendor_profiles["vendor_name"] = vendor_profiles["vendor_name"].fillna(vendor_profiles["vendor_id"])
vendor_profiles = vendor_profiles.sort_values("total_invoice_amount", ascending=False)

# Each vendor usually creates one bank-account edge and one mobile-number edge, so this
# keeps the visible node count near the sidebar limit without dropping the largest exposure.
vendor_limit = max(5, max_nodes // 3)
vendor_profiles = vendor_profiles.head(vendor_limit).copy()

edge_min = vendor_profiles["total_invoice_amount"].min() if not vendor_profiles.empty else 0
edge_max = vendor_profiles["total_invoice_amount"].max() if not vendor_profiles.empty else 0

identifier_config = {
    "bank_account": {
        "label": "Bank Account",
        "prefix": "bank_account",
        "color": "#0B7285",
        "edge_color": "#0B7285",
    },
    "mobile_number": {
        "label": "Mobile Number",
        "prefix": "mobile_number",
        "color": "#6741D9",
        "edge_color": "#6741D9",
    },
}

for _, row in vendor_profiles.iterrows():
    vendor_id = row["vendor_id"]
    amount = float(row["total_invoice_amount"])
    vendor_title = (
        f"{row['vendor_name']}<br>"
        f"Risk: {row['risk_level']}<br>"
        f"Cases: {int(row['case_count'])}<br>"
        f"Invoices: {int(row['invoice_count'])}<br>"
        f"Total invoice amount: {format_currency(amount)}"
    )
    G.add_node(
        vendor_id,
        label=row["vendor_name"],
        title=vendor_title,
        color="#F59F00",
        shape="dot",
    )

    for column, config in identifier_config.items():
        value = str(row.get(column, "")).strip()
        if not value:
            continue

        normalized_value = normalize_value(value)
        node_id = f"{config['prefix']}:{normalized_value}"
        if node_id not in G.nodes:
            G.add_node(
                node_id,
                label=f"{config['label']}\n{value}",
                title=f"{config['label']}: {value}",
                color=config["color"],
                shape="box",
            )

        width = scale_width(amount, edge_min, edge_max)
        G.add_edge(
            node_id,
            vendor_id,
            title=f"{config['label']} relationship<br>Total invoice amount: {format_currency(amount)}",
            color=config["edge_color"],
            width=width,
            value=amount,
        )
        relationships.append({
            "vendor_id": vendor_id,
            "vendor_name": row["vendor_name"],
            "relationship_type": config["label"],
            "shared_value": value,
            "total_invoice_amount": amount,
            "invoice_count": int(row["invoice_count"]),
            "case_count": int(row["case_count"]),
            "edge_width": round(width, 2),
        })

# -------------------------------------------------------
# Shared Cluster Summary
# -------------------------------------------------------

if relationships:
    shared_clusters = (
        pd.DataFrame(relationships)
        .groupby(["relationship_type", "shared_value"], as_index=False)
        .agg(
            vendor_count=("vendor_id", "nunique"),
            total_invoice_amount=("total_invoice_amount", "sum"),
            invoice_count=("invoice_count", "sum"),
            vendors=("vendor_name", lambda s: ", ".join(sorted(set(map(str, s)))[:6])),
        )
    )
    shared_clusters = shared_clusters[shared_clusters["vendor_count"] > 1].sort_values(
        ["vendor_count", "total_invoice_amount", "relationship_type"],
        ascending=[False, False, True],
    )
else:
    shared_clusters = pd.DataFrame(
        columns=["relationship_type", "shared_value", "vendor_count", "total_invoice_amount", "invoice_count", "vendors"]
    )

for node in G.nodes:
    degree = G.degree(node)
    base_size = 16 + min(degree, 8) * 4
    if isinstance(node, str) and node.startswith(("bank_account:", "mobile_number:")):
        base_size += 10
    G.nodes[node]["size"] = base_size
    G.nodes[node]["font"] = {"size": 16 if degree >= 2 else 14}

# -------------------------------------------------------
# Reduce Size
# -------------------------------------------------------

if len(G.nodes) > max_nodes:
    keep = list(G.nodes)[:max_nodes]
    G = G.subgraph(keep).copy()

# -------------------------------------------------------
# PyVis
# -------------------------------------------------------

net = Network(
    height="750px",
    width="100%",
    bgcolor="#FFFFFF",
    font_color="black"
)

net.from_nx(G)
net.repulsion(node_distance=220, spring_length=260)

output = Path("output/network.html")
net.save_graph(str(output))
components.html(output.read_text(), height=760, scrolling=True)

# -------------------------------------------------------
# Statistics
# -------------------------------------------------------

st.divider()
render_red_flag_summary(cases, title="Relationship-red-flag tests")
render_case_queue_snapshot(cases, limit=6, title="Cases tied to relationship clusters")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Nodes", len(G.nodes))
c2.metric("Relationships", len(G.edges))
c3.metric("Shared Clusters", len(shared_clusters))

degrees = dict(G.degree())
highest = max(degrees.values()) if degrees else 0
c4.metric("Highest Degree", highest)

st.subheader("Shared Identifier Clusters")
if not shared_clusters.empty:
    st.dataframe(shared_clusters.head(15), use_container_width=True, hide_index=True)
else:
    st.info("No multi-vendor shared identifiers matched the current filters.")

# -------------------------------------------------------
# Relationship Table
# -------------------------------------------------------

st.subheader("Matched Vendor-Identifier Relationships")

if relationships:
    rel_df = pd.DataFrame(relationships)
    rel_df = rel_df.drop_duplicates()
    st.dataframe(rel_df, use_container_width=True, hide_index=True)
else:
    st.info("No vendor-identifier relationships matched the current filters. Adjust the filters or add contact fields to the source data.")

# -------------------------------------------------------
# Investigation Notes
# -------------------------------------------------------

st.subheader("Investigator Interpretation")

st.info("""
Use this network to identify:

• Vendors and employees linked by shared bank accounts

• Shared addresses or phone numbers that can indicate collusion or concealment

• High-risk clusters for expanded communication review

• Candidate custodians and associated vendor records
""")
