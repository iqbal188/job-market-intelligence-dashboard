#  Author: Mohd Iqbal | github.com/iqbal188

import re
import pandas as pd
from sqlalchemy import create_engine
from datetime import timedelta

SKILL_NORMALIZATION = {
    "ai": "artificial intelligence",
    "ml": "machine learning",
    "nlp": "natural language processing",
    "llm": "large language model",
    "rag": "retrieval augmented generation",

    "gen ai": "generative ai",
    "genai": "generative ai",

    "aiml": "artificial intelligence",

    "microsoft azure": "azure",

    "data bricks": "databricks",

    "advanced excel": "excel"
}

CITY_MAPPING = {

    # NCR
    "gurugram": "Delhi NCR",
    "gurugram(cyber city)": "Delhi NCR",
    "noida": "Delhi NCR",
    "greater noida": "Delhi NCR",
    "faridabad": "Delhi NCR",

    # Mumbai Region
    "navi mumbai": "Mumbai",
    "thane": "Mumbai",
    "mumbai suburban": "Mumbai",
    "mumbai(andheri east)": "Mumbai",
    "goregaon": "Mumbai",

    # Bengaluru
    "bangalore rural": "Bengaluru",

    # Pune
    "pune(baner)": "Pune",
    "pimpri-chinchwad": "Pune",

    # Hyderabad
    "hyderabad(hitec city)": "Hyderabad",
    "hyderabad(gachibowli)": "Hyderabad",
    "hyderabad(begumpet)": "Hyderabad",

    # Chennai
    "chennai(taramani)": "Chennai",

    # Jaipur
    "jaipur(vaishali nagar)": "Jaipur",

    # Chandigarh Tricity
    "mohali": "Chandigarh Tricity",
    "panchkula": "Chandigarh Tricity",

    "remote": "Remote",
    "india": "Unknown"
}

#  SECTION 1 — SETTINGS

DB_PATH        = "sqlite:///db/jobs.db"

#  SECTION 2 — LOAD DATA

def load_data():

    engine = create_engine(DB_PATH)
    df     = pd.read_sql("SELECT * FROM jobs", engine)

    print(f"Loaded {len(df):,} rows")
    return df


#  SECTION 3 — CLEAN SALARY
    
def clean_salary(salary):
    
    # If salary is hidden or unpaid — return NULL
    if pd.isna(salary) or salary in ["Not Disclosed", "Unpaid", "N/A"]:
        return None, None

    # Remove commas and extra spaces — "50,000" → "50000"
    salary = salary.replace(",", "").strip()

    # Try to find two numbers like "10-20" or "50000-3"
    numbers = re.findall(r"[\d.]+", salary)

    if len(numbers) < 2:
        return None, None

    min_val = float(numbers[0])
    max_val = float(numbers[1])

    # Convert thousands to Lakhs — if value > 99 it's in rupees not lakhs then 50000 → 0.5 Lakhs
    if min_val > 99:
        min_val = round(min_val / 100000, 2)
    if max_val > 99:
        max_val = round(max_val / 100000, 2)

    return min_val, max_val

def apply_salary_cleaning(df):

    print("Cleaning salary column...")

    # Apply clean_salary to each row — returns two values
    df[["salary_min", "salary_max"]] = df["salary"].apply(
        lambda x: pd.Series(clean_salary(x))
    )

    # How many rows have salary data
    has_salary = df["salary_min"].notna().sum()
    print(f"  Salary data available: {has_salary} rows")
    print(f"  Salary not disclosed : {len(df) - has_salary} rows")

    return df

#  SECTION 4 — CLEAN EXPERIENCE

def clean_experience(experience):

    if pd.isna(experience) or experience == "N/A":
        return None, None

    # Find all numbers in the string
    numbers = re.findall(r"\d+", experience)

    if len(numbers) < 2:
        return None, None

    return int(numbers[0]), int(numbers[1])


def apply_experience_cleaning(df):

    print("Cleaning experience column...")

    df[["exp_min", "exp_max"]] = df["experience"].apply(
        lambda x: pd.Series(clean_experience(x))
    )

    # Add experience level label based on exp_min
    def get_experience_level(exp_min):
        if pd.isna(exp_min):
            return "Unknown"
        elif exp_min == 0:
            return "Fresher"        # 0 years
        elif exp_min <= 2:
            return "Junior"         # 1-2 years
        elif exp_min <= 5:
            return "Mid Level"      # 3-5 years
        elif exp_min <= 10:
            return "Senior"         # 6-10 years
        else:
            return "Lead/Manager"   # 10+ years

    df["experience_level"] = df["exp_min"].apply(get_experience_level)

    print("  Experience levels distribution:")
    print(df["experience_level"].value_counts().to_string())

    return df

