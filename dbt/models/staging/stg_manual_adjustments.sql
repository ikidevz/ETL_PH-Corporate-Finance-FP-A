SELECT
    adjustment_id,
    posting_date,
    fiscal_year,
    fiscal_month,
    gl_account,
    cost_center,
    subsidiary,
    amount,
    adjustment_type,
    description,
    supporting_doc,
    prepared_by,
    approved_by,
    approved_date,
    notes,
    _loaded_at
FROM {{ source('bronze', 'raw_manual_adjustments') }}
WHERE adjustment_id IS NOT NULL
  AND adjustment_type IN ('ACCRUAL', 'REVERSAL', 'RECLASSIFICATION', 'CORRECTION')