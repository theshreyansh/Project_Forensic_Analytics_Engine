"""
=========================================================
Relationship Network
Deloitte Forensic Investigation Workbench
=========================================================
"""

import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
from pathlib import Path

from config import DATA_DIR, OUTPUT_DIR

st.set_page_config(
    page_title="Relationship Network",
    page_icon="🕸",
    layout="wide"
)

st.title("🕸 Investigation Relationship Network")

# -------------------------------------------------------
# Load Data
# -------------------------------------------------------

vendors = pd.read_csv(DATA_DIR / "vendor_master.csv")
employees = pd.read_csv(DATA_DIR / "employee_master.csv")
invoices = pd.read_csv(DATA_DIR / "invoice_header.csv")
payments = pd.read_csv(DATA_DIR / "payments.csv")
approvals = pd.read_csv(DATA_DIR / "approval_logs.csv")
cases = pd.read_csv(OUTPUT_DIR / "case_queue.csv")

# -------------------------------------------------------
# Filters
# -------------------------------------------------------

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
# Graph
# -------------------------------------------------------

G = nx.Graph()

# Vendors
for _, row in vendors.iterrows():

    G.add_node(
        row["vendor_id"],
        label=row["vendor_name"],
        title="Vendor",
        color="#FF9800"
    )

# Employees
for _, row in employees.iterrows():

    G.add_node(
        row["employee_id"],
        label=row["employee_name"],
        title="Employee",
        color="#2196F3"
    )

# Bank Accounts
for _, row in vendors.iterrows():

    G.add_node(
        row["bank_account"],
        label=row["bank_account"],
        title="Bank Account",
        color="#4CAF50"
    )

# Invoice Nodes
for _, row in invoices[
    invoices.invoice_id.isin(invoice_ids)
].iterrows():

    G.add_node(
        row["invoice_id"],
        label=row["invoice_id"],
        title="Invoice",
        color="#E91E63"
    )

# -------------------------------------------------------
# Relationships
# -------------------------------------------------------

# Vendor -> Bank

for _, row in vendors.iterrows():

    G.add_edge(
        row["vendor_id"],
        row["bank_account"],
        title="Owns"
    )

# Vendor -> Invoice

for _, row in invoices[
    invoices.invoice_id.isin(invoice_ids)
].iterrows():

    G.add_edge(
        row["vendor_id"],
        row["invoice_id"],
        title="Issued"
    )

# Employee -> Invoice

merged = approvals.merge(
    invoices,
    on="invoice_id"
)

for _, row in merged.iterrows():

    if row["invoice_id"] in invoice_ids:

        G.add_edge(
            row["approver"],
            row["invoice_id"],
            title="Approved"
        )

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

net.repulsion(
    node_distance=200,
    spring_length=250
)

output = Path("output/network.html")

net.save_graph(str(output))

components.html(
    output.read_text(),
    height=760,
    scrolling=True
)

# -------------------------------------------------------
# Statistics
# -------------------------------------------------------

st.divider()

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Nodes",
    len(G.nodes)
)

c2.metric(
    "Relationships",
    len(G.edges)
)

c3.metric(
    "Connected Components",
    nx.number_connected_components(G)
)

degrees = dict(G.degree())

highest = max(degrees.values()) if degrees else 0

c4.metric(
    "Highest Degree",
    highest
)

# -------------------------------------------------------
# Top Connected Entities
# -------------------------------------------------------

st.subheader("Most Connected Entities")

ranking = pd.DataFrame({

    "Entity": list(degrees.keys()),

    "Connections": list(degrees.values())

}).sort_values(
    "Connections",
    ascending=False
)

st.dataframe(
    ranking.head(20),
    use_container_width=True,
    hide_index=True
)

# -------------------------------------------------------
# Investigation Notes
# -------------------------------------------------------

st.subheader("Investigator Interpretation")

st.info("""
Use this network to identify:

• Vendors sharing bank accounts

• Employees approving multiple high-risk invoices

• Highly connected vendors

• Isolated clusters

• Potential collusion patterns

• Candidate custodians for communication review
""")