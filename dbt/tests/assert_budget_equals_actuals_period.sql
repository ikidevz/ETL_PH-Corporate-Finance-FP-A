SELECT
    g.fiscal_year,
    g.fiscal_month,
    COUNT(*) AS late_postings
FROM {{ ref('fct_gl_actuals') }} g
JOIN {{ ref('dim_date') }} d ON g.fiscal_year = d.fiscal_year
                             AND g.fiscal_month = d.fiscal_month
WHERE d.is_period_locked = TRUE
  AND g._loaded_at > (
      SELECT MAX(closed_date)
      FROM {{ source('control', 'period_lock') }}
      WHERE fiscal_year = d.fiscal_year
        AND fiscal_month = d.fiscal_month
  )
GROUP BY 1, 2
HAVING COUNT(*) > 0