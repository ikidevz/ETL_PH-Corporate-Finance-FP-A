SELECT
    {{ dbt_utils.generate_surrogate_key(['employee_id']) }}        AS employee_key,
    employee_id,
    full_name,
    cc.cost_center_key,
    sub.subsidiary_key,
    job_level,
    monthly_base_php,
    monthly_base_php * 12                                          AS annualized_base_php,
    hire_date,
    termination_date,
    employment_status,
    CASE WHEN employment_status = 'ACTIVE' THEN TRUE ELSE FALSE END AS is_active
FROM {{ ref('stg_employee_roster') }}      e
LEFT JOIN {{ ref('dim_cost_center') }}     cc  ON e.cost_center = cc.cost_center_code
LEFT JOIN {{ ref('dim_subsidiary') }}      sub ON e.subsidiary  = sub.subsidiary_code