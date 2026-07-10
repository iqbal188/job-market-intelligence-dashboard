
# Salary intelligence

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
import plotly.express as px

from config import APP_TITLE, APP_LAYOUT, SIDEBAR_STATE, COLOR_SEQUENCE, EXP_LEVEL_ORDER
from db import (
    load_all_jobs, load_filter_options, apply_filters,
    get_salary_by_role,
    get_top_paying_companies,
    get_top_paying_cities,
    get_salary_by_experience,
    get_dashboard_kpis,
)
from utils import (
    page_header, render_sidebar_filters, show_table,
    fmt_inr, _base_layout, kpi_row, fmt_int,
)

st.set_page_config(
    page_title=f"Salary · {APP_TITLE}",
    page_icon="💰",
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

# RAW DATA — loaded ONCE, used ONLY for box plot and scatter (need rows)

df_raw = load_all_jobs()
df     = apply_filters(df_raw, **filters)
df_sal = (
    df[df["salary_avg"].notna() & (df["salary_avg"] > 0)].copy()
    if "salary_avg" in df.columns else pd.DataFrame()
)

coverage = (len(df_sal) / len(df) * 100) if len(df) else 0

page_header(
    "💰 Salary Intelligence",
    f"{len(df_sal):,} listings with salary data ({coverage:.1f}% coverage) · All figures in LPA",
)

if not df_sal.empty:
    kpis = get_dashboard_kpis(
        roles=f_roles, role_groups=f_role_groups,
        cities=f_cities, exp_levels=f_exp_levels,
    )

    kpi_row([
        {"label": "💰 Avg Salary",
         "value": fmt_inr(kpis.get("avg_salary") or 0),
         "help": "SQL: ROUND(AVG(salary_avg),2)"},
        {"label": "📈 Max Salary",
         "value": fmt_inr(df_sal["salary_max"].max()) if "salary_max" in df_sal.columns else "N/A"},
        {"label": "📊 Median Salary",
         "value": fmt_inr(df_sal["salary_avg"].median()),
         "help": "Median less affected by outliers"},
        {"label": "📋 Salary Records",
         "value": fmt_int(len(df_sal)),
         "help": "Naukri shows salary for ~30–40% of listings"},
    ])
    st.divider()
else:
    st.warning("⚠️ No salary data found for the current filter selection.")

# TABS

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 By Role",
    "🎓 By Experience",
    "🏙️ Top Paying Cities",
    "🏢 Top Paying Companies",
])

# TAB 1 — Salary by Role

with tab1:
    st.subheader("📊 Salary Distribution by Role")

    if df_sal.empty or "role_searched" not in df_sal.columns:
        st.info("Insufficient salary data for role breakdown.")
    else:
        # ── Box plot: needs individual rows → Pandas df_sal (intentional) ────
        fig_box = px.box(
            df_sal,
            x="salary_avg", y="role_searched",
            orientation="h",
            color="role_searched",
            color_discrete_sequence=COLOR_SEQUENCE,
            points="outliers",
            labels={"salary_avg": "Salary (LPA)", "role_searched": "Role"},
        )
        fig_box.update_yaxes(autorange="reversed")
        fig_box = _base_layout(fig_box, "Salary Range Distribution by Role", height=520)
        st.plotly_chart(fig_box, use_container_width=True)

        # Average salary bar
        avg_sal_role = get_salary_by_role(
            roles=f_roles, role_groups=f_role_groups,
            cities=f_cities, exp_levels=f_exp_levels,
        )

        if not avg_sal_role.empty:
            fig_avg = px.bar(
                avg_sal_role,
                x="Average Salary (LPA)", y="Role",
                orientation="h",
                color="Average Salary (LPA)", color_continuous_scale="Blues",
                text="Average Salary (LPA)",
                hover_data=["Max Salary (LPA)", "Listings"],
            )
            fig_avg.update_traces(texttemplate="%{text:.1f} LPA", textposition="outside")
            fig_avg.update_yaxes(autorange="reversed")
            fig_avg = _base_layout(fig_avg, "Average Salary by Role (LPA)", height=520)
            st.plotly_chart(fig_avg, use_container_width=True)

            # Reset index to start from 1 for display
            display_df = avg_sal_role.copy()
            display_df.index = range(1, len(display_df) + 1)
            show_table(display_df, "Salary Stats by Role (LPA)", download=False)

# TAB 2 — Salary by Experience

