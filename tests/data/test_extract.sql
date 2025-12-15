-- Test SQL file for extraction

create view analytics_schema.dim_customer as
select * from raw_data.customers;

create table datamart_schema.dim_customer as
select * from analytics_schema.dim_customer;

create view analytics_schema.fact_orders as
select
    o.order_id
    , c.customer_id
from raw_data.orders o
join analytics_schema.dim_customer c on o.customer_id = c.customer_id;
