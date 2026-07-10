-- ============================================================
-- DASHBOARD KPI QUERIES
-- Author: Mohd Iqbal
-- ============================================================

-- ============================================================
-- 1. Total Jobs
-- ============================================================

SELECT
    COUNT(*) AS total_jobs
FROM jobs_clean;
    

-- ============================================================
-- 2. Total Companies
-- ============================================================

SELECT
    COUNT(DISTINCT company) AS total_companies
FROM jobs_clean;


-- ============================================================
-- 3. Total Cities
-- ============================================================

SELECT
    COUNT(DISTINCT primary_city) AS total_cities
FROM jobs_clean;


-- ============================================================
-- 4. Total Roles
-- ============================================================

SELECT
    COUNT(DISTINCT role_searched) AS total_roles
FROM jobs_clean;


-- ============================================================
-- 5. Average Salary
-- ============================================================

SELECT
    ROUND(AVG(salary_avg), 2) AS avg_salary
FROM jobs_clean
WHERE salary_avg IS NOT NULL;


-- ============================================================
-- 6. Top Hiring City
-- ============================================================

SELECT
    primary_city,
    COUNT(*) AS jobs
FROM jobs_clean
GROUP BY primary_city
ORDER BY jobs DESC
LIMIT 1;


-- ============================================================
-- 7. Top Hiring Company
-- ============================================================

SELECT
    company,
    COUNT(*) AS jobs
FROM jobs_clean
GROUP BY company
ORDER BY jobs DESC
LIMIT 1;


-- ============================================================
-- 8. Highest Paying Role
-- ============================================================

SELECT
    role_searched,
    ROUND(AVG(salary_avg), 2) AS avg_salary
FROM jobs_clean
WHERE salary_avg IS NOT NULL
GROUP BY role_searched
ORDER BY avg_salary DESC
LIMIT 1;


-- ============================================================
-- 9. Top Hiring Role
-- ============================================================

SELECT
    role_searched,
    COUNT(*) AS jobs
FROM jobs_clean
GROUP BY role_searched
ORDER BY jobs DESC
LIMIT 1;


-- ============================================================
-- 10. Average Company Rating
-- ============================================================

SELECT
    ROUND(AVG(company_rating), 2) AS avg_rating
FROM jobs_clean
WHERE company_rating IS NOT NULL;


-- ============================================================
-- 11. Remote Jobs %
-- ============================================================

SELECT
    ROUND(
        SUM(
            CASE
                WHEN work_mode = 'Remote'
                THEN 1
                ELSE 0
            END
        ) * 100.0
        / COUNT(*),
        2
    ) AS remote_percent
FROM jobs_clean;


-- ============================================================
-- 12. Hybrid Jobs %
-- ============================================================

SELECT
    ROUND(
        SUM(
            CASE
                WHEN work_mode = 'Hybrid'
                THEN 1
                ELSE 0
            END
        ) * 100.0
        / COUNT(*),
        2
    ) AS hybrid_percent
FROM jobs_clean;


-- ============================================================
-- 13. Salary By Role Group
-- ============================================================

SELECT
    role_group,
    ROUND(AVG(salary_avg), 2) AS avg_salary
FROM jobs_clean
WHERE salary_avg IS NOT NULL
GROUP BY role_group
ORDER BY avg_salary DESC;


-- ============================================================
-- 14. Jobs By Experience Level
-- ============================================================

SELECT
    experience_level,
    COUNT(*) AS jobs
FROM jobs_clean
GROUP BY experience_level
ORDER BY jobs DESC;


-- ============================================================
-- 15. Top 10 Cities
-- ============================================================

SELECT
    primary_city,
    COUNT(*) AS jobs
FROM jobs_clean
GROUP BY primary_city
ORDER BY jobs DESC
LIMIT 10;


-- ============================================================
-- 16. Top 10 Companies
-- ============================================================

SELECT
    company,
    COUNT(*) AS jobs
FROM jobs_clean
GROUP BY company
ORDER BY jobs DESC
LIMIT 10;


-- ============================================================
-- 17. Top Paying Cities
-- ============================================================

SELECT
    primary_city,
    ROUND(AVG(salary_avg), 2) AS avg_salary
FROM jobs_clean
WHERE salary_avg IS NOT NULL
GROUP BY primary_city
HAVING COUNT(*) >= 5
ORDER BY avg_salary DESC
LIMIT 10;


-- ============================================================
-- 18. Top Paying Companies
-- ============================================================

SELECT
    company,
    ROUND(AVG(salary_avg), 2) AS avg_salary
FROM jobs_clean
WHERE salary_avg IS NOT NULL
GROUP BY company
HAVING COUNT(*) >= 3
ORDER BY avg_salary DESC
LIMIT 10;


-- ============================================================
-- 19. Role Group Distribution
-- ============================================================

SELECT
    role_group,
    COUNT(*) AS jobs
FROM jobs_clean
GROUP BY role_group
ORDER BY jobs DESC;


-- ============================================================
-- 20. Market Summary
-- ============================================================

SELECT
    COUNT(*) AS total_jobs,
    COUNT(DISTINCT company) AS companies,
    COUNT(DISTINCT primary_city) AS cities,
    COUNT(DISTINCT role_searched) AS roles
FROM jobs_clean;