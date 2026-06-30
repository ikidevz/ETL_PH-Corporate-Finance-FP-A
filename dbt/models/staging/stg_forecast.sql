SELECT
    fiscal_year,
    fiscal_month,
    gl_account,
    cost_center,
    subsidiary,
    forecast_amount                     AS forecast_amount_php,
    currency,
    scenario,
    version,
    created_date,
    created_by,
    _loaded_at
FROM {{ source('bronze', 'raw_forecast') }}
WHERE forecast_amount IS NOT NULL
  AND fiscal_year IS NOT NULL
  AND version IN ('RF1', 'RF2', 'RF3')