#  SECTION 4A — ADD SALARY & EXPERIENCE AVERAGES

def add_salary_average(df):

    df["salary_avg"] = (
        df["salary_min"] + df["salary_max"]
    ) / 2

    return df


def add_experience_average(df):

    df["exp_avg"] = (
        df["exp_min"] + df["exp_max"]
    ) / 2

    return df

#  SECTION 4B — CREATE ACTUAL POSTED DATE

def convert_posted_date(relative_date, scraped_date):

    if pd.isna(relative_date):
        return None

    relative_date = str(relative_date).lower().strip()

    try:

        scrape_dt = pd.to_datetime(scraped_date)

        if relative_date == "just now":
            return scrape_dt.date()

        if "day" in relative_date:

            days = int(
                re.findall(r"\d+", relative_date)[0]
            )

            return (
                scrape_dt -
                timedelta(days=days)
            ).date()

        if "week" in relative_date:

            weeks = int(
                re.findall(r"\d+", relative_date)[0]
            )

            return (
                scrape_dt -
                timedelta(days=weeks * 7)
            ).date()

        if "month" in relative_date:

            months = int(
                re.findall(r"\d+", relative_date)[0]
            )

            return (
                scrape_dt -
                timedelta(days=months * 30)
            ).date()

    except:
        return None

    return None


def apply_posted_date_cleaning(df):

    print("Creating actual posted dates...")

    df["posted_date_actual"] = df.apply(
        lambda row: convert_posted_date(
            row["date_posted"],
            row["scraped_date"]
        ),
        axis=1
    )

    print(
        f"  Posted dates created: "
        f"{df['posted_date_actual'].notna().sum()}"
    )

    return df

#  SECTION 5 — CLEAN LOCATION

def clean_location(location):

    if pd.isna(location) or location == "N/A":
        return "Unknown", "Unknown"

    location = location.strip()

    # Detect work mode
    if location.lower().startswith("hybrid"):
        work_mode = "Hybrid"
        # Remove "Hybrid - " prefix to get cities
        location  = re.sub(r"(?i)hybrid\s*-\s*", "", location).strip()
    elif location.lower() == "remote":
        return "Remote", "Remote"
    else:
        work_mode = "On-site"

    # Take only first city from comma separated list
    primary_city = location.split(",")[0].strip()

    return primary_city, work_mode

def apply_location_cleaning(df):

    print("Cleaning location column...")

    df[["primary_city", "work_mode"]] = df["location"].apply(
        lambda x: pd.Series(clean_location(x))
    )

    print("  Top 5 cities:")
    print(df["primary_city"].value_counts().head(5).to_string())
    print("  Work mode distribution:")
    print(df["work_mode"].value_counts().to_string())

    return df

def add_standardized_city(df):

    print("Creating standardized_city column...")

    df["standardized_city"] = (
        df["primary_city"]
        .fillna("Unknown")
        .str.strip()
        .str.lower()
        .replace(CITY_MAPPING)
        .apply(lambda x: x.title() if x != "Delhi NCR" else x)
    )

    return df

#  SECTION 6 — CLEAN COMPANY REVIEWS

def clean_reviews(reviews):

    if pd.isna(reviews) or reviews == "N/A":
        return None

    # Extract only the number from string
    numbers = re.findall(r"\d+", str(reviews))

    if numbers:
        return int(numbers[0])

    return None

def apply_reviews_cleaning(df):

    print("Cleaning company_reviews column...")

    df["company_reviews"] = df["company_reviews"].apply(clean_reviews)

    has_reviews = df["company_reviews"].notna().sum()
    print(f"  Reviews data available: {has_reviews} rows")

    return df

#  SECTION 7 — CLEAN SKILLS

def clean_skills(skills):

    if pd.isna(skills) or skills == "N/A":
        return None

    # Split by comma, strip spaces, lowercase each skill
    skill_list = []

    for skill in skills.split(","):

        skill = skill.strip().lower()

        skill = SKILL_NORMALIZATION.get(skill, skill)

        if skill:
            skill_list.append(skill)
    # Remove empty strings
    
    skill_list = [s for s in skill_list if s]
    
    skill_list = list(dict.fromkeys(skill_list))
    
    return ", ".join(skill_list)


