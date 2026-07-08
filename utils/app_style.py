import streamlit as st


NAV_ITEMS = [
    ("/", "Home"),
    ("/Executive_Dashboard", "Executive"),
    ("/ERP_Analytics", "ERP Analytics"),
    ("/Vendor_Intelligence", "Vendor Intelligence"),
    ("/Network_Graph", "Network Graph"),
    ("/Communication_Review", "Communication Review"),
    ("/Case_Queue", "Case Queue"),
    ("/Evidence_Pack", "Evidence Pack"),
    ("/Din", "Din"),
]


def apply_global_style():
    st.markdown(
        """
<style>
:root {
    --ink: #1d1d1f;
    --muted: #6e6e73;
    --panel: rgba(255, 255, 255, 0.78);
    --line: rgba(0, 0, 0, 0.08);
    --blue: #0071e3;
    --green: #34c759;
    --amber: #ff9f0a;
    --red: #ff3b30;
}

[data-testid="stSidebar"], [data-testid="collapsedControl"] {
    display: none;
}

.main .block-container {
    padding-top: 1.1rem;
    max-width: 1380px;
}

html, body, [data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 12% 0%, rgba(0, 113, 227, 0.14), transparent 28rem),
        radial-gradient(circle at 88% 8%, rgba(52, 199, 89, 0.10), transparent 24rem),
        linear-gradient(180deg, #fbfbfd 0%, #f5f5f7 48%, #ffffff 100%);
    color: var(--ink);
}

h1, h2, h3 {
    color: var(--ink);
    letter-spacing: 0;
}

p, label, span, div {
    letter-spacing: 0;
}

[data-testid="stHeader"] {
    background: rgba(251, 251, 253, 0.72);
    backdrop-filter: blur(20px);
}

[data-testid="stMetric"], [data-testid="stDataFrame"], .stAlert {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 18px;
    box-shadow: 0 16px 50px rgba(0, 0, 0, 0.055);
}

[data-testid="stMetric"] {
    padding: 16px 18px;
}

.stButton > button, .stDownloadButton > button, [data-testid="stBaseButton-secondary"] {
    border-radius: 999px;
    border: 1px solid rgba(0, 113, 227, 0.20);
    background: linear-gradient(180deg, #0a84ff, #0071e3);
    color: white;
    font-weight: 650;
    min-height: 2.55rem;
    box-shadow: 0 10px 24px rgba(0, 113, 227, 0.20);
    transition: transform 180ms ease, box-shadow 180ms ease, filter 180ms ease;
}

.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-1px);
    filter: brightness(1.04);
    box-shadow: 0 16px 32px rgba(0, 113, 227, 0.28);
}

.stSelectbox, .stMultiSelect, .stTextInput, .stTextArea, .stSlider {
    background: rgba(255, 255, 255, 0.55);
    border-radius: 16px;
}

.apple-nav {
    position: sticky;
    top: 0.35rem;
    z-index: 999;
    display: flex;
    gap: 0.45rem;
    align-items: center;
    overflow-x: auto;
    padding: 0.62rem;
    margin: 0 0 1.25rem 0;
    border: 1px solid var(--line);
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.70);
    backdrop-filter: blur(24px) saturate(1.4);
    box-shadow: 0 14px 38px rgba(0, 0, 0, 0.08);
}

.apple-brand {
    flex: 0 0 auto;
    font-weight: 800;
    color: var(--ink);
    padding: 0.5rem 0.85rem;
}

.apple-tab {
    flex: 0 0 auto;
    color: var(--ink);
    text-decoration: none;
    padding: 0.5rem 0.85rem;
    border-radius: 999px;
    font-size: 0.9rem;
    line-height: 1;
    transition: background 160ms ease, color 160ms ease, transform 160ms ease, box-shadow 160ms ease, border 160ms ease;
    border: 1px solid transparent;
}

.apple-tab.active {
    color: #ffffff;
    background: #012169;
    border: 1px solid rgba(0, 113, 227, 0.35);
    box-shadow: 0 14px 30px rgba(1, 33, 105, 0.25);
}


.apple-tab:hover {
    color: #ffffff;
    background: #1d1d1f;
    transform: translateY(-1px);
}

.apple-hero {
    padding: 1.1rem 1.2rem;
    border: 1px solid var(--line);
    border-radius: 22px;
    background: rgba(255, 255, 255, 0.72);
    box-shadow: 0 20px 55px rgba(0, 0, 0, 0.055);
}

.apple-callout {
    padding: 14px 16px;
    border-radius: 18px;
    border: 1px solid rgba(0, 113, 227, 0.14);
    background: rgba(255, 255, 255, 0.72);
    box-shadow: 0 14px 34px rgba(0, 0, 0, 0.05);
}

@keyframes soft-rise {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

.element-container {
    animation: soft-rise 260ms ease both;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def render_top_tabs():
    # Query-param driven active tab styling
    # Pages can set: ?tab=<one of NAV_ITEMS labels>
    qp = st.query_params
    active_label = qp.get("tab", [""])[0] if hasattr(qp, "get") else ""

    links = ["<div class='apple-brand'>FornsicTech</div>"]
    for target, label in NAV_ITEMS:
        active_class = " active" if str(active_label) == str(label) else ""
        links.append(
            f"<a class='apple-tab{active_class}' href='{target}' target='_self'>{label}</a>"
        )
    st.markdown(f"<nav class='apple-nav'>{''.join(links)}</nav>", unsafe_allow_html=True)



def render_page_shell():
    apply_global_style()
    render_top_tabs()
