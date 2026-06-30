SELECT
    invoice_id,
    doc_type,
    invoice_date,
    due_date,
    fiscal_year,
    fiscal_month,
    subsidiary,
    counterparty,
    amount_php,
    status,
    paid_date,
    DATEDIFF('day', invoice_date, COALESCE(paid_date, CURRENT_DATE())) AS days_outstanding,
    _loaded_at
FROM {{ source('bronze', 'raw_ap_ar') }}
WHERE invoice_id IS NOT NULL