def apply_skills_cleaning(df):

    print("Cleaning skills column...")

    df["skills"] = df["skills"].apply(clean_skills)

    has_skills = df["skills"].notna().sum()
    print(f"  Skills data available: {has_skills} rows")

    return df

#  SECTION 7A — SKILL COUNT

def add_skill_count(df):

    def count_skills(skill_string):

        if pd.isna(skill_string):
            return 0

        return len([
            skill.strip()
            for skill in skill_string.split(",")
            if skill.strip()
        ])

    df["skill_count"] = df["skills"].apply(count_skills)

    print("Creating skill_count column...")
    print(f"  Average skills per job: {df['skill_count'].mean():.1f}")

    return df


#  SECTION 8 — CLEAN COMPANY RATING

def apply_rating_cleaning(df):

    print("Cleaning company_rating column...")

    df["company_rating"] = pd.to_numeric(df["company_rating"], errors="coerce")

    has_rating = df["company_rating"].notna().sum()
    print(f"  Rating data available: {has_rating} rows")

    return df

def add_role_group(df):

    role_groups = {
        "Data Analyst": "Analytics",
        "Business Analyst": "Analytics",
        "BI Analyst": "Analytics",
        "Product Analyst": "Analytics",

        "Data Engineer": "Engineering",
        "Analytics Engineer": "Engineering",

        "Data Scientist": "AI",
        "Machine Learning Engineer": "AI",
        "AI Engineer": "AI",
        "Generative AI Engineer": "AI",
        "NLP Engineer": "AI"
    }

    df["role_group"] = df["role_searched"].map(role_groups)

    print("Role Group Distribution:")
    print(df["role_group"].value_counts().to_string())

    return df

#  SECTION 9 — SAVE CLEANED DATA

def save_cleaned_data(df):

    # Save to SQLite as new table — jobs_clean
    engine = create_engine(DB_PATH)
    df.to_sql("jobs_clean", engine, if_exists="replace", index=False)
    print(f"Cleaned data saved to SQLite table: jobs_clean")

#  SECTION 10 — MAIN PIPELINE

def main():
    print("=" * 60)
    print("  Job Market Analytics — Data Cleaning Pipeline")
    print("=" * 60)

    # Step 1 — Load
    df = load_data()
    print(f"\nRaw data shape  : {df.shape}")

    # Step 2 — Clean each column
    print()
    df = apply_salary_cleaning(df)
    print()
    df = apply_experience_cleaning(df)
    print()
    df = add_salary_average(df)
    print()
    df = add_experience_average(df)
    print()
    df = apply_posted_date_cleaning(df)
    print()
    df = apply_location_cleaning(df)
    print()
    df = add_standardized_city(df)
    print()
    df = apply_reviews_cleaning(df)
    print()
    df = apply_skills_cleaning(df)
    df = add_skill_count(df)
    print()
    df = apply_rating_cleaning(df)
    print()
    df = add_role_group(df)
    # Remove duplicate jobs
    before_dup = len(df)

    df = df.drop_duplicates(
        subset=["job_url"],
        keep="first"
)

    print(
        f"Removed {before_dup - len(df)} duplicate jobs"
    )
    # Step 3 — Drop rows where title is N/A (completely useless rows)
    before = len(df)
    df = df[df["title"].notna()]
    
    print(f"\nRemoved {before - len(df)} rows with no title")

    # Step 4 — Final shape
    print(f"\nCleaned data shape : {df.shape}")
    print(f"Columns            : {df.columns.tolist()}")

    # Step 5 — Save
    print()
    save_cleaned_data(df)

    # Step 6 — Final summary
    print("\n" + "=" * 60)
    print("  CLEANING COMPLETE")
    print(f"  Total clean rows     : {len(df)}")
    print(f"  Roles covered        : {df['role_searched'].nunique()}")
    print(f"  Salary available     : {df['salary_min'].notna().sum()} rows")
    print(f"  With experience data : {df['exp_min'].notna().sum()} rows")
    print(f"  With skills data     : {df['skills'].notna().sum()} rows")
    print(f"  With rating data     : {df['company_rating'].notna().sum()} rows")
    print("=" * 60)


if __name__ == "__main__":
    main()