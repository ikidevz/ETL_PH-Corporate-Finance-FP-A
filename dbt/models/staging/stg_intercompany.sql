SELECT
    intercompany_id,
    posting_date,
    fiscal_year,
    fiscal_month,
    from_subsidiary,
    to_subsidiary,
    ic_type,
    amount_php,
    description,
    _loaded_at
FROM {{ source('bronze', 'raw_intercompany') }}
WHERE intercompany_id IS NOT NULL
  AND from_subsidiary != to_subsidiary