#  Author: Mohd Iqbal | github.com/iqbal188

import time
import random
import pandas as pd
from datetime import date
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text
import os

#  SECTION 1 — CONFIGURATION  #

# ---- BROWSER MODE ----
HEADLESS = True  # True = no browser window (faster, less detectable), False = visible browser (slower, more human-like)                              

# ---- SCRAPING SETTINGS ----
PAGES_PER_ROLE   = 30                         
WAIT_MIN         = 2                          # min seconds between pages
WAIT_MAX         = 5                          # max seconds — random keeps it human-like
LOCATION         = "india"

# ---- OUTPUT PATHS ----
CSV_OUTPUT       = "data/raw/all_jobs.csv"
DB_PATH          = "sqlite:///db/jobs.db"

# ---- 11 ROLES ----
ROLES = [
    ("data-analyst", "Data Analyst"),
    ("business-analyst", "Business Analyst"),
    ("bi-analyst", "BI Analyst"),
    ("product-analyst", "Product Analyst"),

    ("data-engineer", "Data Engineer"),
    ("analytics-engineer", "Analytics Engineer"),

    ("data-scientist", "Data Scientist"),
    ("machine-learning-engineer", "Machine Learning Engineer"),
    ("ai-engineer", "AI Engineer"),
    ("generative-ai", "Generative AI Engineer"),
    ("nlp-engineer", "NLP Engineer")
]


#  SECTION 2 — BROWSER SETUP
#  Reads HEADLESS setting above and configures Chrome

def get_driver():
    """
    Creates Chrome WebDriver based on HEADLESS setting.
    HEADLESS = False → visible browser window
    HEADLESS = True  → silent background browser
    """
    options = webdriver.ChromeOptions()

    # ---- EXACT LINES THAT CONTROL HEADLESS MODE ----
    if HEADLESS:
        options.add_argument("--headless")      # hides browser window
        options.add_argument("--disable-gpu")   # needed on Windows in headless

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    # Fake real browser so Naukri doesn't detect Selenium
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver

#  SECTION 3 — PAGE SCRAPER
#  Loads one Naukri page and returns list of raw job dicts

def scrape_page(driver, page_num, role_key, role_name):
    """
    Scrapes one page for a given role.
    Returns list of job dicts with role_searched + scraped_date added.
    """
    # Build Naukri URL — page 1 has no number suffix
    if page_num == 1:
        url = f"https://www.naukri.com/{role_key}-jobs-in-{LOCATION}"
    else:
        url = f"https://www.naukri.com/{role_key}-jobs-in-{LOCATION}-{page_num}"

    print(f"  [{role_name}] Page {page_num} → {url}")
    driver.get(url)

    # Wait for job cards to load in DOM — timeout after 10 seconds
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "srp-jobtuple-wrapper"))
        )
    except:
        print(f"  [{role_name}] Page {page_num}: timed out — skipping")
        return []

    soup = BeautifulSoup(driver.page_source, "html.parser")
    job_cards = soup.find_all("div", class_="srp-jobtuple-wrapper")
    print(f"  [{role_name}] Page {page_num}: found {len(job_cards)} cards")

    jobs = []
    for card in job_cards:
        job = extract_job_data(card, role_name)
        if job:
            jobs.append(job)

    return jobs

#  SECTION 4 — DATA EXTRACTOR

def extract_job_data(card, role_name):
    """
    Extracts all fields from one job card.
    Adds role_searched and scraped_date columns.
    Returns dict or None if extraction fails.
    """
    try:
        # Job title + URL
        title_tag  = card.find("a", class_="title")
        title      = title_tag.text.strip() if title_tag else "N/A"
        job_url    = title_tag["href"]       if title_tag else "N/A"

        # Company name
        company_tag = card.find("a", class_="comp-name")
        company     = company_tag.text.strip() if company_tag else "N/A"

        # Location
        location_tag = card.find("span", class_="locWdth")
        location     = location_tag.text.strip() if location_tag else "N/A"

        # Experience required
        exp_tag    = card.find("span", class_="expwdth")
        experience = exp_tag.text.strip() if exp_tag else "N/A"

        # Salary — many companies hide this, stored as-is for cleaning later
        salary_tag = card.find("span", class_="sal")
        salary     = salary_tag.text.strip() if salary_tag else "Not Disclosed"

        # Skills — comma separated list
        skills_tags = card.find_all("li", class_="dot-gt")
        skills      = ", ".join([s.text.strip() for s in skills_tags]) if skills_tags else "N/A"

        # Date posted
        date_tag    = card.find("span", class_="job-post-day")
        date_posted = date_tag.text.strip() if date_tag else "N/A"

        # Company rating
        rating_tag    = card.find("span", class_="main-2")
        company_rating = rating_tag.text.strip() if rating_tag else "N/A"

        # Number of reviews — company popularity indicator
        reviews_tag      = card.find("a", class_="review ver-line")
        company_reviews  = reviews_tag.text.strip() if reviews_tag else "N/A"

        return {
            "title":          title,
            "company":        company,
            "location":       location,
            "experience":     experience,
            "salary":         salary,
            "skills":         skills,
            "date_posted":    date_posted,     
            "company_rating":  company_rating,
            "company_reviews": company_reviews,        
            "role_searched":  role_name,           # which role was searched
            "scraped_date":   str(date.today()),   # when this was scraped
            "job_url":        job_url
        }

    except Exception as e:
        print(f"  Error extracting card: {e}")
        return None

