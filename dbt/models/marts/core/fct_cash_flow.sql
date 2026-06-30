{{
  config(
    materialized='incremental',
    unique_key='bank_ref'
  )
}}

SELECT
    s.bank_ref,
    d.date_key,
    d.fiscal_year,
    d.fiscal_month,
    sub.subsidiary_key,
    a.account_key,
    s.debit_amount                                          AS outflow_php,
    s.credit_amount                                         AS inflow_php,
    s.net_amount                                            AS net_cash_php,
    s.cf_category,
    s._loaded_at
FROM {{ ref('stg_bank_statements') }}       s
LEFT JOIN {{ ref('dim_date') }}             d   ON s.txn_date   = d.date_key
LEFT JOIN {{ ref('dim_subsidiary') }}       sub ON s.subsidiary = sub.subsidiary_code
-- Map bank account type to a GL account for reporting joins
LEFT JOIN {{ ref('dim_account') }}          a   ON a.gl_account_code = CASE s.cf_category
    WHEN 'Operating'  THEN '4001'
    WHEN 'Investing'  THEN '6004'
    WHEN 'Financing'  THEN '7001'
    ELSE '4001'
END
{% if is_incremental() %}
WHERE s._loaded_at > (SELECT MAX(_loaded_at) FROM {{ this }})
{% endif %}