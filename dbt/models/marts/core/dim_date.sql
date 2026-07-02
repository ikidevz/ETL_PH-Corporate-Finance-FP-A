{{ config(materialized='table') }}

WITH date_spine AS (
    SELECT DATEADD(DAY, ROW_NUMBER() OVER (ORDER BY seq4()) - 1, '2025-01-01') AS date_day
    FROM TABLE(GENERATOR(ROWCOUNT => 730))
)

SELECT
    d.date_day AS date_key,

    YEAR(d.date_day)           AS calendar_year,
    MONTH(d.date_day)          AS calendar_month,
    DAY(d.date_day)            AS day_of_month,

    MONTHNAME(d.date_day)      AS month_name,
    DAYNAME(d.date_day)        AS day_name,

    QUARTER(d.date_day)        AS calendar_quarter,
    DAYOFWEEK(d.date_day)      AS day_of_week,
    DAYOFYEAR(d.date_day)      AS day_of_year,
    WEEKOFYEAR(d.date_day)     AS week_of_year,

    fc.fiscal_year,
    fc.fiscal_month,
    fc.fiscal_quarter,
    fc.period_name,

    COALESCE(pl.period_status, 'OPEN') AS period_status,

    CASE
        WHEN pl.period_status = 'CLOSED' THEN TRUE
        ELSE FALSE
    END AS is_period_locked,

    pl.closed_date,
    pl.closed_by

FROM date_spine d

LEFT JOIN {{ ref('ph_fiscal_calendar') }} fc
    ON YEAR(d.date_day) = fc.calendar_year
   AND MONTH(d.date_day) = fc.calendar_month

LEFT JOIN {{ source('control', 'period_lock') }} pl
    ON fc.fiscal_year = pl.fiscal_year
   AND fc.fiscal_month = pl.fiscal_month