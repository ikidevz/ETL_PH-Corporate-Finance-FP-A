SELECT
    {{ dbt_utils.generate_surrogate_key(['scenario_type','version']) }} AS scenario_key,
    scenario_type,
    version,
    CASE scenario_type
        WHEN 'Actual'            THEN 1
        WHEN 'Budget'            THEN 2
        WHEN 'Forecast'          THEN 3
        WHEN 'Revised Forecast'  THEN 4
    END                                                             AS scenario_order,
    created_date
FROM (
    SELECT DISTINCT 'Actual'           AS scenario_type, 'ACTUAL'  AS version, MIN(_loaded_at)::DATE AS created_date FROM {{ ref('stg_gl_actuals') }} GROUP BY 1,2
    UNION ALL
    SELECT DISTINCT 'Budget'           AS scenario_type, version,   MIN(_loaded_at)::DATE FROM {{ ref('stg_budget') }} GROUP BY 1,2
    UNION ALL
    SELECT DISTINCT 'Revised Forecast' AS scenario_type, version,   MIN(_loaded_at)::DATE FROM {{ ref('stg_forecast') }} GROUP BY 1,2
)