with tab2:
    st.subheader("🎓 Salary by Experience Level")

    if df_sal.empty:
        st.info("No salary data available.")
    else:
        col1, col2 = st.columns(2)

        # Box plot
        with col1:
            if "experience_level" in df_sal.columns:
                order = [e for e in EXP_LEVEL_ORDER if e in df_sal["experience_level"].unique()]
                fig_exp = px.box(
                    df_sal, x="experience_level", y="salary_avg",
                    color="experience_level",
                    color_discrete_sequence=COLOR_SEQUENCE,
                    category_orders={"experience_level": order},
                    points="outliers",
                    labels={"experience_level": "Experience Level", "salary_avg": "Salary (LPA)"},
                )
                fig_exp = _base_layout(fig_exp, "Salary by Experience Level", height=420)
                st.plotly_chart(fig_exp, use_container_width=True)

        # Scatter
        with col2:
            if "exp_avg" in df_sal.columns:
                scatter_df = df_sal[df_sal["exp_avg"].notna()].copy()
                fig_sc = px.scatter(
                    scatter_df, x="exp_avg", y="salary_avg",
                    color="experience_level" if "experience_level" in scatter_df.columns else None,
                    color_discrete_sequence=COLOR_SEQUENCE,
                    labels={"exp_avg": "Avg Experience (Yrs)", "salary_avg": "Avg Salary (LPA)"},
                    opacity=0.6,
                    hover_data=["role_searched"] if "role_searched" in scatter_df.columns else [],
                )
                fig_sc = _base_layout(fig_sc, "Experience Years vs Salary", height=420)
                st.plotly_chart(fig_sc, use_container_width=True)
            else:
                st.info("exp_avg column not found for scatter plot.")

        # Summary stats table
        exp_stats = get_salary_by_experience(
            roles=f_roles, role_groups=f_role_groups,
            cities=f_cities, exp_levels=f_exp_levels,
        )
        if not exp_stats.empty:
            # Reorder rows to match EXP_LEVEL_ORDER
            exp_stats["_order"] = exp_stats["Level"].map(
                {e: i for i, e in enumerate(EXP_LEVEL_ORDER)}
            ).fillna(99)
            exp_stats = exp_stats.sort_values("_order").drop("_order", axis=1)
            show_table(exp_stats, download=True, filename="salary_by_experience.csv")

# TAB 3 — Top Paying Cities

with tab3:
    st.subheader("🏙️ Top Paying Cities")

    city_sal = get_top_paying_cities(
        roles=f_roles, role_groups=f_role_groups,
        cities=f_cities, exp_levels=f_exp_levels,
        min_listings=3, limit=20,
    )

    if city_sal.empty:
        st.info("City salary data not available.")
    else:
        fig_city = px.bar(
            city_sal, x="Avg (LPA)", y="City", orientation="h",
            color="Avg (LPA)", color_continuous_scale="Teal",
            text="Avg (LPA)", hover_data=["Listings"],
        )
        fig_city.update_traces(texttemplate="%{text:.1f} LPA", textposition="outside")
        fig_city.update_yaxes(autorange="reversed")
        fig_city = _base_layout(
            fig_city, "Average Salary by City (Top 20, min 3 listings)", height=480
        )
        st.plotly_chart(fig_city, use_container_width=True)
        show_table(city_sal, download=False, filename="salary_by_city.csv")

# TAB 4 — Top Paying Companies

with tab4:
    st.subheader("🏢 Top Paying Companies")

    co_sal = get_top_paying_companies(
        roles=f_roles, role_groups=f_role_groups,
        cities=f_cities, exp_levels=f_exp_levels,
        min_listings=2, limit=20,
    )

    if co_sal.empty:
        st.info("Company salary data not available.")
    else:
        fig_co = px.bar(
            co_sal, x="Avg (LPA)", y="Company", orientation="h",
            color="Avg (LPA)", color_continuous_scale="Purples",
            text="Avg (LPA)", hover_data=["Listings"],
        )
        fig_co.update_traces(texttemplate="%{text:.1f} LPA", textposition="outside")
        fig_co.update_yaxes(autorange="reversed")
        fig_co = _base_layout(
            fig_co, "Top 20 Highest Paying Companies (avg, min 2 listings)", height=500
        )
        st.plotly_chart(fig_co, use_container_width=True)
        show_table(co_sal, download=False, filename="salary_by_company.csv")

st.caption("📌 Salary data based on disclosed listings only · ~30-40% of Naukri listings show salary")