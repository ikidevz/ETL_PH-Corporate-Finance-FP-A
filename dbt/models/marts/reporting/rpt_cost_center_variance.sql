SELECT
    fiscal_year,
    fiscal_month,
    cost_center_code,
    department,
    subsidiary_code,
    subsidiary_name,
    SUM(actual_php)              AS actual_php,
    SUM(budget_php)              AS budget_php,
    SUM(actual_php) - SUM(budget_php) AS variance_vs_budget_php,
    CASE WHEN SUM(budget_php) = 0 THEN NULL
         ELSE ROUND((SUM(actual_php) - SUM(budget_php)) / ABS(SUM(budget_php)) * 100, 2)
    END                           AS variance_pct_vs_budget
FROM {{ ref('rpt_variance_analysis') }}
GROUP BY 1, 2, 3, 4, 5, 6