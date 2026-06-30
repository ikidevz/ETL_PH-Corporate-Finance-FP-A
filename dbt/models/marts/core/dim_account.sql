SELECT
    {{ dbt_utils.generate_surrogate_key(['gl_account_code']) }}     AS account_key,
    gl_account_code,
    account_name,
    account_type,
    pnl_line,
    financial_statement,
    normal_balance,
    sort_order,
    is_active,
    CASE
        WHEN account_type = 'Revenue' THEN -1
        ELSE 1
    END                                                             AS sign_convention
FROM {{ ref('chart_of_accounts') }}
WHERE is_active = TRUE