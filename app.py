import streamlit as st
from config import APP_NAME, APP_SUBTITLE, VERSION
from utils.app_style import apply_global_style, render_top_tabs

# -------------------------------------------------------
# Page Configuration
# -------------------------------------------------------

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_global_style()

# -------------------------------------------------------
# Session State
# -------------------------------------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_role" not in st.session_state:
    st.session_state.user_role = ""

# -------------------------------------------------------
# Custom CSS
# -------------------------------------------------------

st.markdown("""
<style>

.main-title{
    font-size:34px;
    font-weight:700;
    color:#012169;
}

.subtitle{
    color:gray;
    font-size:18px;
}

.metric-card{
    background:#f7f7f7;
    border-radius:12px;
    padding:15px;
}

.footer{
    color:gray;
    text-align:center;
    font-size:12px;
    margin-top:50px;
}

</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Login Screen
# -------------------------------------------------------

if not st.session_state.logged_in:

    st.markdown("<div class='main-title'>Deloitte Forensic Investigation Workbench</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Procurement Fraud Investigation Accelerator</div>", unsafe_allow_html=True)

    st.write("")

    col1,col2,col3 = st.columns([1,2,1])

    with col2:

        st.subheader("User Login")

        username = st.text_input("Username")

        password = st.text_input("Password", type="password")

        role = st.selectbox(
            "Role",
            [
                "Manager",
                "Investigator",
                "Legal Counsel",
                "Compliance"
            ]
        )

        if st.button("Login", use_container_width=True):

            if username=="admin" and password=="admin":

                st.session_state.logged_in=True
                st.session_state.user_role=role
                st.rerun()

            else:
                st.error("Invalid credentials")

    st.stop()

# -------------------------------------------------------
# Home Screen
# -------------------------------------------------------

render_top_tabs()

session_col, logout_col = st.columns([5, 1])
with session_col:
    st.caption(f"Logged in as {st.session_state.user_role}")
with logout_col:
    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in=False
        st.rerun()

st.markdown(f"# {APP_NAME}")

st.caption(APP_SUBTITLE)

st.divider()

nav_cols = st.columns(8)
page_links = [
    ("pages/01_Executive_Dashboard.py", "Executive Dashboard"),
    ("pages/02_ERP_Analytics.py", "ERP Analytics"),
    ("pages/03_Vendor_Intelligence.py", "Vendor Intelligence"),
    ("pages/04_Network_Graph.py", "Network Graph"),
    ("pages/05_Communication_Review.py", "Communication Review"),
    ("pages/06_Case_Queue.py", "Case Queue"),
    ("pages/07_Evidence_Pack.py", "Evidence Pack"),
    ("pages/09_Din.py", "Din"),
]
for col, (page, label) in zip(nav_cols, page_links):
    with col:
        st.page_link(page, label=label)

st.divider()

st.success(
"""
Welcome to the Deloitte Forensic Investigation Workbench.

Use the tabs above to access:

• Executive Dashboard
• ERP Fraud Analytics
• Vendor Intelligence
• Network Graph
• Communication Review
• Case Queue
• Evidence Pack
"""
)

st.info(
"""
Interview Demo Flow

1. Executive Dashboard

2. ERP Red Flags

3. Vendor Intelligence

4. Network Analysis

5. Communication Review

6. Case Queue

7. Evidence Pack
"""
)

st.divider()

st.markdown(
f"<div class='footer'>Version {VERSION} | Deloitte Forensic Technology Accelerator Demo</div>",
unsafe_allow_html=True
)
