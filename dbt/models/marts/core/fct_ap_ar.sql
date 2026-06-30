{{ config(materialized='table') }}

SELECT
    {{ dbt_utils.generate_surrogate_key(['invoice_id']) }}         AS ap_ar_key,
    s.invoice_id,
    s.doc_type,
    d.date_key                                                     AS invoice_date_key,
    s.fiscal_year,
    s.fiscal_month,
    sub.subsidiary_key,
    s.counterparty,
    s.amount_php,
    -- Normalize so AP is a future cash outflow (negative) and AR a future
    -- cash inflow (positive) when summed for working-capital metrics.
    CASE WHEN s.doc_type = 'AP' THEN -s.amount_php ELSE s.amount_php END AS signed_amount_php,
    s.status,
    s.due_date,
    s.paid_date,
    s.days_outstanding,
    s._loaded_at
FROM {{ ref('stg_ap_ar') }}                 s
LEFT JOIN {{ ref('dim_date') }}             d   ON s.invoice_date = d.date_key
LEFT JOIN {{ ref('dim_subsidiary') }}       sub ON s.subsidiary   = sub.subsidiary_code