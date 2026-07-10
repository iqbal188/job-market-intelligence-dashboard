-- ============================================================
-- SALARY INTELLIGENCE QUERIES
-- Author: Mohd Iqbal
-- ============================================================

-- 1. Average Salary by Role

SELECT
    role_searched,
    ROUND(AVG(salary_avg), 2) AS avg_salary
FROM jobs_clean
WHERE salary_avg IS NOT NULL
GROUP BY role_searched
ORDER BY avg_salary DESC;


-- 2. Average Salary by Role Group

SELECT
    role_group,
    ROUND(AVG(salary_avg), 2) AS avg_salary
FROM jobs_clean
WHERE salary_avg IS NOT NULL
GROUP BY role_group
ORDER BY avg_salary DESC;


-- 3. Salary by Experience Level

SELECT
    experience_level,
    ROUND(AVG(salary_avg), 2) AS avg_salary
FROM jobs_clean
WHERE salary_avg IS NOT NULL
GROUP BY experience_level
ORDER BY avg_salary DESC;


-- 4. Top 10 Paying Cities

SELECT
    primary_city,
    COUNT(*) AS jobs,
    ROUND(AVG(salary_avg), 2) AS avg_salary
FROM jobs_clean
WHERE salary_avg IS NOT NULL
GROUP BY primary_city
HAVING COUNT(*) >= 5
ORDER BY avg_salary DESC
LIMIT 10;


-- 5. Top Paying Companies

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


-- 6. Highest Maximum Salary Roles

SELECT
    role_searched,
    MAX(salary_max) AS highest_salary
FROM jobs_clean
WHERE salary_max IS NOT NULL
GROUP BY role_searched
ORDER BY highest_salary DESC;


-- 7. Lowest Average Salary Roles

SELECT
    role_searched,
    ROUND(AVG(salary_avg), 2) AS avg_salary
FROM jobs_clean
WHERE salary_avg IS NOT NULL
GROUP BY role_searched
ORDER BY avg_salary ASC;


-- 8. Salary Distribution by Work Mode

SELECT
    work_mode,
    COUNT(*) AS jobs,
    ROUND(AVG(salary_avg), 2) AS avg_salary
FROM jobs_clean
WHERE salary_avg IS NOT NULL
GROUP BY work_mode
ORDER BY avg_salary DESC;


-- 9. Salary Records Coverage

SELECT
    COUNT(*) AS total_jobs,
    COUNT(salary_avg) AS salary_records,
    ROUND(
        COUNT(salary_avg) * 100.0 /
        COUNT(*),
        2
    ) AS salary_coverage_percent
FROM jobs_clean;


-- 10. Average Salary by Company Rating

SELECT
    ROUND(company_rating, 0) AS rating_band,
    COUNT(*) AS jobs,
    ROUND(AVG(salary_avg), 2) AS avg_salary
FROM jobs_clean
WHERE salary_avg IS NOT NULL
  AND company_rating IS NOT NULL
GROUP BY rating_band
ORDER BY rating_band DESC;