-- Test SQL file for extraction

create view lsbi_dwh_eah.dim_customer as
select * from raw_data.customers;

create table lsbi_dm_eah.dim_customer as
select * from lsbi_dwh_eah.dim_customer;

create view lsbi_dwh_eah.fact_orders as
select
    o.order_id
    , c.customer_id
from raw_data.orders o
join lsbi_dwh_eah.dim_customer c on o.customer_id = c.customer_id;
