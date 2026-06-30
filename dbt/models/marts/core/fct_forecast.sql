{{
  config(
    materialized='table'    -- reloaded each close cycle when RF versions change
  )
}}

SELECT
    {{ dbt_utils.generate_surrogate_key(
        ['fiscal_year','fiscal_month','gl_account','cost_center','subsidiary','version']
    ) }}                                                    AS forecast_key,
    f.fiscal_year,
    f.fiscal_month,
    a.account_key,
    cc.cost_center_key,
    sub.subsidiary_key,
    sc.scenario_key,
    f.forecast_amount_php,
    f.version
FROM {{ ref('stg_forecast') }}              f
LEFT JOIN {{ ref('dim_account') }}          a   ON f.gl_account  = a.gl_account_code
LEFT JOIN {{ ref('dim_cost_center') }}      cc  ON f.cost_center = cc.cost_center_code
LEFT JOIN {{ ref('dim_subsidiary') }}       sub ON f.subsidiary  = sub.subsidiary_code
LEFT JOIN {{ ref('dim_scenario') }}         sc  ON sc.scenario_type = 'Revised Forecast'
                                                AND sc.version      = f.version