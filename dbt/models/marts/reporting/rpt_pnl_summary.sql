SELECT
    fiscal_year,
    fiscal_month,
    subsidiary_code,
    subsidiary_name,
    SUM(CASE WHEN account_type = 'Revenue'                   THEN actual_php ELSE 0 END) AS revenue,
    SUM(CASE WHEN account_type = 'COGS'                      THEN actual_php ELSE 0 END) AS cogs,
    SUM(CASE WHEN account_type = 'Revenue'                   THEN actual_php ELSE 0 END)
  - SUM(CASE WHEN account_type = 'COGS'                      THEN actual_php ELSE 0 END) AS gross_profit,
    SUM(CASE WHEN account_type = 'OpEx'                      THEN actual_php ELSE 0 END) AS opex,
    SUM(CASE WHEN account_type = 'Revenue' THEN actual_php ELSE 0 END)
  - SUM(CASE WHEN account_type = 'COGS'    THEN actual_php ELSE 0 END)
  - SUM(CASE WHEN account_type = 'OpEx'    THEN actual_php ELSE 0 END)                    AS ebitda,
    SUM(CASE WHEN account_type = 'Finance Cost'              THEN actual_php ELSE 0 END) AS finance_cost,
    SUM(CASE WHEN account_type = 'Tax'                       THEN actual_php ELSE 0 END) AS tax_expense,
    SUM(CASE WHEN account_type = 'Revenue' THEN actual_php ELSE 0 END)
  - SUM(CASE WHEN account_type = 'COGS'    THEN actual_php ELSE 0 END)
  - SUM(CASE WHEN account_type = 'OpEx'    THEN actual_php ELSE 0 END)
  - SUM(CASE WHEN account_type = 'Finance Cost' THEN actual_php ELSE 0 END)
  - SUM(CASE WHEN account_type = 'Tax'          THEN actual_php ELSE 0 END)               AS net_income
FROM {{ ref('rpt_variance_analysis') }}
GROUP BY 1, 2, 3, 4