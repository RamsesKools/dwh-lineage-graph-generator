-- ============================================================
--  DUMMY LINEAGE STRUCTURE
--  This SQL creates placeholder tables/views to represent
--  your lineage graph structure.
-- ============================================================

-- ---------- SOURCE LAYER ----------
create table source.raw_customers as (
    select 'dummy_customer'::varchar as customer_id
);

create table source.raw_orders as (
    select 'dummy_order'::varchar as order_id
);

create table source.manual_adjustments as (
    select 'manual_adjustment'::varchar as adjustment_id
);

-- ---------- STAGING LAYER ----------
create view staging.stg_customers as (
    select *
    from source.raw_customers
);

create view staging.stg_orders as (
    select *
    from source.raw_orders
);

-- ---------- BASE LAYER ----------
create table base.base_customers as (
    select *
    from staging.stg_customers
    union all
    select *
    from source.manual_adjustments
);

create table base.base_orders as (
    select *
    from staging.stg_orders
);

-- ---------- DIMENSION LAYER ----------
create table dimension.dim_customer as (
    select *
    from base.base_customers
);

-- ---------- FACT LAYER ----------
create table fact.fact_orders as (
    select *
    from base.base_orders
    union all
    select *
    from dimension.dim_customer
);

-- ---------- EXPORT LAYER ----------
create view export.export_customer_orders as (
    select *
    from dimension.dim_customer
    union all
    select *
    from fact.fact_orders
);
