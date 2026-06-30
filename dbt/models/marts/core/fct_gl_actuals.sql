{{
  config(
    materialized='incremental',
    unique_key='journal_id'
  )
}}

SELECT
    s.journal_id,
    d.date_key,
    d.fiscal_year,
    d.fiscal_month,
    a.account_key,
    cc.cost_center_key,
    sub.subsidiary_key,
    sc.scenario_key,
    s.debit_amount,
    s.credit_amount,
    s.net_amount,
    ROUND(s.net_amount * COALESCE(fx.usd_php_rate, 1) * COALESCE(a.sign_convention, 1), 2) AS net_amount_php,
    s.entry_source,
    s._loaded_at
FROM {{ ref('stg_gl_actuals') }}            s
LEFT JOIN {{ ref('dim_date') }}             d   ON s.posting_date    = d.date_key
LEFT JOIN {{ ref('dim_account') }}          a   ON s.gl_account      = a.gl_account_code
LEFT JOIN {{ ref('dim_cost_center') }}      cc  ON s.cost_center     = cc.cost_center_code
LEFT JOIN {{ ref('dim_subsidiary') }}       sub ON s.subsidiary      = sub.subsidiary_code
LEFT JOIN {{ ref('dim_scenario') }}         sc  ON sc.scenario_type  = 'Actual'
LEFT JOIN {{ ref('fx_rates') }}             fx  ON d.fiscal_year     = fx.fiscal_year
                                                AND d.fiscal_month   = fx.fiscal_month
{% if is_incremental() %}
WHERE s._loaded_at > (SELECT MAX(_loaded_at) FROM {{ this }})
{% endif %}