#  SECTION 5 — DATABASE HANDLER
#  Creates SQLite table and inserts rows — skips duplicates

def setup_database(engine):
    """Creates jobs table if it doesn't exist."""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS jobs (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                title         TEXT,
                company       TEXT,
                location      TEXT,
                experience    TEXT,
                salary        TEXT,
                skills        TEXT,
                date_posted      TEXT,
                company_rating   TEXT,
                company_reviews  TEXT,
                role_searched    TEXT,
                scraped_date  TEXT,
                job_url       TEXT UNIQUE
            )
        """))
        conn.commit()
    print("Database ready.")


def save_to_db(df, engine):
    """
    Inserts DataFrame rows into SQLite.
    Skips rows where job_url already exists (deduplication).
    """
    inserted = 0
    skipped  = 0

    with engine.connect() as conn:
        for _, row in df.iterrows():
            try:
                conn.execute(text("""
                    INSERT INTO jobs
                        (title, company, location, experience, salary, skills,
                        date_posted, company_rating, company_reviews, role_searched, scraped_date, job_url)
                    VALUES
                        (:title, :company, :location, :experience, :salary, :skills,
                        :date_posted, :company_rating, :company_reviews, :role_searched, :scraped_date, :job_url)
                """), row.to_dict())
                inserted += 1
            except:
                skipped += 1  # duplicate job_url — silently skip

        conn.commit()

    print(f"DB saved — {inserted} new rows, {skipped} duplicates skipped.")

#  SECTION 6 — MAIN PIPELINE
#  Orchestrates scraping all 20 roles end to end

def main():
    print("=" * 60)
    print("  Job Market Analytics — Scraping Pipeline")
    print(f"  Roles: {len(ROLES)} | Pages per role: {PAGES_PER_ROLE}")
    print(f"  Mode: {'Headless' if HEADLESS else 'Visible Browser'}")
    print("=" * 60)

    all_jobs = []
    driver   = get_driver()
    engine   = create_engine(DB_PATH)
    setup_database(engine)

    try:
        for i, (role_key, role_name) in enumerate(ROLES, 1):
            print(f"\n>>> [{i}/{len(ROLES)}] Scraping: {role_name.upper()}")
            role_jobs = []

            for page in range(1, PAGES_PER_ROLE + 1):
                jobs = scrape_page(driver, page, role_key, role_name)
                role_jobs.extend(jobs)

                # Random wait — looks human, reduces block risk
                wait = round(random.uniform(WAIT_MIN, WAIT_MAX), 1)
                print(f"  Waiting {wait}s...")
                time.sleep(wait)

            print(f"  {role_name}: {len(role_jobs)} jobs scraped")
            all_jobs.extend(role_jobs)

            # Save progress after every role — crash protection
            temp_df = pd.DataFrame(all_jobs)
            temp_df.to_csv("data/progress_backup.csv", index=False)
            print(f"  Progress saved — {len(all_jobs)} jobs so far")

    finally:
        driver.quit()  # always close browser even if error occurs

    if not all_jobs:
        print("No jobs scraped. Check your internet or Naukri's HTML structure.")
        return

    # Build DataFrame + deduplicate
    df = pd.DataFrame(all_jobs)
    before = len(df)
    df.drop_duplicates(subset=["job_url"], inplace=True)
    after = len(df)
    print(f"\nDeduplication: {before} → {after} rows ({before - after} removed)")

    # Save to CSV
    # Append to existing CSV instead of overwriting

    if os.path.exists(CSV_OUTPUT):
        existing_df = pd.read_csv(CSV_OUTPUT)
        combined_df = pd.concat([existing_df, df], ignore_index=True)
        combined_df.drop_duplicates(subset=["job_url"], inplace=True)
        combined_df.to_csv(CSV_OUTPUT, index=False)
        print(f"CSV updated: {CSV_OUTPUT} ({len(combined_df)} total rows)")
    else:
        df.to_csv(CSV_OUTPUT, index=False)
        print(f"CSV created: {CSV_OUTPUT} ({after} rows)")

    # Save to SQLite
    save_to_db(df, engine)

    # Final summary
    print("\n" + "=" * 60)
    print("  SCRAPING COMPLETE")
    print(f"  Total jobs collected : {after}")
    print(f"  Roles covered        : {df['role_searched'].nunique()}")
    print(f"  Top locations        : {df['location'].value_counts().head(3).to_dict()}")
    print("=" * 60)
    print(df.groupby("role_searched").size().reset_index(name="jobs_scraped").to_string(index=False))


if __name__ == "__main__":
    main()