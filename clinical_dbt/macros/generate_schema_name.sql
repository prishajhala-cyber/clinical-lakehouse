{#
  Default dbt behavior names custom schemas "<target>_<custom>", like DEV_SILVER.
  This override uses the custom name as-is, so models land in SILVER.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}