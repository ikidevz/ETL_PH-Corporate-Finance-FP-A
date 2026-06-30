SELECT
    employee_id,
    full_name,
    cost_center,
    subsidiary,
    job_level,
    monthly_base_php,
    hire_date,
    termination_date,
    employment_status,
    _loaded_at
FROM {{ source('bronze', 'raw_employee_roster') }}
WHERE employee_id IS NOT NULL