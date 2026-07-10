# SQLite connection + SQL analytics layer

import sqlite3
import pandas as pd
import streamlit as st
from config import DB_PATH

# SECTION 1 — CONNECTION & GENERIC RUNNER

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@st.cache_data(ttl=300, show_spinner=False)
def run_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    conn = get_connection()
    try:
        df = pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()
    return df

# SECTION 2 — TABLE INTROSPECTION

@st.cache_data(ttl=600, show_spinner=False)
def table_exists(table_name: str) -> bool:
    """Return True if *table_name* exists in jobs.db."""
    conn = get_connection()
    cur  = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    result = cur.fetchone()
    conn.close()
    return result is not None


def best_table() -> str:
    return "jobs_standardized" if table_exists("jobs_standardized") else "jobs_clean"


def _col_exists(col: str) -> bool:
    """Return True if *col* exists in the primary dashboard table."""
    tbl = best_table()
    df  = run_query(f"PRAGMA table_info({tbl})")
    return col in df["name"].values

# SECTION 3 — FILTER HELPERS

def _where_clause(
    roles:       list | None = None,
    role_groups: list | None = None,
    cities:      list | None = None,
    exp_levels:  list | None = None,
) -> tuple[str, tuple]:
    conditions: list[str] = []
    params:     list      = []

    if roles:
        placeholders = ",".join("?" * len(roles))
        conditions.append(f"role_searched IN ({placeholders})")
        params.extend(roles)

    if role_groups:
        placeholders = ",".join("?" * len(role_groups))
        conditions.append(f"role_group IN ({placeholders})")
        params.extend(role_groups)

    if cities:
        placeholders = ",".join("?" * len(cities))
        conditions.append(f"standardized_city IN ({placeholders})")
        params.extend(cities)

    if exp_levels:
        placeholders = ",".join("?" * len(exp_levels))
        conditions.append(f"experience_level IN ({placeholders})")
        params.extend(exp_levels)

    clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    return clause, tuple(params)


# Sidebar option loader (unchanged) 
@st.cache_data(ttl=300, show_spinner=False)
def load_filter_options() -> dict:

    tbl = best_table()

    def distinct(col: str) -> list:
        df = run_query(
            f"SELECT DISTINCT {col} FROM {tbl} "
            f"WHERE {col} IS NOT NULL AND {col} != '' ORDER BY {col}"
        )
        return df[col].dropna().tolist()

    city_col = "standardized_city" if _col_exists("standardized_city") else "primary_city"
    cities_df = run_query(f"""
        SELECT {city_col}
        FROM   {tbl}
        WHERE  {city_col} IS NOT NULL AND {city_col} != ''
        GROUP  BY {city_col}
        HAVING COUNT(*) >= 15
        ORDER  BY {city_col}
    """)

    return {
        "roles":       distinct("role_searched"),
        "role_groups": distinct("role_group") if _col_exists("role_group") else [],
        "cities":      cities_df[city_col].tolist(),
        "exp_levels":  distinct("experience_level"),
    }


# ── Pandas in-memory filter (kept for Skill page which needs raw rows) ────────
def apply_filters(
    df: pd.DataFrame,
    roles:       list,
    role_groups: list,
    cities:      list,
    exp_levels:  list,
) -> pd.DataFrame:
    """
    Filter a raw DataFrame in Python.
    Used ONLY by the Skills page, which needs individual rows to explode
    comma-separated skill strings — a task SQL cannot do cleanly in SQLite.
    All other pages call the SQL functions below instead.
    """
    city_col = "standardized_city" if "standardized_city" in df.columns else "primary_city"
    if roles:
        df = df[df["role_searched"].isin(roles)]
    if role_groups and "role_group" in df.columns:
        df = df[df["role_group"].isin(role_groups)]
    if cities and city_col in df.columns:
        df = df[df[city_col].isin(cities)]
    if exp_levels and "experience_level" in df.columns:
        df = df[df["experience_level"].isin(exp_levels)]
    return df


# ── Full table loader (kept for Skills page only) ─────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_all_jobs() -> pd.DataFrame:
    """
    Load every row from the primary table.
    Only the Skills page calls this — it needs raw rows to explode skills.
    All aggregation pages call the targeted SQL functions below.
    """
    tbl = best_table()
    return run_query(f"SELECT * FROM {tbl}")


