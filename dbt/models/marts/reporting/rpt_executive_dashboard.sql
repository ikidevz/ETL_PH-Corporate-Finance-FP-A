WITH latest_closed AS (
    SELECT
        MAX(fiscal_year * 100 + fiscal_month)   AS latest_period_key,
        MAX(fiscal_year)                         AS fiscal_year,
        MAX(fiscal_month)                        AS fiscal_month
    FROM {{ source('control', 'period_lock') }}
    WHERE period_status = 'CLOSED'
),
pnl AS (
    SELECT
        v.fiscal_year,
        v.fiscal_month,
        SUM(CASE WHEN v.pnl_line = 'Net Revenue'
                 THEN v.actual_php     ELSE 0 END)  AS total_revenue,
        SUM(CASE WHEN v.pnl_line = 'COGS'
                 THEN v.actual_php     ELSE 0 END)  AS total_cogs,
        SUM(CASE WHEN v.pnl_line = 'Net Revenue' THEN v.actual_php ELSE 0 END)
      - SUM(CASE WHEN v.pnl_line = 'COGS'        THEN v.actual_php ELSE 0 END)  AS gross_profit,
        SUM(CASE WHEN v.pnl_line = 'Personnel Costs'
                 THEN v.actual_php     ELSE 0 END)  AS personnel_costs,
        SUM(CASE WHEN v.pnl_line = 'Net Revenue' THEN v.actual_php ELSE 0 END)
      - SUM(CASE WHEN v.pnl_line IN ('COGS','Personnel Costs','Occupancy',
                                      'Marketing','D&A','Admin & General')
                 THEN v.actual_php     ELSE 0 END)  AS ebitda,
        SUM(CASE WHEN v.pnl_line = 'Finance Costs'
                 THEN v.actual_php     ELSE 0 END)  AS finance_costs,
        -- net_income = ebitda - finance_costs - tax (Tax pnl_line not yet
        -- broken out above, so subtract Finance Costs and Tax explicitly)
        SUM(CASE WHEN v.pnl_line = 'Net Revenue' THEN v.actual_php ELSE 0 END)
      - SUM(CASE WHEN v.pnl_line IN ('COGS','Personnel Costs','Occupancy',
                                      'Marketing','D&A','Admin & General',
                                      'Finance Costs','Tax')
                 THEN v.actual_php     ELSE 0 END)  AS net_income,
        SUM(v.budget_php)                           AS total_budget,
        SUM(v.forecast_php)                         AS total_forecast,
        SUM(v.variance_vs_budget_php)               AS total_variance_vs_budget
    FROM {{ ref('rpt_variance_analysis') }} v
    INNER JOIN latest_closed lc
        ON v.fiscal_year  = lc.fiscal_year
       AND v.fiscal_month = lc.fiscal_month
    GROUP BY 1, 2
),
cash AS (
    SELECT
        cf.fiscal_year,
        cf.fiscal_month,
        SUM(CASE WHEN cf.cf_category = 'Operating'  THEN cf.net_cash_php ELSE 0 END) AS operating_cf,
        SUM(CASE WHEN cf.cf_category = 'Investing'  THEN cf.net_cash_php ELSE 0 END) AS investing_cf,
        SUM(CASE WHEN cf.cf_category = 'Financing'  THEN cf.net_cash_php ELSE 0 END) AS financing_cf,
        SUM(cf.net_cash_php)                                                          AS net_cash_movement
    FROM {{ ref('fct_cash_flow') }} cf
    INNER JOIN latest_closed lc
        ON cf.fiscal_year  = lc.fiscal_year
       AND cf.fiscal_month = lc.fiscal_month
    GROUP BY 1, 2
)
SELECT
    p.fiscal_year,
    p.fiscal_month,
    -- ── P&L KPIs ──────────────────────────────────────────────────────
    p.total_revenue,
    p.total_cogs,
    p.gross_profit,
    CASE WHEN p.total_revenue = 0 THEN NULL
         ELSE ROUND(p.gross_profit / p.total_revenue * 100, 2)
    END                                                         AS gross_margin_pct,
    p.ebitda,
    CASE WHEN p.total_revenue = 0 THEN NULL
         ELSE ROUND(p.ebitda / p.total_revenue * 100, 2)
    END                                                         AS ebitda_margin_pct,
    p.finance_costs,
    p.net_income,
    CASE WHEN p.total_revenue = 0 THEN NULL
         ELSE ROUND(p.net_income / p.total_revenue * 100, 2)
    END                                                         AS net_margin_pct,
    -- ── Budget variance KPIs ──────────────────────────────────────────
    p.total_budget,
    p.total_forecast,
    p.total_variance_vs_budget,
    CASE WHEN p.total_budget = 0 THEN NULL
         ELSE ROUND(p.total_variance_vs_budget / ABS(p.total_budget) * 100, 2)
    END                                                         AS variance_pct_vs_budget,
    -- ── Cash flow KPIs ────────────────────────────────────────────────
    c.operating_cf,
    c.investing_cf,
    c.financing_cf,
    c.net_cash_movement,
    -- ── Derived executive flags ───────────────────────────────────────
    CASE WHEN p.net_income > 0      THEN 'PROFITABLE'
         WHEN p.net_income = 0      THEN 'BREAK-EVEN'
         ELSE 'LOSS'
    END                                                         AS profitability_status,
    CASE WHEN c.operating_cf > 0    THEN 'POSITIVE'
         ELSE 'NEGATIVE'
    END                                                         AS operating_cf_status,
    CASE
        WHEN p.total_variance_vs_budget >= 0                              THEN 'ON-BUDGET'
        WHEN p.total_variance_vs_budget / ABS(p.total_budget) >= -0.05   THEN 'WITHIN-5%'
        ELSE 'OVER-BUDGET'
    END                                                         AS budget_status
FROM pnl p
LEFT JOIN cash c
    ON p.fiscal_year  = c.fiscal_year
   AND p.fiscal_month = c.fiscal_month