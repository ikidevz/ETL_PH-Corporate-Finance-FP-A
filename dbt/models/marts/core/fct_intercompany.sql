{{
  config(
    materialized='incremental',
    unique_key='intercompany_id'
  )
}}

SELECT
    s.intercompany_id,
    d.date_key,
    d.fiscal_year,
    d.fiscal_month,
    from_sub.subsidiary_key                                        AS from_subsidiary_key,
    to_sub.subsidiary_key                                          AS to_subsidiary_key,
    s.ic_type,
    s.amount_php,
    s._loaded_at
FROM {{ ref('stg_intercompany') }}          s
LEFT JOIN {{ ref('dim_date') }}             d        ON s.posting_date     = d.date_key
LEFT JOIN {{ ref('dim_subsidiary') }}       from_sub ON s.from_subsidiary  = from_sub.subsidiary_code
LEFT JOIN {{ ref('dim_subsidiary') }}       to_sub   ON s.to_subsidiary    = to_sub.subsidiary_code
{% if is_incremental() %}
WHERE s._loaded_at > (SELECT MAX(_loaded_at) FROM {{ this }})
{% endif %}