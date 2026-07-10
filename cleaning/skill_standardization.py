import pandas as pd
from sqlalchemy import create_engine

DB_PATH = "sqlite:///db/jobs.db"

# LOAD DATA

def load_data():

    engine = create_engine(DB_PATH)

    df = pd.read_sql(
        "SELECT * FROM jobs_clean",
        engine
    )

    print(f"Loaded {len(df)} rows")

    return df

# SKILL STANDARDIZATION MAP

SKILL_MAPPING = {

    # Core Skills
    "python": "Python",
    "python programming": "Python",

    "sql": "SQL",
    "mysql": "SQL",
    "postgresql": "SQL",

    "aws": "AWS",
    "aws cloud": "AWS",
    "amazon web services": "AWS",

    "azure": "Azure",
    "azure cloud": "Azure",
    "microsoft azure": "Azure",

    "gcp": "Google Cloud",
    "google cloud platform": "Google Cloud",

    "power bi": "Power BI",
    "powerbi": "Power BI",
    "microsoft power bi": "Power BI",

    "tableau": "Tableau",
    "tableau desktop": "Tableau",

    # AI / ML
    "artificial intelligence": "AI",
    "aiml": "AI",

    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "machine learning algorithms": "Machine Learning",

    "deep learning": "Deep Learning",
    "dl": "Deep Learning",

    "natural language processing": "NLP",
    "nlp": "NLP",

    "large language model": "LLM",
    "large language models": "LLM",
    "llm": "LLM",

    "retrieval augmented generation": "RAG",
    "rag": "RAG",

    "generative ai": "Generative AI",
    "gen ai": "Generative AI",
    "genai": "Generative AI",
    "generative artificial intelligence": "Generative AI",

    "langchain": "LangChain",
    "langgraph": "LangChain",

    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",

    "numpy": "NumPy",

    "scikit-learn": "Scikit-Learn",
    "sklearn": "Scikit-Learn",

    # Analytics
    "data analysis": "Data Analysis",
    "data analytics": "Data Analysis",
    "analytics": "Data Analysis",

    "business analysis": "Business Analysis",
    "business analytics": "Business Analysis",

    # Platforms
    "data bricks": "Databricks"
}

# REMOVE GARBAGE SKILLS

BAD_SKILLS = {

    "Data",
    "Machine",
    "Science",
    "Computer",
    "Large",
    "Generation",
    "Building",
    "Focus",
    "Training",
    "Exp",
    "Loop",
    "Object",
    "Foundation",
    "Production",

    # Job Titles (NOT skills)
    "Data Scientist",
    "Data Engineer",
    "Ai Engineer",
    "Analytics Engineer",
    "Machine Learning Engineer",
    "Nlp Engineer",
    "Business Analyst",
    "Product Analyst",
    "Bi Analyst",
    "Ai Analyst"
}

# STANDARDIZE SKILLS

def standardize_skills(skill_string):

    if pd.isna(skill_string):
        return None

    standardized = []

    for skill in skill_string.split(","):

        skill = skill.strip().lower()

        if not skill:
            continue

        standardized_skill = SKILL_MAPPING.get(
            skill,
            skill.title()
        )

        # Remove garbage skills
        if standardized_skill in BAD_SKILLS:
            continue

        # Remove role names automatically
        if standardized_skill.endswith("Engineer"):
            continue

        if standardized_skill.endswith("Analyst"):
            continue

        standardized.append(
            standardized_skill
        )

    # Remove duplicates while preserving order
    standardized = list(
        dict.fromkeys(standardized)
    )

    if len(standardized) == 0:
        return None

    return ", ".join(standardized)

# APPLY

def apply_skill_standardization(df):

    print("Standardizing skills...")

    df["skills_standardized"] = (
        df["skills"]
        .apply(standardize_skills)
    )

    print(
        f"Skills standardized: "
        f"{df['skills_standardized'].notna().sum()}"
    )

    return df

# SAVE

def save_data(df):

    engine = create_engine(DB_PATH)

    df.to_sql(
        "jobs_standardized",
        engine,
        if_exists="replace",
        index=False
    )

    print("Saved table: jobs_standardized")

# MAIN

def main():

    print("=" * 60)
    print("Skill Standardization")
    print("=" * 60)

    df = load_data()

    df = apply_skill_standardization(df)

    save_data(df)

    print("\nDone.")


if __name__ == "__main__":
    main()