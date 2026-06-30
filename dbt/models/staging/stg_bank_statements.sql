SELECT
    bank_ref,
    txn_date,
    fiscal_year,
    fiscal_month,
    bank_account,
    subsidiary,
    bank_name,
    account_type,
    description,
    reference,
    debit_amount,
    credit_amount,
    net_amount,
    running_balance,
    currency,
    cf_category,
    _loaded_at
FROM {{ source('bronze', 'raw_bank_statements') }}
WHERE bank_ref IS NOT NULL
  AND txn_date IS NOT NULL