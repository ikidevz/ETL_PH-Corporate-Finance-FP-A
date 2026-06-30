WITH actuals AS (
    SELECT
        fiscal_year, fiscal_month,
        account_key, cost_center_key, subsidiary_key,
        SUM(net_amount_php)         AS actual_php
    FROM {{ ref('fct_gl_actuals') }}
    GROUP BY 1,2,3,4,5
),
budget AS (
    SELECT
        fiscal_year, fiscal_month,
        account_key, cost_center_key, subsidiary_key,
        SUM(budget_amount_php)      AS budget_php
    FROM {{ ref('fct_budget') }}
    GROUP BY 1,2,3,4,5
),
forecast AS (
    SELECT
        fiscal_year, fiscal_month,
        account_key, cost_center_key, subsidiary_key,
        SUM(forecast_amount_php)    AS forecast_php
    FROM {{ ref('fct_forecast') }}
    GROUP BY 1,2,3,4,5
)
SELECT
    COALESCE(a.fiscal_year,  b.fiscal_year,  f.fiscal_year)  AS fiscal_year,
    COALESCE(a.fiscal_month, b.fiscal_month, f.fiscal_month) AS fiscal_month,
    acc.account_key,
    acc.gl_account_code,
    acc.account_name,
    acc.account_type,
    acc.pnl_line,
    cc.cost_center_code,
    cc.department,
    sub.subsidiary_code,
    sub.subsidiary_name,
    COALESCE(a.actual_php,   0)                              AS actual_php,
    COALESCE(b.budget_php,   0)                              AS budget_php,
    COALESCE(f.forecast_php, 0)                              AS forecast_php,
    COALESCE(a.actual_php, 0) - COALESCE(b.budget_php, 0)   AS variance_vs_budget_php,
    COALESCE(a.actual_php, 0) - COALESCE(f.forecast_php, 0) AS variance_vs_forecast_php,
    CASE
        WHEN COALESCE(b.budget_php, 0) = 0 THEN NULL
        ELSE ROUND(
            (COALESCE(a.actual_php,0) - COALESCE(b.budget_php,0))
            / ABS(b.budget_php) * 100, 2)
    END                                                      AS variance_pct_vs_budget
FROM actuals a
FULL OUTER JOIN budget   b USING (fiscal_year, fiscal_month, account_key, cost_center_key, subsidiary_key)
FULL OUTER JOIN forecast f USING (fiscal_year, fiscal_month, account_key, cost_center_key, subsidiary_key)
LEFT JOIN {{ ref('dim_account') }}      acc USING (account_key)
LEFT JOIN {{ ref('dim_cost_center') }}  cc  USING (cost_center_key)
LEFT JOIN {{ ref('dim_subsidiary') }}   sub USING (subsidiary_key)