# =============================================================================
# SECTION 4 — SQL ANALYTICS FUNCTIONS
# =============================================================================
# Each function:
#   1. Accepts the same filter kwargs that the sidebar returns
#   2. Calls _where_clause() to build a safe parameterised WHERE fragment
#   3. Runs a single SQL query that does ALL aggregation inside SQLite
#   4. Returns a clean, rename-ready DataFrame
#   5. Is cached independently so changing one filter invalidates only its cache
#
# Naming convention: get_<what>()   e.g. get_dashboard_kpis()
# =============================================================================

# ── 4A  KPI CARDS ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_dashboard_kpis(
    roles:       tuple = (),
    role_groups: tuple = (),
    cities:      tuple = (),
    exp_levels:  tuple = (),
) -> dict:
    """
    Return a single-row dict of all Home page KPI values.

    SQL computes COUNT, COUNT DISTINCT, AVG, and ROUND in one query —
    no Pandas groupby or mean() call needed.

    WHY SQL: Aggregating over 3,000+ rows to produce six scalar values
    is exactly what SQL optimisers are built for.  The query runs in
    < 5 ms; the Pandas equivalent requires loading the full table first.
    """
    tbl    = best_table()
    where, params = _where_clause(
        list(roles), list(role_groups), list(cities), list(exp_levels)
    )
    city_col = "standardized_city" if _col_exists("standardized_city") else "primary_city"

    sql = f"""
        SELECT
            COUNT(*)                                    AS total_jobs,
            COUNT(DISTINCT company)                     AS total_companies,
            COUNT(DISTINCT {city_col})                  AS total_cities,
            COUNT(DISTINCT role_searched)               AS total_roles,
            ROUND(AVG(salary_avg),  2)                  AS avg_salary,
            ROUND(AVG(company_rating), 2)               AS avg_rating,
            ROUND(
                SUM(CASE WHEN salary_avg IS NOT NULL
                         THEN 1 ELSE 0 END) * 100.0
                / COUNT(*), 1
            )                                           AS salary_coverage_pct
        FROM {tbl}
        {where}
    """
    row = run_query(sql, params)
    # Return as a plain dict so pages can access values by name
    return row.iloc[0].to_dict() if not row.empty else {}


# ── 4B  TOP HIRING CITIES ─────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_top_hiring_cities(
    roles:       tuple = (),
    role_groups: tuple = (),
    cities:      tuple = (),
    exp_levels:  tuple = (),
    limit:       int   = 15,
) -> pd.DataFrame:
    """
    Return (City, Jobs) sorted by job count descending.

    WHY SQL: GROUP BY + ORDER BY + LIMIT inside SQLite is one index scan.
    The Pandas equivalent (value_counts().head()) loads the full column
    into memory first, then sorts in Python.
    """
    tbl    = best_table()
    where, params = _where_clause(
        list(roles), list(role_groups), list(cities), list(exp_levels)
    )
    city_col = "standardized_city" if _col_exists("standardized_city") else "primary_city"

    sql = f"""
        SELECT
            {city_col}          AS City,
            COUNT(*)            AS Jobs
        FROM  {tbl}
        {where}
        GROUP BY {city_col}
        ORDER BY Jobs DESC
        LIMIT {limit}
    """
    return run_query(sql, params)


# ── 4C  TOP HIRING COMPANIES ──────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_top_hiring_companies(
    roles:       tuple = (),
    role_groups: tuple = (),
    cities:      tuple = (),
    exp_levels:  tuple = (),
    limit:       int   = 20,
) -> pd.DataFrame:
    """
    Return (Company, Jobs) sorted by listing count descending.

    WHY SQL: Same reasoning as cities — single GROUP BY is more efficient
    than loading all company strings into a Pandas Series.
    """
    tbl    = best_table()
    where, params = _where_clause(
        list(roles), list(role_groups), list(cities), list(exp_levels)
    )
    sql = f"""
        SELECT
            company             AS Company,
            COUNT(*)            AS Jobs
        FROM  {tbl}
        {where}
        GROUP BY company
        ORDER BY Jobs DESC
        LIMIT {limit}
    """
    return run_query(sql, params)


