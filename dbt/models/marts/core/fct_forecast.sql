{{
    config(
        materialized='table'
    )
}}

SELECT
    {{
        dbt_utils.generate_surrogate_key([
            'f.fiscal_year',
            'f.fiscal_month',
            'f.gl_account',
            'f.cost_center',
            'f.subsidiary',
            'f.version'
        ])
    }} AS forecast_key,

    f.fiscal_year,
    f.fiscal_month,

    a.account_key,
    cc.cost_center_key,
    sub.subsidiary_key,
    sc.scenario_key,

    f.forecast_amount_php,
    f.version

FROM {{ ref('stg_forecast') }} f

LEFT JOIN {{ ref('dim_account') }} a
    ON f.gl_account = a.gl_account_code

LEFT JOIN {{ ref('dim_cost_center') }} cc
    ON f.cost_center = cc.cost_center_code

LEFT JOIN {{ ref('dim_subsidiary') }} sub
    ON f.subsidiary = sub.subsidiary_code

LEFT JOIN {{ ref('dim_scenario') }} sc
    ON sc.scenario_type = 'Revised Forecast'
   AND sc.version = f.version