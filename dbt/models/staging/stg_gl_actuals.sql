WITH source AS (
    SELECT * FROM {{ source('bronze', 'raw_gl_actuals') }}
),
manual_adj AS (
    SELECT * FROM {{ source('bronze', 'raw_manual_adjustments') }}
),
combined AS (
    -- Actuals: ERP entries
    SELECT
        journal_id,
        posting_date,
        fiscal_year,
        fiscal_month,
        gl_account,
        account_type,
        cost_center,
        subsidiary,
        debit_amount,
        credit_amount,
        debit_amount - credit_amount    AS net_amount,
        currency,
        'ERP'                           AS entry_source,
        _loaded_at
    FROM source
    WHERE journal_id IS NOT NULL

    UNION ALL

    -- Actuals: manual adjustments from Excel uploads
    SELECT
        adjustment_id                   AS journal_id,
        posting_date,
        EXTRACT(YEAR FROM posting_date) AS fiscal_year,
        EXTRACT(MONTH FROM posting_date) AS fiscal_month,
        gl_account,
        NULL                            AS account_type,
        cost_center,
        subsidiary,
        CASE WHEN amount > 0 THEN amount ELSE 0 END AS debit_amount,
        CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END AS credit_amount,
        amount                          AS net_amount,
        'PHP'                           AS currency,
        'EXCEL_UPLOAD'                  AS entry_source,
        _loaded_at
    FROM manual_adj
)
SELECT * FROM combined