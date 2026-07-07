import streamlit as st
from config import APP_NAME, APP_SUBTITLE, VERSION

# -------------------------------------------------------
# Page Configuration
# -------------------------------------------------------

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
# Sidebar
# -------------------------------------------------------

with st.sidebar:

    st.title("Navigation")

    st.success(f"Logged in as")

    st.info(st.session_state.user_role)

    st.page_link("pages/01_Executive_Dashboard.py",label="Executive Dashboard")

    st.page_link("pages/02_ERP_Analytics.py",label="ERP Analytics")

    st.page_link("pages/03_Vendor_Intelligence.py",label="Vendor Intelligence")

    st.page_link("pages/04_Network_Graph.py",label="Relationship Network")

    st.page_link("pages/05_Communication_Review.py",label="Communication Review")

    st.page_link("pages/06_Case_Queue.py",label="Case Queue")

    st.page_link("pages/07_Evidence_Pack.py",label="Evidence Packs")

    st.divider()

    if st.button("Logout"):

        st.session_state.logged_in=False
        st.rerun()

# -------------------------------------------------------
# Home Screen
# -------------------------------------------------------

st.markdown(f"# {APP_NAME}")

st.caption(APP_SUBTITLE)

st.divider()

st.success(
"""
Welcome to the Deloitte Forensic Investigation Workbench.

Use the navigation menu on the left to access:

• Executive Dashboard

• ERP Fraud Analytics

• Vendor Intelligence

• Relationship Network

• Communication Review

• Investigation Queue

• Evidence Pack Generator

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