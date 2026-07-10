# =============================================================================
# Home.py — Landing page: KPIs, top cities, top roles, work-mode breakdown
# Run with: streamlit run dashboard/Home.py
#
# REFACTOR CHANGES vs previous version:
#   OLD → Loaded full table with load_all_jobs(), then used Pandas
#         .nunique(), .value_counts(), and .mean() for every KPI and chart.
#   NEW → Calls SQL analytics functions from db.py:
#         get_dashboard_kpis()       → all six KPI scalars in one SQL query
#         get_top_hiring_cities()    → GROUP BY city ORDER BY COUNT DESC
#         get_top_hiring_companies() → GROUP BY company ORDER BY COUNT DESC
#         get_role_distribution()    → GROUP BY role_searched
#         get_role_group_distribution() → GROUP BY role_group
#   Pandas is only used for post-fetch formatting (no groupby/agg).
#   load_all_jobs() is NOT called on this page at all.
# =============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import plotly.express as px

from config import APP_TITLE, APP_ICON, APP_LAYOUT, SIDEBAR_STATE
from db import (
    load_filter_options, apply_filters, load_all_jobs,
    get_dashboard_kpis,
    get_top_hiring_cities,
    get_top_hiring_companies,
    get_role_distribution,
    get_role_group_distribution,
)
from utils import (
    page_header, kpi_row, render_sidebar_filters,
    horizontal_bar, pie_chart,
    fmt_inr, fmt_int, df_download_button, _base_layout,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=f"Home · {APP_TITLE}",
    page_icon=APP_ICON,
    layout=APP_LAYOUT,
    initial_sidebar_state=SIDEBAR_STATE,
)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR FILTERS
# render_sidebar_filters() draws the widgets and returns the selections.
# We convert lists → tuples so they are hashable for @st.cache_data.
# ─────────────────────────────────────────────────────────────────────────────
options = load_filter_options()
filters = render_sidebar_filters(options)

# Unpack into named variables for clarity
f_roles       = tuple(filters["roles"])
f_role_groups = tuple(filters["role_groups"])
f_cities      = tuple(filters["cities"])
f_exp_levels  = tuple(filters["exp_levels"])

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────

df_raw = load_all_jobs()

page_header(
    f"{APP_ICON} {APP_TITLE} Dashboard",
    "Real-time job market intelligence scraped from Naukri.com · Use sidebar filters to drill down",
)
if "scraped_date" in df_raw.columns:

    latest_scrape = df_raw["scraped_date"].max()

    st.info(
        f"📅 Dataset Last Updated: {latest_scrape}"
    )
# ─────────────────────────────────────────────────────────────────────────────
# KPI CARDS — powered entirely by SQL (get_dashboard_kpis)
#
# CHANGE: Previously computed with:
#   total_jobs   = len(df)
#   total_cos    = df["company"].nunique()
#   avg_salary   = df["salary_avg"].mean()   ← Pandas on full column
#
# Now a single SQL query returns all six values:
#   SELECT COUNT(*), COUNT(DISTINCT company), COUNT(DISTINCT city),
#          COUNT(DISTINCT role_searched), ROUND(AVG(salary_avg),2),
#          ROUND(AVG(company_rating),2)
#   FROM jobs_standardized [WHERE …]
# ─────────────────────────────────────────────────────────────────────────────
kpis = get_dashboard_kpis(
    roles=f_roles, role_groups=f_role_groups,
    cities=f_cities, exp_levels=f_exp_levels,
)

kpi_row([
    {"label": "📋 Total Jobs",
     "value": fmt_int(kpis.get("total_jobs", 0)),
     "help": "Job listings after filters"},
    {"label": "🏢 Companies",
     "value": fmt_int(kpis.get("total_companies", 0)),
     "help": "Unique hiring companies"},
    {"label": "🏙️ Cities",
     "value": fmt_int(kpis.get("total_cities", 0)),
     "help": "Unique hiring cities"},
    {"label": "🎯 Roles",
     "value": fmt_int(kpis.get("total_roles", 0)),
     "help": "Unique searched roles"},
    {"label": "💰 Avg Salary",
     "value": fmt_inr(kpis.get("avg_salary") or 0),
     "help": "Average midpoint salary (LPA)"},
    {"label": "⭐ Avg Rating",
     "value": f"{kpis['avg_rating']:.2f}" if kpis.get("avg_rating") else "N/A",
     "help": "Average company rating"},
])

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# TOP HIRING CITIES — powered by get_top_hiring_cities()
#
# CHANGE: Previously:
#   city_counts = df["standardized_city"].value_counts().reset_index()
#   ← Pandas loads every city string, sorts in Python
#
# Now:
#   SELECT standardized_city AS City, COUNT(*) AS Jobs
#   FROM jobs_standardized [WHERE …]
#   GROUP BY standardized_city ORDER BY Jobs DESC LIMIT 15
# ─────────────────────────────────────────────────────────────────────────────
city_counts = get_top_hiring_cities(
    roles=f_roles, role_groups=f_role_groups,
    cities=f_cities, exp_levels=f_exp_levels,
    limit=12,
)

