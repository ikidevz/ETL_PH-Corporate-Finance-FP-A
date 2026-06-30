WITH actuals AS (
    SELECT fiscal_year, fiscal_month, account_key, cost_center_key, subsidiary_key,
           SUM(net_amount_php) AS actual_php
    FROM {{ ref('fct_gl_actuals') }}
    GROUP BY 1,2,3,4,5
),
forecast AS (
    SELECT fiscal_year, fiscal_month, account_key, cost_center_key, subsidiary_key,
           version, SUM(forecast_amount_php) AS forecast_php
    FROM {{ ref('fct_forecast') }}
    GROUP BY 1,2,3,4,5,6
)
SELECT
    f.fiscal_year,
    f.fiscal_month,
    f.version                                                    AS forecast_version,
    sub.subsidiary_code,
    sub.subsidiary_name,
    COALESCE(a.actual_php, 0)                                    AS actual_php,
    f.forecast_php,
    COALESCE(a.actual_php, 0) - f.forecast_php                   AS forecast_error_php,
    CASE WHEN f.forecast_php = 0 THEN NULL
         ELSE ROUND(
             ABS(COALESCE(a.actual_php, 0) - f.forecast_php)
             / ABS(f.forecast_php) * 100, 2)
    END                                                           AS abs_pct_error
FROM forecast f
LEFT JOIN actuals a USING (fiscal_year, fiscal_month, account_key, cost_center_key, subsidiary_key)
LEFT JOIN {{ ref('dim_subsidiary') }} sub USING (subsidiary_key)