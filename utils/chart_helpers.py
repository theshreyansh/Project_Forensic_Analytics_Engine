import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from rapidfuzz import fuzz


def detect_outliers(series):
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty or len(values) < 4:
        return pd.Series(False, index=series.index, dtype=bool)

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    mask = pd.Series(False, index=series.index, dtype=bool)
    mask.loc[values.index] = (values < lower) | (values > upper)
    return mask


def style_chart_for_anomalies(fig, values, highlight_mask, base_color="#012169", anomaly_color="#d62728"):
    if not hasattr(fig, "data") or not fig.data:
        return fig

    trace_type = getattr(fig.data[0], "type", None)
    if trace_type in {"bar", "histogram"}:
        colors = [anomaly_color if bool(flag) else base_color for flag in highlight_mask.tolist()]
        fig.update_traces(marker_color=colors)
    elif trace_type in {"scatter", "line"}:
        x_values = list(fig.data[0].x or [])
        y_values = list(fig.data[0].y or [])
        if len(x_values) != len(y_values):
            return fig
        highlight_x = [x_values[idx] for idx, flag in enumerate(highlight_mask.tolist()) if flag]
        highlight_y = [y_values[idx] for idx, flag in enumerate(highlight_mask.tolist()) if flag]
        if highlight_x:
            fig.add_trace(
                go.Scatter(
                    x=highlight_x,
                    y=highlight_y,
                    mode="markers",
                    marker=dict(size=11, color=anomaly_color),
                    name="Outlier / anomaly",
                    showlegend=False,
                )
            )
    elif trace_type == "pie":
        colors = [anomaly_color if bool(flag) else base_color for flag in highlight_mask.tolist()]
        fig.update_traces(marker=dict(colors=colors))
    return fig


def apply_briefing_theme(fig):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=20, r=20, t=55, b=20),
        title_x=0.5,
        font=dict(family="Arial", size=12, color="#0f172a"),
    )
    return fig


def render_chart_context(callout, action):
    st.markdown(
        f"<div style='margin-top:8px; padding:10px 12px; border:1px solid #d9e2f0; border-radius:8px; background:#f9fbff; max-height:90px; overflow-y:auto; font-size:0.95rem;'>"
        f"<div><b>Callout:</b> {callout}</div>"
        f"<div><b>Suggested action:</b> {action}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def build_name_variation_table(names, threshold=85):
    names = [str(name).strip() for name in names if str(name).strip()]
    unique_names = sorted(set(names))
    rows = []
    seen = set()

    for i, left in enumerate(unique_names):
        for right in unique_names[i + 1:]:
            score = fuzz.ratio(left, right)
            if score >= threshold:
                pair = tuple(sorted([left, right]))
                if pair in seen:
                    continue
                seen.add(pair)
                rows.append({"Name": left, "Likely Variant": right, "Similarity": score})

    if not rows:
        return pd.DataFrame(columns=["Name", "Likely Variant", "Similarity"])

    return pd.DataFrame(rows).sort_values(["Similarity", "Name"], ascending=[False, True]).reset_index(drop=True)


def render_red_flag_summary(cases_df, title="Red-flag tests"):
    if cases_df is None or cases_df.empty:
        return pd.DataFrame(columns=["Test", "Hits"])

    indicator_columns = [
        "duplicate_payment",
        "invoice_split",
        "shared_bank",
        "vendor_similarity",
        "approval_override",
        "communication",
    ]
    available = [col for col in indicator_columns if col in cases_df.columns]
    summary = []
    for col in available:
        hits = int(cases_df[col].sum()) if pd.api.types.is_numeric_dtype(cases_df[col]) else 0
        summary.append({"Test": col.replace("_", " ").title(), "Hits": hits})

    summary_df = pd.DataFrame(summary).sort_values("Hits", ascending=False)
    st.subheader(title)
    st.dataframe(summary_df.head(8), use_container_width=True, hide_index=True)
    st.caption("Priority is ranked by the density of overlapping red-flag tests and the resulting risk score.")
    return summary_df


def render_case_queue_snapshot(cases_df, limit=8, title="Investigator case queue"):
    if cases_df is None or cases_df.empty:
        st.info("No queue items available for review.")
        return

    display_cols = [col for col in ["case_id", "vendor_id", "invoice_id", "risk_score", "risk_level", "reason"] if col in cases_df.columns]
    if not display_cols:
        return

    queue = cases_df[display_cols].copy().head(limit)
    if "risk_score" in queue.columns:
        queue["risk_score"] = queue["risk_score"].map(lambda x: f"{x:.1f}%")
    st.subheader(title)
    st.dataframe(queue, use_container_width=True, hide_index=True)
