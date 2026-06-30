SELECT
    d.date_day                                              AS date_key,
    d.year                                                  AS calendar_year,
    d.month_of_year                                         AS calendar_month,
    fc.fiscal_year,
    fc.fiscal_month,
    fc.fiscal_quarter,
    fc.period_name,
    COALESCE(pl.period_status, 'OPEN')                      AS period_status,
    CASE WHEN pl.period_status = 'CLOSED' THEN TRUE
         ELSE FALSE END                                     AS is_period_locked,
    pl.closed_date,
    pl.closed_by
FROM {{ ref('spine_date') }}     d
LEFT JOIN {{ ref('ph_fiscal_calendar') }} fc
    ON d.year = fc.calendar_year AND d.month_of_year = fc.calendar_month
LEFT JOIN {{ source('control', 'period_lock') }} pl
    ON fc.fiscal_year = pl.fiscal_year AND fc.fiscal_month = pl.fiscal_month