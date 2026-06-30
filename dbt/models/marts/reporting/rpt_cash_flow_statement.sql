SELECT
    fiscal_year,
    fiscal_month,
    subsidiary_code,
    SUM(CASE WHEN cf_category = 'Operating'  THEN net_cash_php ELSE 0 END) AS operating_cf,
    SUM(CASE WHEN cf_category = 'Investing'  THEN net_cash_php ELSE 0 END) AS investing_cf,
    SUM(CASE WHEN cf_category = 'Financing'  THEN net_cash_php ELSE 0 END) AS financing_cf,
    SUM(net_cash_php)                                                       AS net_cash_movement
FROM {{ ref('fct_cash_flow') }}
JOIN {{ ref('dim_subsidiary') }} USING (subsidiary_key)
GROUP BY 1, 2, 3