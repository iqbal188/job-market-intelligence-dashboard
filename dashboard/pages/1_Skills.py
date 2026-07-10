
# Skills intelligence

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
import plotly.express as px

from config import APP_TITLE, APP_ICON, APP_LAYOUT, SIDEBAR_STATE
from db import load_all_jobs, load_filter_options, apply_filters
from utils import (
    page_header, render_sidebar_filters, show_table, _base_layout
)

st.set_page_config(
    page_title=f"Skills · {APP_TITLE}",
    page_icon="🛠️",
    layout=APP_LAYOUT,
    initial_sidebar_state=SIDEBAR_STATE,
)

# DATA LOAD

df_raw  = load_all_jobs()
options = load_filter_options()
filters = render_sidebar_filters(options)
df      = apply_filters(df_raw, **filters)

page_header("🛠️ Skills Intelligence", f"Analysing skill demand across {len(df):,} filtered job listings")


# ── Helper: explode skills column (intentional Pandas operation) ──────────────
def explode_skills(data: pd.DataFrame, col: str = "skills_standardized") -> pd.Series:
    """
    Split comma-separated skill strings into individual skill tokens.

    This is why we keep Pandas on this page: SQLite cannot split strings
    into rows without a custom extension.  str.split().explode() is the
    correct Pandas idiom for this transformation.
    """
    if col not in data.columns:
        col = "skills"
    if col not in data.columns:
        return pd.Series(dtype=str)
    return (
        data[col]
        .dropna()
        .str.split(",")
        .explode()
        .str.strip()
        .str.lower()
        .replace("", pd.NA)
        .dropna()
    )

# TABS

tab1, tab2, tab3 = st.tabs([
    "🔥 Top Skills",
    "🚀 AI & GenAI Skills",
    "📊 Skill Frequency Table",
])

# TAB 1 — Top Skills Overall

with tab1:
    st.subheader("🔥 Most In-Demand Skills")

    all_skills = explode_skills(df)
    if all_skills.empty:
        st.warning("No skill data found. Check that the 'skills' or 'skills_standardized' column exists.")
    else:
        # Pandas value_counts() is correct here — we already exploded the strings
        skill_counts = (
            all_skills.value_counts()
            .reset_index()
            .rename(columns={"index": "Skill", 0: "Count", "skills_standardized": "Skill", "count": "Count"})
            .head(30)
        )
        skill_counts.columns = ["Skill", "Count"] if skill_counts.shape[1] == 2 else skill_counts.columns

        col1, col2 = st.columns([3, 1])
        with col1:
            top_n = st.slider("Show top N skills", min_value=5, max_value=30, value=20, key="top_skills_n")

        plot_df = skill_counts.head(top_n)
        fig = px.bar(
            plot_df, x="Count", y="Skill", orientation="h",
            color="Count", color_continuous_scale="Viridis",
            text_auto=True,
        )
        fig.update_yaxes(autorange="reversed")
        fig = _base_layout(fig, f"Top {top_n} Most Required Skills", height=max(400, top_n * 28))
        st.plotly_chart(fig, use_container_width=True)

        top_skill       = plot_df.iloc[0]["Skill"]
        top_skill_count = plot_df.iloc[0]["Count"]
        pct = top_skill_count / len(df) * 100 if len(df) else 0
        st.info(f"**{top_skill.title()}** appears in **{pct:.1f}%** of all filtered job listings.")

# TAB 2 — AI & GenAI Skills

with tab2:
    st.subheader("🚀 AI & GenAI Skills Demand")

    ai_keywords = [
        "AI", "Machine Learning", "LLM", "RAG", "LangChain",
        "TensorFlow", "PyTorch", "Deep Learning", "NLP", "Generative AI",
    ]

    skills     = explode_skills(df)
    ai_counts  = []
    for skill in ai_keywords:
        count = (skills.str.lower() == skill.lower()).sum()
        ai_counts.append({"Skill": skill, "Jobs": count})

    ai_df = pd.DataFrame(ai_counts)

    fig = px.bar(
        ai_df.sort_values("Jobs", ascending=True),
        x="Jobs", y="Skill", orientation="h",
        text_auto=True,
    )
    fig = _base_layout(fig, "AI & GenAI Skill Demand", height=400)
    st.plotly_chart(fig, use_container_width=True)

# TAB 3 — Skill Frequency Table

with tab3:
    st.subheader("📊 Skill Frequency Table")

    # Dynamically load available roles from filtered dataset
    ROLE_OPTIONS = ["All Roles"] + sorted(
        df["role_searched"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_role = st.selectbox(
        "Select Role",
        ROLE_OPTIONS
    )
    if selected_role != "All Roles":
        filtered_df = df[df["role_searched"] == selected_role]
    else:
        filtered_df = df

    st.info(
        f"📊 {len(filtered_df):,} jobs found for {selected_role}"
    )

    all_skills3 = explode_skills(filtered_df)
    if all_skills3.empty:
        st.warning("No skill data found.")
    else:
        freq_df = (
            all_skills3.value_counts()
            .reset_index()
            .rename(columns={"index": "Skill", 0: "Job Count"})
        )
        freq_df.columns = ["Skill", "Job Count"]
        freq_df = freq_df[freq_df["Job Count"] >= 32]

        st.caption(
            f"Showing skills appearing in ≥32 job listings for: **{selected_role}**"
        )

        freq_df["% of Jobs"] = (freq_df["Job Count"] / len(filtered_df) * 100).round(2)
        freq_df["Rank"]      = range(1, len(freq_df) + 1)
        freq_df = freq_df[["Rank", "Skill", "Job Count", "% of Jobs"]]

        search_term = st.text_input("🔍 Search skill", placeholder="e.g. python")
        display_df  = (
            freq_df[freq_df["Skill"].str.contains(search_term, case=False)]
            if search_term else freq_df
        )
        show_table(display_df, download=True, filename="skill_frequency.csv", max_rows=300)