# ── 4D  ROLE DISTRIBUTION ─────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_role_distribution(
    roles:       tuple = (),
    role_groups: tuple = (),
    cities:      tuple = (),
    exp_levels:  tuple = (),
    limit:       int   = 20,
) -> pd.DataFrame:
    """Return (Role, Jobs) for the top-N searched roles."""
    tbl    = best_table()
    where, params = _where_clause(
        list(roles), list(role_groups), list(cities), list(exp_levels)
    )
    sql = f"""
        SELECT
            role_searched       AS Role,
            COUNT(*)            AS Jobs
        FROM  {tbl}
        {where}
        GROUP BY role_searched
        ORDER BY Jobs DESC
        LIMIT {limit}
    """
    return run_query(sql, params)


# ── 4E  ROLE GROUP DISTRIBUTION ───────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_role_group_distribution(
    roles:       tuple = (),
    role_groups: tuple = (),
    cities:      tuple = (),
    exp_levels:  tuple = (),
) -> pd.DataFrame:
    """Return (Role Group, Jobs) for pie / bar charts."""
    tbl    = best_table()
    where, params = _where_clause(
        list(roles), list(role_groups), list(cities), list(exp_levels)
    )
    sql = f"""
        SELECT
            role_group          AS "Role Group",
            COUNT(*)            AS Jobs
        FROM  {tbl}
        {where}
        GROUP BY role_group
        ORDER BY Jobs DESC
    """
    return run_query(sql, params)


# ── 4F  SALARY BY ROLE ────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_salary_by_role(
    roles:       tuple = (),
    role_groups: tuple = (),
    cities:      tuple = (),
    exp_levels:  tuple = (),
) -> pd.DataFrame:
    """
    Return per-role salary statistics.

    Columns: Role, Average Salary (LPA), Median Salary (LPA),
             Max Salary (LPA), Listings

    WHY SQL: AVG, MAX, COUNT, and ROUND are native SQL aggregates.
    Doing the same with Pandas .agg() is fine but requires loading every
    salary_avg value into memory; SQL pushes the aggregation down to
    the storage layer and returns only one row per role.

    Note: SQLite has no built-in MEDIAN — we use AVG as the centre
    estimate for the bar chart.  The box plot on the page still uses
    the raw rows from load_all_jobs() so the true distribution is shown.
    """
    tbl    = best_table()
    where, params = _where_clause(
        list(roles), list(role_groups), list(cities), list(exp_levels)
    )
    # Add salary filter directly into WHERE
    salary_filter = (
        " AND salary_avg IS NOT NULL AND salary_avg > 0"
        if where
        else
        " WHERE salary_avg IS NOT NULL AND salary_avg > 0"
    )
    sql = f"""
        SELECT
            role_searched                           AS Role,
            ROUND(AVG(salary_avg),  2)              AS "Average Salary (LPA)",
            ROUND(MAX(salary_avg),  2)              AS "Max Salary (LPA)",
            COUNT(*)                                AS Listings
        FROM  {tbl}
        {where}
        {salary_filter}
        GROUP BY role_searched
        ORDER BY "Average Salary (LPA)" DESC
    """
    return run_query(sql, params)


# ── 4G  TOP PAYING COMPANIES ──────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_top_paying_companies(
    roles:       tuple = (),
    role_groups: tuple = (),
    cities:      tuple = (),
    exp_levels:  tuple = (),
    min_listings: int  = 2,
    limit:        int  = 20,
) -> pd.DataFrame:
    """
    Return companies ranked by average salary (min_listings threshold applied).

    Columns: Company, Avg (LPA), Median-approx (LPA), Listings

    WHY SQL: The HAVING COUNT(*) >= min_listings filter cannot be done with
    Pandas value_counts alone — you'd need a merge step.  SQL does it inline.
    """
    tbl    = best_table()
    where, params = _where_clause(
        list(roles), list(role_groups), list(cities), list(exp_levels)
    )
    salary_and = (
        " AND salary_avg IS NOT NULL AND salary_avg > 0"
        if where
        else
        " WHERE salary_avg IS NOT NULL AND salary_avg > 0"
    )
    sql = f"""
        SELECT
            company                             AS Company,
            ROUND(AVG(salary_avg), 2)           AS "Avg (LPA)",
            COUNT(*)                            AS Listings
        FROM  {tbl}
        {where}
        {salary_and}
        GROUP BY company
        HAVING COUNT(*) >= {min_listings}
        ORDER BY "Avg (LPA)" DESC
        LIMIT {limit}
    """
    return run_query(sql, params)


