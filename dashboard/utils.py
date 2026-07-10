# =============================================================================
# utils.py — Reusable UI helpers: KPI cards, chart wrappers, download buttons
# =============================================================================

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from config import (
    COLOR_SEQUENCE, CHART_HEIGHT, CHART_TEMPLATE, TOP_N_DEFAULT, PRIMARY_COLOR
)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE SETUP
# ─────────────────────────────────────────────────────────────────────────────

def page_header(title: str, subtitle: str = "") -> None:
    """Render a styled page header with an optional subtitle."""
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)
    st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# KPI / METRIC CARDS
# ─────────────────────────────────────────────────────────────────────────────

def kpi_row(metrics: list[dict]) -> None:
    """
    Render a horizontal row of metric cards.

    Each dict in *metrics* should have:
        label  : str
        value  : str | int | float
        delta  : str | None   (optional)
        help   : str | None   (optional tooltip)
    """
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            st.metric(
                label=m.get("label", ""),
                value=m.get("value", "—"),
                delta=m.get("delta"),
                help=m.get("help"),
            )


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────────────────────────────────────

def render_sidebar_filters(options: dict) -> dict:
    """
    Draw the global sidebar filter panel and return selected values.

    *options* is the dict returned by db.load_filter_options().
    Returns a dict with keys: roles, role_groups, cities, work_modes, exp_levels.
    Each value is a list (empty → no filter applied).
    """
    with st.sidebar:
        
        st.title("📊 Filters")
        st.caption("Across all pages")
        st.divider()

        roles = st.multiselect(
            "🔍 Role / Title",
            options=options.get("roles", []),
            placeholder="All roles",
        )
        role_groups = st.multiselect(
            "📂 Role Group",
            options=options.get("role_groups", []),
            placeholder="All groups",
        )
        cities = st.multiselect(
            "🏙️ City",
            options=options.get("cities", []),
            placeholder="All cities",
        )
        exp_levels = st.multiselect(
            "🎓 Experience Level",
            options=options.get("exp_levels", []),
            placeholder="All levels",
        )

        st.divider()
        st.caption("Data refreshes every 5 min · SQLite")

    return dict(
        roles=roles,
        role_groups=role_groups,
        cities=cities,
        exp_levels=exp_levels,
    )


# ─────────────────────────────────────────────────────────────────────────────
# DOWNLOAD HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def df_download_button(df: pd.DataFrame, filename: str = "data.csv", label: str = "⬇️ Download CSV") -> None:
    """Render a CSV download button for *df*."""
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label=label, data=csv, file_name=filename, mime="text/csv")

# ─────────────────────────────────────────────────────────────────────────────
# CHART FACTORY FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def _base_layout(fig, title: str = "", height: int = CHART_HEIGHT) -> go.Figure:
    """Apply consistent styling to any Plotly figure."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        template=CHART_TEMPLATE,
        height=height,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig

def horizontal_bar(
    df: pd.DataFrame,
    value_col: str,
    label_col: str,
    title: str = "",
    top_n: int = TOP_N_DEFAULT,
    height: int = CHART_HEIGHT,
    color_col: str | None = None,
) -> go.Figure:
    """Convenience wrapper for horizontal bars with multi-color support."""
    df = df.nlargest(top_n, value_col).copy()
    color_seq = COLOR_SEQUENCE if color_col else [PRIMARY_COLOR]
    fig = px.bar(
        df, x=value_col, y=label_col,
        orientation="h",
        color=color_col if color_col else None,
        color_discrete_sequence=color_seq,
        text_auto=True,
    )
    fig.update_yaxes(autorange="reversed")
    return _base_layout(fig, title, height)


def pie_chart(
    df: pd.DataFrame,
    names: str,
    values: str,
    title: str = "",
    height: int = CHART_HEIGHT,
    hole: float = 0.4,
) -> go.Figure:
    """Donut / pie chart."""
    fig = px.pie(
        df, names=names, values=values,
        hole=hole,
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _base_layout(fig, title, height)

# ─────────────────────────────────────────────────────────────────────────────
# DATAFRAME DISPLAY HELPER
# ─────────────────────────────────────────────────────────────────────────────

def show_table(
    df: pd.DataFrame,
    title: str = "",
    download: bool = True,
    filename: str = "table.csv",
    max_rows: int = 200,
) -> None:
    """Render a section header + dataframe + optional download button."""
    if title:
        st.subheader(title)
    st.dataframe(df.head(max_rows), use_container_width=True)
    if download:
        df_download_button(df, filename=filename)


# ─────────────────────────────────────────────────────────────────────────────
# NUMBER FORMATTERS
# ─────────────────────────────────────────────────────────────────────────────

def fmt_inr(value: float) -> str:
    """Format a number as Indian Rupee LPA string."""
    if pd.isna(value):
        return "N/A"
    return f"₹{value:,.1f} LPA"


def fmt_int(value: float) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{int(value):,}"


def safe_avg(series: pd.Series) -> float:
    """Return mean ignoring NaN, or 0."""
    return series.dropna().mean() if not series.dropna().empty else 0.0