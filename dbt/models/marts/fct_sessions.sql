-- depends_on: {{ ref('stg_events') }}
{{ config(materialized='incremental', incremental_strategy='merge', unique_key='user_session') }}

{%- set load_month = var('load_month') -%}
{%- if load_month is not none and not modules.re.match('^[0-9]{4}-(0[1-9]|1[0-2])$', load_month | string) -%}
    {{ exceptions.raise_compiler_error("load_month must be YYYY-MM, got '" ~ load_month ~ "'") }}
{%- endif %}

select *
from {{ ref('int_sessions') }}
{% if is_incremental() and load_month is not none %}
-- REES46 session IDs can span weeks (up to ~60 days in the real data), so
-- recompute every session that has any event in the loaded month, whatever
-- day it started. Correct for any session length and any load order.
where user_session in (
    select user_session
    from {{ ref('stg_events') }}
    where event_date >= to_date('{{ load_month }}-01')
      and event_date < add_months(to_date('{{ load_month }}-01'), 1)
)
{% endif %}
