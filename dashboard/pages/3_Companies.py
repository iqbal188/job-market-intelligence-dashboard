
# Company intelligence

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
import plotly.express as px

from config import APP_TITLE, APP_LAYOUT, SIDEBAR_STATE, COLOR_SEQUENCE
from db import (
    load_filter_options,
    get_dashboard_kpis,
    get_top_hiring_companies,
    get_highest_rated_companies,
    get_most_reviewed_companies,
    get_company_salary_comparison,
    get_company_role_group_matrix,
)
from utils import (
    page_header, render_sidebar_filters, df_download_button, fmt_inr,
    _base_layout, kpi_row, fmt_int,
)

st.set_page_config(
    page_title=f"Companies · {APP_TITLE}",
    page_icon="🏢",
    layout=APP_LAYOUT,
    initial_sidebar_state=SIDEBAR_STATE,
)

# SIDEBAR & FILTER TUPLES

options = load_filter_options()
filters = render_sidebar_filters(options)

f_roles       = tuple(filters["roles"])
f_role_groups = tuple(filters["role_groups"])
f_cities      = tuple(filters["cities"])
f_exp_levels  = tuple(filters["exp_levels"])

page_header("🏢 Company Intelligence", "")

# KPI ROW

kpis = get_dashboard_kpis(
    roles=f_roles, role_groups=f_role_groups,
    cities=f_cities, exp_levels=f_exp_levels,
)

total_companies = int(kpis.get("total_companies", 0))
total_jobs      = int(kpis.get("total_jobs", 0))
avg_salary      = kpis.get("avg_salary") or 0
avg_rating      = kpis.get("avg_rating")
avg_per_co      = total_jobs / max(total_companies, 1)

# Update page header subtitle now that we have the count
st.caption(
    f"Profiling **{total_companies:,}** companies across **{total_jobs:,}** filtered listings"
)

kpi_row([
    {"label": "🏢 Total Companies",   "value": fmt_int(total_companies)},
    {"label": "⭐ Avg Rating",        "value": f"{avg_rating:.2f}" if avg_rating else "N/A"},
    {"label": "💰 Avg Salary",        "value": fmt_inr(avg_salary)},
    {"label": "📋 Avg Listings/Co",   "value": f"{avg_per_co:.1f}"},
])
st.divider()

# TABS

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 Top Hiring",
    "⭐ Highest Rated",
    "💬 Most Reviewed",
    "💰 Salary Comparison",
    "📂 Hiring by Role Group",
])

# TAB 1 — Top Hiring Companies

with tab1:
    st.subheader("🏆 Top Hiring Companies")
    top_n_hire = st.slider("Top N companies", 5, 30, 15, key="hire_n")

    hire_df = get_top_hiring_companies(
        roles=f_roles, role_groups=f_role_groups,
        cities=f_cities, exp_levels=f_exp_levels,
        limit=top_n_hire,
    )

    if not hire_df.empty:
        fig1 = px.bar(
            hire_df, x="Jobs", y="Company", orientation="h",
            color="Jobs", color_continuous_scale="Blues",
            text_auto=True,
        )
        fig1.update_yaxes(autorange="reversed")
        fig1 = _base_layout(
            fig1, f"Top {top_n_hire} Companies by Job Listings",
            height=max(400, top_n_hire * 30),
        )
        st.plotly_chart(fig1, use_container_width=True)
        df_download_button(hire_df, "top_hiring_companies.csv")

        # Treemap
        st.subheader("🗺️ Hiring Distribution Treemap")
        tm_df = get_top_hiring_companies(
            roles=f_roles, role_groups=f_role_groups,
            cities=f_cities, exp_levels=f_exp_levels,
            limit=40,
        )
        fig_tm = px.treemap(
            tm_df, path=["Company"], values="Jobs",
            color="Jobs", color_continuous_scale="Teal",
        )
        fig_tm = _base_layout(fig_tm, "Hiring Share — Top 40 Companies", height=420)
        st.plotly_chart(fig_tm, use_container_width=True)
    else:
        st.info("No company hiring data available.")

# TAB 2 — Highest Rated Companies

