-- Example lineage extraction demo

create view analytics.customer_summary as
select
    c.customer_id,
    c.customer_name,
    count(o.order_id) as total_orders
from raw.customers c
left join raw.orders o on c.customer_id = o.customer_id
group by c.customer_id, c.customer_name;

create table warehouse.dim_customer as
select
    cs.*,
    ca.address_line1
from analytics.customer_summary cs
join raw.customer_addresses ca on cs.customer_id = ca.customer_id;
