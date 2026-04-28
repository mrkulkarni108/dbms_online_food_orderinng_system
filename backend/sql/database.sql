create database if not exists food_delivery;
use food_delivery;

create table if not exists users (
    id int auto_increment primary key,
    name varchar(255) not null,
    email varchar(255) not null unique,
    password varchar(255) not null,
    address text,
    city varchar(100) default 'pune'
);

create table if not exists restaurants (
    id int auto_increment primary key,
    name varchar(255) not null,
    category varchar(100),
    city varchar(100),
    image_url text
);

create table if not exists food_items (
    id int auto_increment primary key,
    restaurant_id int,
    name varchar(255) not null,
    price int not null,
    image text
);

create table if not exists addresses (
    id int auto_increment primary key,
    user_id int not null,
    label varchar(100) not null,
    address_line text not null,
    city varchar(100) not null,
    is_default boolean default false,
    created_at datetime default current_timestamp
);

create table if not exists orders (
    id int auto_increment primary key,
    user_id int not null,
    restaurant_id int not null,
    address_id int null,
    order_date datetime default current_timestamp,
    status varchar(50) default 'pending',
    delivery_address text,
    city varchar(100),
    subtotal int default 0,
    delivery_fee int default 40,
    tax_amount int default 0,
    total_amount int default 0,
    payment_method varchar(50) default 'cash_on_delivery'
);

create table if not exists order_items (
    id int auto_increment primary key,
    order_id int not null,
    food_item_id int not null,
    quantity int not null default 1,
    unit_price int not null,
    line_total int not null
);

create table if not exists payments (
    id int auto_increment primary key,
    order_id int not null,
    payment_method varchar(50) default 'cash_on_delivery',
    payment_status varchar(50) default 'pending',
    amount int not null,
    paid_at datetime null,
    transaction_ref varchar(100),
    failure_reason varchar(255),
    created_at datetime default current_timestamp
);

create table if not exists order_status_history (
    id int auto_increment primary key,
    order_id int not null,
    status varchar(50) not null,
    notes varchar(255),
    changed_at datetime default current_timestamp
);