with tab2:
    st.subheader("⭐ Highest Rated Companies")
    min_listings = st.slider("Minimum job listings", 1, 20, 3, key="rating_min")

    rated_df = get_highest_rated_companies(
        roles=f_roles, role_groups=f_role_groups,
        cities=f_cities, exp_levels=f_exp_levels,
        min_listings=min_listings, limit=20,
    )

    if rated_df.empty:
        st.info("Company rating data not available.")
    else:
        fig2 = px.bar(
            rated_df, x="Avg Rating", y="Company", orientation="h",
            color="Avg Rating", color_continuous_scale="RdYlGn",
            text="Avg Rating",
            hover_data=["Job Listings"],
            range_color=[1, 5],
        )
        fig2.update_traces(texttemplate="%{text:.2f} ⭐", textposition="outside")
        fig2.update_yaxes(autorange="reversed")
        fig2 = _base_layout(
            fig2, f"Top 20 Rated Companies (min {min_listings} listings)", height=500
        )
        st.plotly_chart(fig2, use_container_width=True)

# TAB 3 — Most Reviewed Companies

with tab3:
    st.subheader("💬 Most Reviewed Companies")

    rev_df = get_most_reviewed_companies(
        roles=f_roles, role_groups=f_role_groups,
        cities=f_cities, exp_levels=f_exp_levels,
        limit=20,
    )

    if rev_df.empty or rev_df["Reviews"].isna().all():
        st.info("Review data not available.")
    else:
        fig3 = px.bar(
            rev_df, x="Reviews", y="Company", orientation="h",
            color="Avg Rating" if "Avg Rating" in rev_df.columns else None,
            color_continuous_scale="RdYlGn",
            text_auto=True,
            hover_data=["Job Listings"],
            range_color=[1, 5],
        )
        fig3.update_yaxes(autorange="reversed")
        fig3 = _base_layout(
            fig3, "Top 20 Most Reviewed Companies (colored by rating)", height=500
        )
        st.plotly_chart(fig3, use_container_width=True)

# TAB 4 — Company Salary Comparison

with tab4:
    st.subheader("💰 Company Salary Comparison")

    sal_df = get_company_salary_comparison(
        roles=f_roles, role_groups=f_role_groups,
        cities=f_cities, exp_levels=f_exp_levels,
        limit=25,
    )

    if sal_df.empty:
        st.info("Salary data not available for comparison.")
    else:
        fig4 = px.bar(
            sal_df, x="Avg Salary (LPA)", y="Company", orientation="h",
            color="Avg Salary (LPA)", color_continuous_scale="Purples",
            text="Avg Salary (LPA)",
            hover_data=["Job Listings", "Avg Rating"],
        )
        fig4.update_traces(texttemplate="₹%{text:.1f}L", textposition="outside")
        fig4.update_yaxes(autorange="reversed")
        fig4 = _base_layout(
            fig4, "Top 25 Companies by Average Salary Offered (LPA)", height=560
        )
        st.plotly_chart(fig4, use_container_width=True)

# TAB 5 — Hiring by Role Group

with tab5:
    st.subheader("📂 Company Hiring Distribution by Role Group")

    heat_df = get_company_role_group_matrix(
        roles=f_roles, role_groups=f_role_groups,
        cities=f_cities, exp_levels=f_exp_levels,
        top_companies=12,
    )

    if heat_df.empty:
        st.info("Role group or company columns not found.")
    else:
        # Pandas pivot is legitimate here — it reshapes SQL output for imshow
        pivot_rg = heat_df.pivot(
            index="company", columns="role_group", values="Listings"
        ).fillna(0)

        fig5 = px.imshow(
            pivot_rg,
            color_continuous_scale="Blues",
            aspect="auto", text_auto=True,
            labels={"color": "Listings"},
        )
        fig5 = _base_layout(
            fig5, "Hiring Distribution: Top 12 Companies × Role Groups", height=480
        )
        st.plotly_chart(fig5, use_container_width=True)

        # Stacked bar from the same long-format SQL result
        fig5b = px.bar(
            heat_df, x="Listings", y="company", color="role_group",
            orientation="h", barmode="stack",
            color_discrete_sequence=COLOR_SEQUENCE,
            text_auto=True,
        )
        fig5b.update_yaxes(autorange="reversed")
        fig5b = _base_layout(
            fig5b, "Stacked Hiring by Role Group — Top 12 Companies", height=480
        )
        st.plotly_chart(fig5b, use_container_width=True)

st.divider()
st.caption("📌 Data sourced from Naukri.com · Job Market Intelligence by Mohd Iqbal")