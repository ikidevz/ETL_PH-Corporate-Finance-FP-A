SELECT
    {{ dbt_utils.generate_surrogate_key(['subsidiary_code']) }}     AS subsidiary_key,
    subsidiary_code,
    subsidiary_name,
    industry,
    reporting_currency,
    CASE WHEN subsidiary_code = 'GROUP' THEN TRUE
         ELSE FALSE END                                             AS is_group_entity,
    is_active
FROM {{ ref('cost_center_hierarchy') }}
QUALIFY ROW_NUMBER() OVER (PARTITION BY subsidiary_code ORDER BY subsidiary_code) = 1