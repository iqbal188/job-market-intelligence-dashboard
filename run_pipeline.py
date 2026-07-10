import time
import shutil
import sqlite3
import pandas as pd
import os

from datetime import datetime

from scraper.scraper import main as scrape_jobs
from cleaning.clean_data import main as clean_jobs
from cleaning.skill_standardization import main as standardize_skills

def create_backup():

    print("\nCreating backup...")

    backup_date = datetime.now().strftime("%Y-%m-%d_%H-%M")

    backup_dir = os.path.join(
        "backups",
        backup_date
    )

    os.makedirs(
        backup_dir,
        exist_ok=True
    )

    # Backup database
    shutil.copy2(
        "db/jobs.db",
        os.path.join(
            backup_dir,
            "jobs.db"
        )
    )

    conn = sqlite3.connect(
        "db/jobs.db"
    )

    try:

        pd.read_sql(
            "SELECT * FROM jobs_clean",
            conn
        ).to_csv(
            os.path.join(
                backup_dir,
                "jobs_clean.csv"
            ),
            index=False
        )

        pd.read_sql(
            "SELECT * FROM jobs_standardized",
            conn
        ).to_csv(
            os.path.join(
                backup_dir,
                "jobs_standardized.csv"
            ),
            index=False
        )

    except Exception as e:

        print(
            f"Warning: {e}"
        )

    finally:
        conn.close()

    if os.path.exists(
        "data/raw/all_jobs.csv"
    ):

        shutil.copy2(
            "data/raw/all_jobs.csv",
            os.path.join(
                backup_dir,
                "all_jobs.csv"
            )
        )

    print(
        f"Backup saved: {backup_dir}"
    )

def execute_pipeline():

    start = time.time()

    print("=" * 60)
    print("JOB MARKET INTELLIGENCE PIPELINE")
    print("=" * 60)

    print("\n[1/3] Scraping Jobs...")
    scrape_jobs()

    print("\n[2/3] Cleaning Data...")
    clean_jobs()

    print("\n[3/3] Standardizing Skills...")
    standardize_skills()

    elapsed = round(time.time() - start, 2)
    
    create_backup()

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETED")
    print(f"Total Time: {elapsed} seconds")
    print("=" * 60)


if __name__ == "__main__":

    try:
        execute_pipeline()

    except Exception as e:

        print("\n" + "=" * 60)
        print("PIPELINE FAILED")
        print(f"Error: {e}")
        print("=" * 60)

        raise