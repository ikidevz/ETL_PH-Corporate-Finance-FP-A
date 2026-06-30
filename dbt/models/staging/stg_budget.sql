SELECT
    fiscal_year,
    fiscal_month,
    gl_account,
    account_type,
    cost_center,
    subsidiary,
    budget_amount                       AS budget_amount_php,
    scenario,
    version,
    _loaded_at
FROM {{ source('bronze', 'raw_budget') }}
WHERE budget_amount IS NOT NULL
  AND fiscal_year IS NOT NULL