SELECT
    {{ dbt_utils.generate_surrogate_key(['cost_center_code']) }}    AS cost_center_key,
    cost_center_code,
    cost_center_name,
    department,
    division,
    subsidiary_code,
    CASE WHEN cost_center_code = 'CC-SHARED-SVC' THEN TRUE
         ELSE FALSE END                                             AS is_shared_service,
    is_active
FROM {{ ref('cost_center_hierarchy') }}