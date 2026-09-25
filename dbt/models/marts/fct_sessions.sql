{{ config(materialized='incremental', incremental_strategy='merge', unique_key='user_session') }}

{%- set load_month = var('load_month') -%}
{%- if load_month is not none and not modules.re.match('^[0-9]{4}-(0[1-9]|1[0-2])$', load_month | string) -%}
    {{ exceptions.raise_compiler_error("load_month must be YYYY-MM, got '" ~ load_month ~ "'") }}
{%- endif %}

select *
from {{ ref('int_sessions') }}
{% if is_incremental() and load_month is not none %}
-- Recompute sessions starting from the day before the loaded month: a
-- session that began on that last day may have events in the new month.
where session_date >= date_sub(to_date('{{ load_month }}-01'), 1)
{% endif %}
