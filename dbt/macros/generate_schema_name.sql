{% macro generate_schema_name(custom_schema_name, node) %}
    {% if node.path.startswith('staging/') %}
        silver
    {% elif node.path.startswith('marts/') %}
        gold
    {% else %}
        {{ target.schema }}
    {% endif %}
{% endmacro %}