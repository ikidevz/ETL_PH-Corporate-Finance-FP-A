WITH standalone AS (
    SELECT fiscal_year, fiscal_month, SUM(revenue) AS revenue, SUM(net_income) AS net_income
    FROM {{ ref('rpt_pnl_summary') }}
    GROUP BY 1, 2
),
eliminations AS (
    SELECT fiscal_year, fiscal_month, SUM(amount_php) AS total_intercompany_php
    FROM {{ ref('fct_intercompany') }}
    GROUP BY 1, 2
)
SELECT
    s.fiscal_year,
    s.fiscal_month,
    s.revenue                                                    AS standalone_revenue,
    s.net_income                                                 AS standalone_net_income,
    COALESCE(e.total_intercompany_php, 0)                        AS intercompany_eliminations_php,
    s.revenue - COALESCE(e.total_intercompany_php, 0)            AS consolidated_revenue,
    s.net_income                                                 AS consolidated_net_income
FROM standalone s
LEFT JOIN eliminations e USING (fiscal_year, fiscal_month)