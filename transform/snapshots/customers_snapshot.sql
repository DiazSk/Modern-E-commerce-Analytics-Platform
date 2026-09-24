{% snapshot customers_snapshot %}

{{
    config(
        unique_key='customer_id',
        strategy='check',
        check_cols=['customer_segment']
    )
}}

-- The source customers table only holds each customer's *current* segment.
-- Every `dbt snapshot` run compares it to the last captured version and
-- closes/opens a version when customer_segment changes. This is where the
-- SCD Type 2 history for dim_customers comes from.
select * from {{ ref('stg_customers') }}

{% endsnapshot %}