# ── 4H  TOP PAYING CITIES ─────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_top_paying_cities(
    roles:        tuple = (),
    role_groups:  tuple = (),
    cities:       tuple = (),
    exp_levels:   tuple = (),
    min_listings: int   = 3,
    limit:        int   = 20,
) -> pd.DataFrame:
    """Return cities ranked by average salary (min_listings threshold applied)."""
    tbl    = best_table()
    where, params = _where_clause(
        list(roles), list(role_groups), list(cities), list(exp_levels)
    )
    city_col  = "standardized_city" if _col_exists("standardized_city") else "primary_city"
    salary_and = (
        " AND salary_avg IS NOT NULL AND salary_avg > 0"
        if where
        else
        " WHERE salary_avg IS NOT NULL AND salary_avg > 0"
    )
    sql = f"""
        SELECT
            {city_col}                          AS City,
            ROUND(AVG(salary_avg), 2)           AS "Avg (LPA)",
            COUNT(*)                            AS Listings
        FROM  {tbl}
        {where}
        {salary_and}
        GROUP BY {city_col}
        HAVING COUNT(*) >= {min_listings}
        ORDER BY "Avg (LPA)" DESC
        LIMIT {limit}
    """
    return run_query(sql, params)


# ── 4I  HIGHEST RATED COMPANIES ───────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_highest_rated_companies(
    roles:        tuple = (),
    role_groups:  tuple = (),
    cities:       tuple = (),
    exp_levels:   tuple = (),
    min_listings: int   = 3,
    limit:        int   = 20,
) -> pd.DataFrame:
    """
    Return companies ranked by average employee rating.

    Columns: Company, Avg Rating, Job Listings

    WHY SQL: AVG(company_rating) with a HAVING threshold is one aggregation
    query; the Pandas equivalent requires groupby + filter + sort, three
    separate operations on a Series already in memory.
    """
    tbl    = best_table()
    where, params = _where_clause(
        list(roles), list(role_groups), list(cities), list(exp_levels)
    )
    rating_and = (
        " AND company_rating IS NOT NULL"
        if where
        else
        " WHERE company_rating IS NOT NULL"
    )
    sql = f"""
        SELECT
            company                                 AS Company,
            ROUND(AVG(company_rating), 2)           AS "Avg Rating",
            COUNT(*)                                AS "Job Listings"
        FROM  {tbl}
        {where}
        {rating_and}
        GROUP BY company
        HAVING COUNT(*) >= {min_listings}
        ORDER BY "Avg Rating" DESC
        LIMIT {limit}
    """
    return run_query(sql, params)


# ── 4J  MOST REVIEWED COMPANIES ───────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_most_reviewed_companies(
    roles:       tuple = (),
    role_groups: tuple = (),
    cities:      tuple = (),
    exp_levels:  tuple = (),
    limit:       int   = 20,
) -> pd.DataFrame:
    """
    Return companies with the highest review count.

    company_reviews may be stored as a numeric or text value (e.g. '12K').
    SQLite CAST handles numeric strings; text like '12K' stays as-is and
    Pandas post-processing can parse it if needed.  We use MAX rather than
    AVG because the same company appears in many rows with the same review
    count — MAX picks the most recent/highest value safely.
    """
    tbl    = best_table()
    where, params = _where_clause(
        list(roles), list(role_groups), list(cities), list(exp_levels)
    )
    sql = f"""
        SELECT
            company                                         AS Company,
            MAX(CAST(company_reviews AS REAL))              AS Reviews,
            ROUND(AVG(company_rating), 2)                   AS "Avg Rating",
            COUNT(*)                                        AS "Job Listings"
        FROM  {tbl}
        {where}
        WHERE company_reviews IS NOT NULL
        GROUP BY company
        ORDER BY Reviews DESC
        LIMIT {limit}
    """
    # Note: the WHERE inside a query that already has a {where} clause
    # needs to be AND if {where} is non-empty. Rebuild cleanly:
    rating_and = (
        " AND company_reviews IS NOT NULL"
        if where else
        " WHERE company_reviews IS NOT NULL"
    )
    sql = f"""
        SELECT
            company                                         AS Company,
            MAX(CAST(company_reviews AS REAL))              AS Reviews,
            ROUND(AVG(company_rating), 2)                   AS "Avg Rating",
            COUNT(*)                                        AS "Job Listings"
        FROM  {tbl}
        {where}
        {rating_and}
        GROUP BY company
        ORDER BY Reviews DESC
        LIMIT {limit}
    """
    return run_query(sql, params)


