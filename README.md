# 📊 Job Market Intelligence Dashboard

> **End-to-End Data Engineering & Analytics Project** built with
> **Python, Selenium, SQLite, SQLAlchemy, Pandas, Plotly, and
> Streamlit**.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red?logo=streamlit)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-yellow)

------------------------------------------------------------------------

## 🚀 Overview

The **Job Market Intelligence Dashboard** is an end-to-end ETL project
that collects job listings from **Naukri.com**, cleans and standardizes
the data, stores it in **SQLite**, performs **SQL-based analytics**, and
visualizes insights using **Streamlit**.

The project demonstrates a production-inspired workflow:

``` text
Extract → Transform → Load → Analytics → Visualization
```

## 📊 Dataset

The dashboard analyzes real-time job market data collected from Naukri.com.

The automated ETL pipeline refreshes the dataset periodically, ensuring that analytics reflect the latest available job listings.

The dataset contains:

- Job titles
- Companies
- Cities
- Salary information
- Experience requirements
- Skills
- Company ratings
- Review counts

------------------------------------------------------------------------

## ✨ Features

-   Selenium-based job scraper
-   SQLite database
-   Automated ETL pipeline
-   Data cleaning & normalization
-   Skill standardization
-   SQL-first analytics
-   Interactive Streamlit dashboard
-   Automatic timestamped backups

------------------------------------------------------------------------

## 🏗 Architecture

``` text
Naukri.com
     │
     ▼
Selenium Scraper
     │
     ▼
SQLite (jobs)
     │
     ▼
Cleaning Pipeline
     │
     ▼
SQLite (jobs_clean)
     │
     ▼
Skill Standardization
     │
     ▼
SQLite (jobs_standardized)
     │
     ▼
SQL Query Layer
     │
     ▼
Streamlit Dashboard
```

------------------------------------------------------------------------

## 🔄 ETL Pipeline

### Extract

-   Scrape multiple Data & AI job roles
-   Store raw data in SQLite

### Transform

-   Clean salary & experience
-   Standardize cities
-   Normalize skills
-   Create analytics-ready fields

### Load

-   Maintain three layers:
    -   `jobs`
    -   `jobs_clean`
    -   `jobs_standardized`

------------------------------------------------------------------------

## 📁 Project Structure

``` text
job-market-intelligence/
├── scraper/
├── cleaning/
├── dashboard/
├── sql/
├── db/
├── data/
├── backups/
├── run_pipeline.py
├── update_data.bat
├── requirements.txt
└── README.md
```

------------------------------------------------------------------------

## 🛠 Technology Stack

  Category          Technology
  ----------------- ---------------
  Language          Python
  Web Scraping      Selenium
  Database          SQLite
  ORM               SQLAlchemy
  Data Processing   Pandas
  Dashboard         Streamlit
  Visualization     Plotly
  HTML Parsing      BeautifulSoup
  Version Control   Git & GitHub

------------------------------------------------------------------------

## 📊 Dashboard

### 🏠 Home

-   KPIs
-   Hiring cities
-   Hiring roles
-   Company statistics

### 🛠 Skills

-   Top skills
-   AI & GenAI skills
-   Skill demand

### 💰 Salary

-   Salary by role
-   Salary by experience
-   Highest paying cities
-   Highest paying companies

### 🏢 Companies

-   Top hiring companies
-   Ratings
-   Reviews
-   Hiring trends

------------------------------------------------------------------------

## 🗄 Database

  Table               Purpose
  ------------------- -------------------------
  jobs                Raw scraped data
  jobs_clean          Cleaned dataset
  jobs_standardized   Analytics-ready dataset

------------------------------------------------------------------------

## ⚙ Installation

``` bash
git clone https://github.com/<your-username>/job-market-intelligence-dashboard.git
cd job-market-intelligence-dashboard

python -m venv venv
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

------------------------------------------------------------------------

## ▶ Running the Project

Run the complete ETL pipeline:

``` bash
python run_pipeline.py
```

Or on Windows:

``` text
update_data.bat
```

Launch the dashboard:

``` bash
streamlit run dashboard/Home.py
```

------------------------------------------------------------------------

## 📸 Dashboard Preview

Replace these placeholders after capturing screenshots.

``` markdown
![Home](screenshots/home.png)

![Skills](screenshots/skills.png)

![Salary](screenshots/salary.png)

![Companies](screenshots/companies.png)
```

------------------------------------------------------------------------

## 📈 Engineering Highlights

-   Modular architecture
-   Separation of concerns
-   SQL-first aggregations
-   Pandas for row transformations
-   Automatic backups
-   Reusable dashboard components
-   Configurable settings

------------------------------------------------------------------------

## 🔮 Future Improvements

-   Historical analytics
-   Weekly market reports
-   Salary trends
-   Skill growth analysis
-   PostgreSQL support
-   Docker deployment

------------------------------------------------------------------------

## 📄 License

This project is licensed under the **MIT License**.

------------------------------------------------------------------------

## 👨‍💻 Author

**Mohd Iqbal**

-   B.Tech -- Computer Science & Engineering
-   Aspiring Data Engineer / Data Analyst

GitHub: `https://github.com/<your-username>`

LinkedIn: `https://linkedin.com/in/<your-linkedin>`

------------------------------------------------------------------------

⭐ If you found this project useful, consider giving it a star on
GitHub.
