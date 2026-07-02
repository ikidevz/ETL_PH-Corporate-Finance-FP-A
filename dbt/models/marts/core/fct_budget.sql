{{
    config(
        materialized='table'
    )
}}

SELECT
    {{
        dbt_utils.generate_surrogate_key([
            'b.fiscal_year',
            'b.fiscal_month',
            'b.gl_account',
            'b.cost_center',
            'b.subsidiary',
            'b.version'
        ])
    }} AS budget_key,

    b.fiscal_year,
    b.fiscal_month,

    a.account_key,
    cc.cost_center_key,
    sub.subsidiary_key,
    sc.scenario_key,

    b.budget_amount_php,
    b.version

FROM {{ ref('stg_budget') }} b

LEFT JOIN {{ ref('dim_account') }} a
    ON b.gl_account = a.gl_account_code

LEFT JOIN {{ ref('dim_cost_center') }} cc
    ON b.cost_center = cc.cost_center_code

LEFT JOIN {{ ref('dim_subsidiary') }} sub
    ON b.subsidiary = sub.subsidiary_code

LEFT JOIN {{ ref('dim_scenario') }} sc
    ON sc.scenario_type = 'Budget'
   AND sc.version = b.version