# ── 4K  SALARY BY EXPERIENCE LEVEL ───────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_salary_by_experience(
    roles:       tuple = (),
    role_groups: tuple = (),
    cities:      tuple = (),
    exp_levels:  tuple = (),
) -> pd.DataFrame:
    """
    Return salary statistics grouped by experience level.

    Columns: Level, Avg (LPA), Max (LPA), Listings
    """
    tbl    = best_table()
    where, params = _where_clause(
        list(roles), list(role_groups), list(cities), list(exp_levels)
    )
    salary_and = (
        " AND salary_avg IS NOT NULL AND salary_avg > 0"
        if where else
        " WHERE salary_avg IS NOT NULL AND salary_avg > 0"
    )
    sql = f"""
        SELECT
            experience_level                    AS Level,
            ROUND(AVG(salary_avg), 2)           AS "Avg (LPA)",
            ROUND(MAX(salary_avg), 2)           AS "Max (LPA)",
            COUNT(*)                            AS Listings
        FROM  {tbl}
        {where}
        {salary_and}
        GROUP BY experience_level
        ORDER BY "Avg (LPA)" DESC
    """
    return run_query(sql, params)


# ── 4L  EXPERIENCE LEVEL DISTRIBUTION ────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_experience_distribution(
    roles:       tuple = (),
    role_groups: tuple = (),
    cities:      tuple = (),
    exp_levels:  tuple = (),
) -> pd.DataFrame:
    """Return (Level, Jobs) for experience level distribution charts."""
    tbl    = best_table()
    where, params = _where_clause(
        list(roles), list(role_groups), list(cities), list(exp_levels)
    )
    sql = f"""
        SELECT
            experience_level    AS Level,
            COUNT(*)            AS Jobs
        FROM  {tbl}
        {where}
        GROUP BY experience_level
        ORDER BY Jobs DESC
    """
    return run_query(sql, params)


# ── 4M  COMPANY SALARY COMPARISON (top 25 by avg salary) ─────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_company_salary_comparison(
    roles:       tuple = (),
    role_groups: tuple = (),
    cities:      tuple = (),
    exp_levels:  tuple = (),
    limit:       int   = 25,
) -> pd.DataFrame:
    """
    Full company profile for the salary comparison chart.

    Columns: Company, Avg Salary (LPA), Job Listings, Avg Rating
    """
    tbl    = best_table()
    where, params = _where_clause(
        list(roles), list(role_groups), list(cities), list(exp_levels)
    )
    salary_and = (
        " AND salary_avg IS NOT NULL AND salary_avg > 0"
        if where else
        " WHERE salary_avg IS NOT NULL AND salary_avg > 0"
    )
    sql = f"""
        SELECT
            company                                     AS Company,
            ROUND(AVG(salary_avg),    2)                AS "Avg Salary (LPA)",
            COUNT(*)                                    AS "Job Listings",
            ROUND(AVG(company_rating), 2)               AS "Avg Rating"
        FROM  {tbl}
        {where}
        {salary_and}
        GROUP BY company
        ORDER BY "Avg Salary (LPA)" DESC
        LIMIT {limit}
    """
    return run_query(sql, params)


# ── 4N  COMPANY HIRING × ROLE GROUP MATRIX ────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_company_role_group_matrix(
    roles:       tuple = (),
    role_groups: tuple = (),
    cities:      tuple = (),
    exp_levels:  tuple = (),
    top_companies: int = 12,
) -> pd.DataFrame:
    """
    Return long-format (company, role_group, Listings) for the
    heatmap and stacked bar on the Companies page.

    We first find the top companies by total listings in a subquery,
    then aggregate by role_group — two GROUP BY operations that would
    require two separate Pandas groupby calls plus a merge.
    """
    tbl    = best_table()
    where, params = _where_clause(
        list(roles), list(role_groups), list(cities), list(exp_levels)
    )
    # Subquery picks the top companies; outer query splits by role_group
    sql = f"""
        SELECT
            t.company,
            t.role_group,
            COUNT(*) AS Listings
        FROM  {tbl} t
        INNER JOIN (
            SELECT company
            FROM   {tbl}
            {where}
            GROUP  BY company
            ORDER  BY COUNT(*) DESC
            LIMIT  {top_companies}
        ) top ON t.company = top.company
        {where}
        GROUP BY t.company, t.role_group
        ORDER BY t.company, Listings DESC
    """
    # params used twice (inner + outer WHERE)
    return run_query(sql, params + params)