set @sql = if(
    (select count(*) from information_schema.columns where table_schema = database() and table_name = 'orders' and column_name = 'address_id') = 0,
    'alter table orders add column address_id int null',
    'select 1'
);
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @sql = if(
    (select count(*) from information_schema.columns where table_schema = database() and table_name = 'orders' and column_name = 'payment_method') = 0,
    'alter table orders add column payment_method varchar(50) default ''cash_on_delivery''',
    'select 1'
);
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @sql = if(
    (select count(*) from information_schema.columns where table_schema = database() and table_name = 'payments' and column_name = 'failure_reason') = 0,
    'alter table payments add column failure_reason varchar(255)',
    'select 1'
);
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @sql = if(
    (select count(*) from information_schema.columns where table_schema = database() and table_name = 'payments' and column_name = 'created_at') = 0,
    'alter table payments add column created_at datetime default current_timestamp',
    'select 1'
);
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @sql = if(
    (select count(*) from information_schema.table_constraints where constraint_schema = database() and table_name = 'food_items' and constraint_name = 'fk_food_items_restaurant') = 0,
    'alter table food_items add constraint fk_food_items_restaurant foreign key (restaurant_id) references restaurants(id) on update cascade on delete restrict',
    'select 1'
);
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @sql = if(
    (select count(*) from information_schema.table_constraints where constraint_schema = database() and table_name = 'addresses' and constraint_name = 'fk_addresses_user') = 0,
    'alter table addresses add constraint fk_addresses_user foreign key (user_id) references users(id) on update cascade on delete cascade',
    'select 1'
);
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @sql = if(
    (select count(*) from information_schema.table_constraints where constraint_schema = database() and table_name = 'orders' and constraint_name = 'fk_orders_user') = 0,
    'alter table orders add constraint fk_orders_user foreign key (user_id) references users(id) on update cascade on delete restrict',
    'select 1'
);
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @sql = if(
    (select count(*) from information_schema.table_constraints where constraint_schema = database() and table_name = 'orders' and constraint_name = 'fk_orders_restaurant') = 0,
    'alter table orders add constraint fk_orders_restaurant foreign key (restaurant_id) references restaurants(id) on update cascade on delete restrict',
    'select 1'
);
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @sql = if(
    (select count(*) from information_schema.table_constraints where constraint_schema = database() and table_name = 'orders' and constraint_name = 'fk_orders_address') = 0,
    'alter table orders add constraint fk_orders_address foreign key (address_id) references addresses(id) on update cascade on delete restrict',
    'select 1'
);
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @sql = if(
    (select count(*) from information_schema.table_constraints where constraint_schema = database() and table_name = 'order_items' and constraint_name = 'fk_order_items_order') = 0,
    'alter table order_items add constraint fk_order_items_order foreign key (order_id) references orders(id) on update cascade on delete cascade',
    'select 1'
);
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @sql = if(
    (select count(*) from information_schema.table_constraints where constraint_schema = database() and table_name = 'order_items' and constraint_name = 'fk_order_items_food_item') = 0,
    'alter table order_items add constraint fk_order_items_food_item foreign key (food_item_id) references food_items(id) on update cascade on delete restrict',
    'select 1'
);
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @sql = if(
    (select count(*) from information_schema.table_constraints where constraint_schema = database() and table_name = 'payments' and constraint_name = 'fk_payments_order') = 0,
    'alter table payments add constraint fk_payments_order foreign key (order_id) references orders(id) on update cascade on delete cascade',
    'select 1'
);
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @sql = if(
    (select count(*) from information_schema.table_constraints where constraint_schema = database() and table_name = 'order_status_history' and constraint_name = 'fk_order_status_history_order') = 0,
    'alter table order_status_history add constraint fk_order_status_history_order foreign key (order_id) references orders(id) on update cascade on delete cascade',
    'select 1'
);
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @sql = if(
    (select count(*) from information_schema.statistics where table_schema = database() and table_name = 'users' and index_name = 'idx_users_email') = 0,
    'create index idx_users_email on users(email)',
    'select 1'
);
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @sql = if(
    (select count(*) from information_schema.statistics where table_schema = database() and table_name = 'food_items' and index_name = 'idx_food_items_restaurant_price') = 0,
    'create index idx_food_items_restaurant_price on food_items(restaurant_id, price)',
    'select 1'
);
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @sql = if(
    (select count(*) from information_schema.statistics where table_schema = database() and table_name = 'orders' and index_name = 'idx_orders_user_date') = 0,
    'create index idx_orders_user_date on orders(user_id, order_date)',
    'select 1'
);
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @sql = if(
    (select count(*) from information_schema.statistics where table_schema = database() and table_name = 'payments' and index_name = 'idx_payments_order_id') = 0,
    'create index idx_payments_order_id on payments(order_id)',
    'select 1'
);
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @sql = if(
    (select count(*) from information_schema.statistics where table_schema = database() and table_name = 'order_items' and index_name = 'idx_order_items_order_id') = 0,
    'create index idx_order_items_order_id on order_items(order_id)',
    'select 1'
);
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

set @sql = if(
    (select count(*) from information_schema.statistics where table_schema = database() and table_name = 'order_status_history' and index_name = 'idx_order_status_history_order_id') = 0,
    'create index idx_order_status_history_order_id on order_status_history(order_id, changed_at)',
    'select 1'
);
prepare stmt from @sql; execute stmt; deallocate prepare stmt;

create or replace view user_order_summary as
select
    o.id as order_id,
    o.user_id,
    u.name as user_name,
    r.name as restaurant_name,
    o.order_date,
    o.status,
    o.total_amount,
    p.payment_method,
    p.payment_status
from orders o
join users u on o.user_id = u.id
join restaurants r on o.restaurant_id = r.id
left join payments p on p.order_id = o.id;

create or replace view restaurant_performance as
select
    r.id as restaurant_id,
    r.name as restaurant_name,
    count(distinct o.id) as total_orders,
    coalesce(sum(o.total_amount), 0) as revenue,
    coalesce(avg(o.total_amount), 0) as avg_order_value
