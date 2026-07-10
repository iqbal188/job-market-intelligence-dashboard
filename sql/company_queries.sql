-- ============================================================
-- COMPANY INTELLIGENCE QUERIES
-- Author: Mohd Iqbal
-- ============================================================

-- 1. Top Hiring Companies

SELECT
    company,
    COUNT(*) AS total_jobs
FROM jobs_clean
GROUP BY company
ORDER BY total_jobs DESC
LIMIT 20;


-- 2. Highest Rated Companies

SELECT
    company,
    COUNT(*) AS records,
    ROUND(AVG(company_rating), 2) AS avg_rating
FROM jobs_clean
WHERE company_rating IS NOT NULL
GROUP BY company
HAVING COUNT(*) >= 3
ORDER BY avg_rating DESC
LIMIT 20;


-- 3. Most Reviewed Companies

SELECT
    company,
    ROUND(AVG(company_reviews), 0) AS avg_reviews
FROM jobs_clean
WHERE company_reviews IS NOT NULL
GROUP BY company
ORDER BY avg_reviews DESC
LIMIT 20;


-- 4. Top Paying Companies

SELECT
    company,
    COUNT(*) AS salary_records,
    ROUND(AVG(salary_avg), 2) AS avg_salary
FROM jobs_clean
WHERE salary_avg IS NOT NULL
GROUP BY company
HAVING COUNT(*) >= 3
ORDER BY avg_salary DESC
LIMIT 20;


-- 5. Companies Hiring Data Analysts

SELECT
    company,
    COUNT(*) AS jobs
FROM jobs_clean
WHERE role_searched = 'Data Analyst'
GROUP BY company
ORDER BY jobs DESC
LIMIT 20;


-- 6. Companies Hiring Data Scientists

SELECT
    company,
    COUNT(*) AS jobs
FROM jobs_clean
WHERE role_searched = 'Data Scientist'
GROUP BY company
ORDER BY jobs DESC
LIMIT 20;


-- 7. Companies Hiring AI Talent

SELECT
    company,
    COUNT(*) AS ai_jobs
FROM jobs_clean
WHERE role_group = 'AI'
GROUP BY company
ORDER BY ai_jobs DESC
LIMIT 20;


-- 8. Companies Hiring Engineering Talent

SELECT
    company,
    COUNT(*) AS engineering_jobs
FROM jobs_clean
WHERE role_group = 'Engineering'
GROUP BY company
ORDER BY engineering_jobs DESC
LIMIT 20;


-- 9. Average Company Rating by Role Group

SELECT
    role_group,
    ROUND(AVG(company_rating), 2) AS avg_rating
FROM jobs_clean
WHERE company_rating IS NOT NULL
GROUP BY role_group
ORDER BY avg_rating DESC;


-- 10. Company Reputation vs Salary

SELECT
    company,
    ROUND(AVG(company_rating),2) AS rating,
    ROUND(AVG(salary_avg),2) AS salary
FROM jobs_clean
WHERE company_rating IS NOT NULL
  AND salary_avg IS NOT NULL
GROUP BY company
HAVING COUNT(*) >= 3
ORDER BY salary DESC;


-- 11. Companies With Most Locations

SELECT
    company,
    COUNT(DISTINCT primary_city) AS cities
FROM jobs_clean
GROUP BY company
ORDER BY cities DESC
LIMIT 20;


-- 12. Top Companies by Role Diversity

SELECT
    company,
    COUNT(DISTINCT role_searched) AS unique_roles
FROM jobs_clean
GROUP BY company
ORDER BY unique_roles DESC
LIMIT 20;