-- ============================================================
-- MARKET INTELLIGENCE QUERIES
-- Author: Mohd Iqbal
-- ============================================================

-- 1. Top Hiring Cities

SELECT
    primary_city,
    COUNT(*) AS total_jobs
FROM jobs_clean
GROUP BY primary_city
ORDER BY total_jobs DESC
LIMIT 20;


-- 2. Work Mode Distribution

SELECT
    work_mode,
    COUNT(*) AS total_jobs,
    ROUND(
        COUNT(*) * 100.0 /
        (SELECT COUNT(*) FROM jobs_clean),
        2
    ) AS percentage
FROM jobs_clean
GROUP BY work_mode
ORDER BY total_jobs DESC;


-- 3. Experience Level Distribution

SELECT
    experience_level,
    COUNT(*) AS total_jobs
FROM jobs_clean
GROUP BY experience_level
ORDER BY total_jobs DESC;


-- 4. Role Distribution

SELECT
    role_searched,
    COUNT(*) AS total_jobs
FROM jobs_clean
GROUP BY role_searched
ORDER BY total_jobs DESC;


-- 5. Role Group Distribution

SELECT
    role_group,
    COUNT(*) AS total_jobs
FROM jobs_clean
GROUP BY role_group
ORDER BY total_jobs DESC;


-- 6. Top Skills in Market

SELECT
    skills_standardized,
    COUNT(*) AS occurrences
FROM jobs_standardized
WHERE skills_standardized IS NOT NULL
GROUP BY skills_standardized
ORDER BY occurrences DESC
LIMIT 20;


-- 7. Cities with Highest Role Diversity

SELECT
    primary_city,
    COUNT(DISTINCT role_searched) AS unique_roles
FROM jobs_clean
GROUP BY primary_city
ORDER BY unique_roles DESC
LIMIT 20;


-- 8. Most Common Skills for AI Roles

SELECT
    role_searched,
    COUNT(*) AS jobs
FROM jobs_clean
WHERE role_group = 'AI'
GROUP BY role_searched
ORDER BY jobs DESC;


-- 9. Most Common Skills for Analytics Roles

SELECT
    role_searched,
    COUNT(*) AS jobs
FROM jobs_clean
WHERE role_group = 'Analytics'
GROUP BY role_searched
ORDER BY jobs DESC;


-- 10. Most Common Skills for Engineering Roles

SELECT
    role_searched,
    COUNT(*) AS jobs
FROM jobs_clean
WHERE role_group = 'Engineering'
GROUP BY role_searched
ORDER BY jobs DESC;


-- 11. Companies Per City

SELECT
    primary_city,
    COUNT(DISTINCT company) AS companies
FROM jobs_clean
GROUP BY primary_city
ORDER BY companies DESC
LIMIT 20;


-- 12. Jobs Per Company

SELECT
    company,
    COUNT(*) AS total_jobs
FROM jobs_clean
GROUP BY company
ORDER BY total_jobs DESC
LIMIT 20;


-- 13. Remote Job Share

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
    ) AS remote_percentage
FROM jobs_clean;


-- 14. Hybrid Job Share

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
    ) AS hybrid_percentage
FROM jobs_clean;


-- 15. Market Overview

SELECT
    COUNT(*) AS total_jobs,
    COUNT(DISTINCT company) AS companies,
    COUNT(DISTINCT primary_city) AS cities,
    COUNT(DISTINCT role_searched) AS roles
FROM jobs_clean;