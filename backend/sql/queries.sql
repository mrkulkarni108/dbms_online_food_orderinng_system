-- online food delivery system dbms query pack
-- all sql is lowercase and organized by syllabus topic

use food_delivery;

-- =========================================================
-- 1. ddl
-- =========================================================

-- purpose: create and evolve the production schema safely
-- syllabus topic: ddl
source backend/sql/database.sql;

-- =========================================================
-- 2. dml
-- =========================================================

-- purpose: load master data and sample users safely
-- syllabus topic: dml
source backend/sql/seed_data.sql;

-- newly added query: sample persisted order for demo use
insert into orders (user_id, restaurant_id, address_id, status, delivery_address, city, subtotal, delivery_fee, tax_amount, total_amount, payment_method)
select u.id, r.id, a.id, 'delivered', a.address_line, a.city, 210, 40, 11, 261, 'upi'
from users u
join addresses a on a.user_id = u.id and a.is_default = 1
join restaurants r on lower(r.name) = 'burger hub'
where lower(u.email) = 'akash@example.com'
  and not exists (
      select 1 from orders o where o.user_id = u.id and o.restaurant_id = r.id and o.total_amount = 261
  );

insert into order_items (order_id, food_item_id, quantity, unit_price, line_total)
select o.id, f.id, 1, 120, 120
from orders o
join users u on u.id = o.user_id
join restaurants r on r.id = o.restaurant_id
join food_items f on f.restaurant_id = r.id and lower(f.name) = 'cheese burger'
where lower(u.email) = 'akash@example.com'
  and o.total_amount = 261
  and not exists (
      select 1 from order_items oi where oi.order_id = o.id and oi.food_item_id = f.id
  );

insert into order_items (order_id, food_item_id, quantity, unit_price, line_total)
select o.id, f.id, 1, 90, 90
from orders o
join users u on u.id = o.user_id
join restaurants r on r.id = o.restaurant_id
join food_items f on f.restaurant_id = r.id and lower(f.name) = 'veg burger'
where lower(u.email) = 'akash@example.com'
  and o.total_amount = 261
  and not exists (
      select 1 from order_items oi where oi.order_id = o.id and oi.food_item_id = f.id
  );

insert into payments (order_id, payment_method, payment_status, amount, paid_at, transaction_ref)
select o.id, 'upi', 'paid', 261, now(), concat('seed-', o.id)
from orders o
join users u on u.id = o.user_id
where lower(u.email) = 'akash@example.com'
  and o.total_amount = 261
  and not exists (
      select 1 from payments p where p.order_id = o.id
  );

insert into order_status_history (order_id, status, notes)
select o.id, 'delivered', 'seeded delivered order'
from orders o
join users u on u.id = o.user_id
where lower(u.email) = 'akash@example.com'
  and o.total_amount = 261
  and not exists (
      select 1 from order_status_history h where h.order_id = o.id and h.status = 'delivered'
  );

-- =========================================================
-- 3. dql
-- =========================================================

select id, name, email, city from users;

select o.id as order_id, u.name as user_name, o.order_date, o.status, o.total_amount
from orders o
inner join users u on o.user_id = u.id;

select r.id as restaurant_id, r.name as restaurant_name, f.name as food_name, f.price
from restaurants r
left join food_items f on r.id = f.restaurant_id
order by r.id, f.price;

select o.id as order_id, u.name as user_name, r.name as restaurant_name, f.name as food_name,
       oi.quantity, oi.line_total, p.payment_status
from orders o
join users u on o.user_id = u.id
join restaurants r on o.restaurant_id = r.id
join order_items oi on o.id = oi.order_id
join food_items f on oi.food_item_id = f.id
left join payments p on o.id = p.order_id
order by o.id;

select coalesce(sum(total_amount), 0) as total_revenue
from orders
where status <> 'cancelled';

select u.name, coalesce(sum(o.total_amount), 0) as total_spent
from users u
left join orders o on o.user_id = u.id and o.status <> 'cancelled'
group by u.id, u.name
order by total_spent desc;

select r.id, r.name, count(o.id) as total_orders
from restaurants r
join orders o on r.id = o.restaurant_id
where o.status <> 'cancelled'
group by r.id, r.name
order by total_orders desc
limit 1;

select avg(total_amount) as avg_order_value
from orders
where status <> 'cancelled';

select u.id, u.name, count(o.id) as total_orders
from users u
join orders o on u.id = o.user_id
group by u.id, u.name
having count(o.id) > (
    select avg(order_count)
    from (
        select count(*) as order_count
        from orders
        group by user_id
    ) as user_order_counts
);

select r.id, r.name, avg(f.price) as avg_menu_price
from restaurants r
join food_items f on r.id = f.restaurant_id
group by r.id, r.name
having avg(f.price) > (
    select avg(price) from food_items
);

select * from user_order_summary order by order_date desc;
select * from restaurant_performance order by revenue desc;
select get_user_total_spent(1) as total_spent_for_user_1;

-- =========================================================
-- 4. dcl
-- =========================================================

create user if not exists 'food_reader'@'localhost' identified by 'reader123';
grant select on food_delivery.* to 'food_reader'@'localhost';
revoke select on food_delivery.payments from 'food_reader'@'localhost';

-- =========================================================
-- 5. tcl
-- =========================================================

start transaction;

insert into orders (user_id, restaurant_id, status, delivery_address, city, subtotal, delivery_fee, tax_amount, total_amount, payment_method)
select 1, 1, 'pending', 'demo transaction address', 'pune', 0, 40, 0, 0, 'upi'
from dual;

set @demo_order_id = last_insert_id();
savepoint after_order_header;

insert into order_items (order_id, food_item_id, quantity, unit_price, line_total)
values (@demo_order_id, 1, 1, 120, 120);

savepoint after_order_items;

insert into payments (order_id, payment_method, payment_status, amount, transaction_ref, failure_reason)
values (@demo_order_id, 'upi', 'failed', 166, concat('txn-demo-', @demo_order_id), 'simulated failure');

rollback to after_order_items;
rollback;

-- =========================================================
-- 6. views
-- =========================================================

select * from user_order_summary;
select * from restaurant_performance;

-- =========================================================
-- 7. indexes
-- =========================================================

show index from users;
show index from food_items;
show index from order_items;
show index from payments;

-- =========================================================
-- 8. pl/sql
-- implemented using mysql stored program syntax
-- =========================================================

call place_order(1, 1, 1, 2, 'cash_on_delivery');
call loop_orders_cursor();