from restaurants r
left join orders o on o.restaurant_id = r.id and o.status <> 'cancelled'
group by r.id, r.name;

drop trigger if exists trg_update_order_total_after_insert;
drop function if exists get_user_total_spent;
drop procedure if exists place_order;
drop procedure if exists loop_orders_cursor;

delimiter $$

create trigger trg_update_order_total_after_insert
after insert on order_items
for each row
begin
    update orders
    set subtotal = (
            select coalesce(sum(line_total), 0)
            from order_items
            where order_id = new.order_id
        ),
        delivery_fee = case
            when (
                select coalesce(sum(line_total), 0)
                from order_items
                where order_id = new.order_id
            ) >= 500 then 0
            else 40
        end,
        tax_amount = round((
            select coalesce(sum(line_total), 0)
            from order_items
            where order_id = new.order_id
        ) * 0.05),
        total_amount = (
            select coalesce(sum(line_total), 0)
            from order_items
            where order_id = new.order_id
        )
        + case
            when (
                select coalesce(sum(line_total), 0)
                from order_items
                where order_id = new.order_id
            ) >= 500 then 0
            else 40
        end
        + round((
            select coalesce(sum(line_total), 0)
            from order_items
            where order_id = new.order_id
        ) * 0.05)
    where id = new.order_id;
end $$

create function get_user_total_spent(p_user_id int)
returns int
reads sql data
begin
    declare v_total int;

    select coalesce(sum(total_amount), 0) into v_total
    from orders
    where user_id = p_user_id
      and status <> 'cancelled';

    return coalesce(v_total, 0);
end $$

create procedure place_order(
    in p_user_id int,
    in p_restaurant_id int,
    in p_food_item_id int,
    in p_quantity int,
    in p_payment_method varchar(50)
)
begin
    declare v_price int;
    declare v_order_id int;
    declare v_total int;
    declare v_address_id int;
    declare v_address text;
    declare v_city varchar(100);

    start transaction;

    select price into v_price
    from food_items
    where id = p_food_item_id
      and restaurant_id = p_restaurant_id;

    select id, address_line, city into v_address_id, v_address, v_city
    from addresses
    where user_id = p_user_id and is_default = 1
    limit 1;

    insert into orders (
        user_id,
        restaurant_id,
        address_id,
        status,
        delivery_address,
        city,
        subtotal,
        delivery_fee,
        tax_amount,
        total_amount,
        payment_method
    ) values (
        p_user_id,
        p_restaurant_id,
        v_address_id,
        'pending',
        v_address,
        v_city,
        0,
        40,
        0,
        0,
        p_payment_method
    );

    set v_order_id = last_insert_id();

    insert into order_items (order_id, food_item_id, quantity, unit_price, line_total)
    values (v_order_id, p_food_item_id, p_quantity, v_price, v_price * p_quantity);

    select total_amount into v_total
    from orders
    where id = v_order_id;

    insert into payments (order_id, payment_method, payment_status, amount, paid_at, transaction_ref)
    values (
        v_order_id,
        p_payment_method,
        if(p_payment_method = 'cash_on_delivery', 'pending', 'paid'),
        v_total,
        if(p_payment_method = 'cash_on_delivery', null, now()),
        concat('txn-', v_order_id)
    );

    insert into order_status_history (order_id, status, notes)
    values (v_order_id, 'pending', 'order created by stored procedure');

    commit;
end $$

create procedure loop_orders_cursor()
begin
    declare done int default 0;
    declare v_order_id int;
    declare v_user_id int;
    declare v_total_amount int;

    declare order_cursor cursor for
        select id, user_id, total_amount
        from orders
        order by id;

    declare continue handler for not found set done = 1;

    open order_cursor;

    read_loop: loop
        fetch order_cursor into v_order_id, v_user_id, v_total_amount;
        if done = 1 then
            leave read_loop;
        end if;

        select concat('order id: ', v_order_id, ', user id: ', v_user_id, ', total: ', v_total_amount) as cursor_output;
    end loop;

    close order_cursor;
end $$

delimiter ;