col1 = st.container()
with col1:
    st.subheader("🏙️ Top Hiring Cities")
    if not city_counts.empty:
        fig_cities = horizontal_bar(
            city_counts, value_col="Jobs", label_col="City",
            title="Top Hiring Cities", top_n=12, height=420,
        )
        st.plotly_chart(fig_cities, use_container_width=True)
        df_download_button(city_counts, "top_cities.csv", "⬇️ Download Cities Data")
    else:
        st.info("City data not available.")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# TOP HIRING ROLES — powered by get_role_distribution()
#
# CHANGE: Previously:
#   role_counts = df["role_searched"].value_counts().reset_index()
#
# Now:
#   SELECT role_searched AS Role, COUNT(*) AS Jobs
#   FROM jobs_standardized [WHERE …]
#   GROUP BY role_searched ORDER BY Jobs DESC LIMIT 20
# ─────────────────────────────────────────────────────────────────────────────
role_counts = get_role_distribution(
    roles=f_roles, role_groups=f_role_groups,
    cities=f_cities, exp_levels=f_exp_levels,
    limit=20,
)

st.subheader("🎯 Top Hiring Roles")
if not role_counts.empty:
    fig_roles = px.bar(
        role_counts, x="Jobs", y="Role", orientation="h",
        color="Jobs", color_continuous_scale="Viridis",
        text_auto=True,
    )
    fig_roles.update_yaxes(autorange="reversed")
    fig_roles = _base_layout(fig_roles, "Top 20 Hiring Roles by Job Count", height=520)
    st.plotly_chart(fig_roles, use_container_width=True)
    df_download_button(role_counts, "top_roles.csv", "⬇️ Download Roles Data")
else:
    st.info("Role data not available.")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# ROLE GROUP PIE  |  TOP COMPANIES
# get_role_group_distribution() replaces df["role_group"].value_counts()
# get_top_hiring_companies()    replaces df["company"].value_counts()
# ─────────────────────────────────────────────────────────────────────────────
rg_counts  = get_role_group_distribution(
    roles=f_roles, role_groups=f_role_groups,
    cities=f_cities, exp_levels=f_exp_levels,
)
co_counts  = get_top_hiring_companies(
    roles=f_roles, role_groups=f_role_groups,
    cities=f_cities, exp_levels=f_exp_levels,
    limit=15,
)

col3, col4 = st.columns(2)

with col3:
    st.subheader("📂 Role Group Distribution")
    if not rg_counts.empty:
        fig_rg = pie_chart(
            rg_counts, names="Role Group", values="Jobs",
            title="Jobs by Role Group", height=380, hole=0.35,
        )
        st.plotly_chart(fig_rg, use_container_width=True)
    else:
        st.info("Role group data not available.")

with col4:
    st.subheader("🏢 Top Hiring Companies")
    if not co_counts.empty:
        fig_company = px.bar(
            co_counts, x="Jobs", y="Company",
            orientation="h", text_auto=True,
        )
        fig_company.update_yaxes(autorange="reversed")
        fig_company = _base_layout(fig_company, "Top 15 Hiring Companies", height=380)
        st.plotly_chart(fig_company, use_container_width=True)
    else:
        st.info("Company data not available.")

# ─────────────────────────────────────────────────────────────────────────────
# JOB EXPLORER EXPANDER
# This still needs the raw rows (for job_url links, skill strings, etc.)
# so load_all_jobs() + apply_filters() are kept here only.
# ─────────────────────────────────────────────────────────────────────────────
with st.expander("🔍 Job Explorer", expanded=False):
    df     = apply_filters(df_raw, **filters)

    display_cols = [
        "title", "company", "role_group", "standardized_city",
        "exp_min", "exp_max", "salary_avg", "posted_date_actual",
        "skills_standardized", "company_rating", "company_reviews",
    ]
    # Only keep columns that actually exist in this table
    display_cols = [c for c in display_cols if c in df.columns]

    rename_map = {
        "title":              "Job Title",
        "company":            "Company",
        "role_group":         "Role Group",
        "standardized_city":  "City",
        "salary_avg":         "Salary (LPA)",
        "posted_date_actual": "Posted Date",
        "skills_standardized":"Skills",
        "company_rating":     "Rating",
        "company_reviews":    "Reviews",
    }
    df_display = df[display_cols].rename(columns=rename_map)

    if "exp_min" in df.columns and "exp_max" in df.columns:
        df_display["Experience"] = (
            df["exp_min"].fillna(0).astype(int).astype(str)
            + " - "
            + df["exp_max"].fillna(0).astype(int).astype(str)
            + " Years"
        )
        df_display.drop(columns=["exp_min", "exp_max"], errors="ignore", inplace=True)

    if "job_url" in df.columns:
        df_display["Apply"] = df["job_url"]

    col_cfg = {}
    if "Apply" in df_display.columns:
        col_cfg["Apply"] = st.column_config.LinkColumn("Apply Job", display_text="Open Job")
    
    df_display.insert(0, "S.No", range(1, len(df_display) + 1))
    
    st.success(
        f"Found {len(df_display):,} job listings after applying filters"
    )

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Apply": st.column_config.LinkColumn(
            "Apply Job",
            display_text="Open Job"
            )
        }
    )
        
    df_download_button(df_display, "filtered_jobs.csv", "⬇️ Download Filtered Jobs")

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.caption("📌 Data sourced from Naukri.com · Built with Streamlit + Plotly + SQLite · Mohd Iqbal")