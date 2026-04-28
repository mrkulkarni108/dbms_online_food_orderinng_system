import logging
from pathlib import Path

import mysql.connector
from mysql.connector import pooling

from config.config import BaseConfig

LOGGER = logging.getLogger(__name__)

RESTAURANT_SEED_DATA = [
    ('Burger Hub', 'Fast Food', 'Pune', 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?q=80&w=600'),
    ('Pizza Palace', 'Italian', 'Pune', 'https://images.unsplash.com/photo-1513104890138-7c749659a591?q=80&w=600'),
    ('South Spice', 'South Indian', 'Pune', 'https://images.unsplash.com/photo-1610192244261-3f33de3f55e4?q=80&w=600'),
    ('North Delight', 'North Indian', 'Pune', 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?q=80&w=600'),
    ('Hyderabadi Biryani House', 'Hyderabadi', 'Pune', 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?q=80&w=600'),
]

FOOD_ITEM_SEED_DATA = [
    (1, 'Cheese Burger', 120, 'https://upload.wikimedia.org/wikipedia/commons/4/4d/Cheeseburger.jpg'),
    (1, 'Veg Burger', 90, 'https://images.unsplash.com/photo-1606755962773-d324e0a13086'),
    (2, 'Margherita Pizza', 200, 'https://images.unsplash.com/photo-1604382354936-07c5d9983bd3'),
    (2, 'Farmhouse Pizza', 250, 'https://images.unsplash.com/photo-1594007654729-407eedc4be65'),
    (3, 'Masala Dosa', 80, 'https://images.unsplash.com/photo-1668236543090-82eba5ee5976'),
    (3, 'Idli Sambar', 60, 'https://images.unsplash.com/photo-1630383249896-424e482df921'),
    (4, 'Butter Chicken', 220, 'https://images.unsplash.com/photo-1603894584373-5ac82b2ae398'),
    (4, 'Paneer Butter Masala', 180, 'https://images.unsplash.com/photo-1604908176997-125f25cc6f3d'),
    (5, 'Chicken Biryani', 250, 'https://images.unsplash.com/photo-1631515243349-e0cb75fb8d3a'),
    (5, 'Veg Biryani', 180, 'https://images.unsplash.com/photo-1633945274405-b6c8069047b0?auto=format&fit=crop&w=800&q=80'),
]

ORDER_STATUSES = ['pending', 'confirmed', 'preparing', 'out_for_delivery', 'delivered', 'cancelled']
PAYMENT_METHODS = ['upi', 'card', 'cash_on_delivery']
PAYMENT_STATUSES = ['pending', 'paid', 'failed']

_CONNECTION_POOL = None


class DatabaseServiceError(RuntimeError):
    """Raised when the database layer cannot safely fulfill a request."""


def get_db_config():
    return {
        'host': BaseConfig.DB_HOST,
        'port': BaseConfig.DB_PORT,
        'user': BaseConfig.DB_USER,
        'password': BaseConfig.DB_PASSWORD,
        'database': BaseConfig.DB_NAME,
        'autocommit': False,
    }


def get_connection_pool():
    global _CONNECTION_POOL
    if _CONNECTION_POOL is None:
        config = get_db_config()
        _CONNECTION_POOL = pooling.MySQLConnectionPool(
            pool_name=BaseConfig.DB_POOL_NAME,
            pool_size=BaseConfig.DB_POOL_SIZE,
            **config,
        )
        LOGGER.info('Created MySQL connection pool %s with size %s.', BaseConfig.DB_POOL_NAME, BaseConfig.DB_POOL_SIZE)
    return _CONNECTION_POOL


def get_db_connection():
    try:
        return get_connection_pool().get_connection()
    except mysql.connector.Error as exc:
        LOGGER.exception('Failed to obtain a database connection.')
        raise DatabaseServiceError('Database connection is unavailable.') from exc


def close_db_resources(conn=None, cursor=None):
    if cursor:
        cursor.close()
    if conn and conn.is_connected():
        conn.close()


def object_exists(cursor, object_type, table_name, object_name):
    query = (
        """
        select count(*)
        from information_schema.statistics
        where table_schema = database()
          and table_name = %s
          and index_name = %s
        """
        if object_type == 'index'
        else
        """
        select count(*)
        from information_schema.table_constraints
        where constraint_schema = database()
          and table_name = %s
          and constraint_name = %s
        """
    )
    cursor.execute(query, (table_name, object_name))
    return cursor.fetchone()[0] > 0


def add_column_if_missing(cursor, table_name, column_name, column_definition):
    cursor.execute(
        """
        select count(*)
        from information_schema.columns
        where table_schema = database()
          and table_name = %s
          and column_name = %s
        """,
        (table_name, column_name),
    )
    if cursor.fetchone()[0] == 0:
        LOGGER.info('Adding missing column %s.%s.', table_name, column_name)
        cursor.execute(f'alter table {table_name} add column {column_name} {column_definition}')


def add_index_if_missing(cursor, table_name, index_name, column_sql):
    if not object_exists(cursor, 'index', table_name, index_name):
        LOGGER.info('Creating index %s on %s.', index_name, table_name)
        cursor.execute(f'create index {index_name} on {table_name} ({column_sql})')


def add_foreign_key_if_safe(cursor, table_name, constraint_name, column_name, ref_table, ref_column='id'):
    if object_exists(cursor, 'constraint', table_name, constraint_name):
        return

    cursor.execute(
        f"""
        select count(*)
        from {table_name} child
        left join {ref_table} parent on child.{column_name} = parent.{ref_column}
        where child.{column_name} is not null and parent.{ref_column} is null
        """
    )
    if cursor.fetchone()[0] == 0:
        delete_rule = 'cascade' if table_name in {'order_items', 'payments', 'order_status_history', 'addresses'} else 'restrict'
        LOGGER.info('Creating foreign key %s on %s.', constraint_name, table_name)
        cursor.execute(
            f"""
            alter table {table_name}
            add constraint {constraint_name}
            foreign key ({column_name}) references {ref_table}({ref_column})
            on update cascade
            on delete {delete_rule}
            """
        )


def backfill_default_addresses(cursor):
    cursor.execute(
        """
        insert into addresses (user_id, label, address_line, city, is_default)
        select u.id, 'home', u.address, u.city, 1
        from users u
        where u.address is not null
          and trim(u.address) <> ''
          and not exists (
              select 1 from addresses a where a.user_id = u.id
          )
        """
    )


def create_views(cursor):
    cursor.execute(
        """
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
        left join payments p on p.order_id = o.id
        """
    )
    cursor.execute(
        """
        create or replace view restaurant_performance as
        select
            r.id as restaurant_id,
            r.name as restaurant_name,
            count(distinct o.id) as total_orders,
            coalesce(sum(o.total_amount), 0) as revenue,
            coalesce(avg(o.total_amount), 0) as avg_order_value
        from restaurants r
        left join orders o on o.restaurant_id = r.id and o.status <> 'cancelled'
        group by r.id, r.name
        """
    )


def create_programmability(cursor):
    cursor.execute('drop trigger if exists trg_update_order_total_after_insert')
    cursor.execute(
        """
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
        end
        """
    )

    cursor.execute('drop function if exists get_user_total_spent')
    cursor.execute(
        """
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
        end
        """
    )

    cursor.execute('drop procedure if exists place_order')
    cursor.execute(
        """
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
        end
        """
    )

    cursor.execute('drop procedure if exists loop_orders_cursor')
    cursor.execute(
        """
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
        end
        """
    )


def initialize_schema(cursor):
    cursor.execute(
        """
        create table if not exists users (
            id int auto_increment primary key,
            name varchar(255) not null,
            email varchar(255) not null unique,
            password varchar(255) not null,
            address text,
            city varchar(100) default 'Pune'
        )
        """
    )
    cursor.execute(
        """
        create table if not exists restaurants (
            id int auto_increment primary key,
            name varchar(255) not null,
            category varchar(100),
            city varchar(100),
            image_url text
        )
        """
    )
    cursor.execute(
        """
        create table if not exists food_items (
            id int auto_increment primary key,
            restaurant_id int,
            name varchar(255) not null,
            price int not null,
            image text
        )
        """
    )
    cursor.execute(
        """
        create table if not exists addresses (
            id int auto_increment primary key,
            user_id int not null,
            label varchar(100) not null,
            address_line text not null,
            city varchar(100) not null,
            is_default boolean default false,
            created_at datetime default current_timestamp
        )
        """
    )
    cursor.execute(
        """
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
        )
        """
    )
    cursor.execute(
        """
        create table if not exists order_items (
            id int auto_increment primary key,
            order_id int not null,
            food_item_id int not null,
            quantity int not null default 1,
            unit_price int not null,
            line_total int not null
        )
        """
    )
    cursor.execute(
        """
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
        )
        """
    )
    cursor.execute(
        """
        create table if not exists order_status_history (
            id int auto_increment primary key,
            order_id int not null,
            status varchar(50) not null,
            notes varchar(255),
            changed_at datetime default current_timestamp
        )
        """
    )


def seed_lookup_data(cursor):
    cursor.execute('select count(*) from restaurants')
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            'insert into restaurants (name, category, city, image_url) values (%s, %s, %s, %s)',
            RESTAURANT_SEED_DATA,
        )
        LOGGER.info('Seeded restaurants table with default records.')

    cursor.execute('select count(*) from food_items')
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            'insert into food_items (restaurant_id, name, price, image) values (%s, %s, %s, %s)',
            FOOD_ITEM_SEED_DATA,
        )
        LOGGER.info('Seeded food_items table with default records.')


def apply_constraints_and_indexes(cursor):
    add_column_if_missing(cursor, 'orders', 'address_id', 'int null')
    add_column_if_missing(cursor, 'orders', 'payment_method', "varchar(50) default 'cash_on_delivery'")
    add_column_if_missing(cursor, 'payments', 'failure_reason', 'varchar(255)')
    add_column_if_missing(cursor, 'payments', 'created_at', 'datetime default current_timestamp')

    add_foreign_key_if_safe(cursor, 'food_items', 'fk_food_items_restaurant', 'restaurant_id', 'restaurants')
    add_foreign_key_if_safe(cursor, 'addresses', 'fk_addresses_user', 'user_id', 'users')
    add_foreign_key_if_safe(cursor, 'orders', 'fk_orders_user', 'user_id', 'users')
    add_foreign_key_if_safe(cursor, 'orders', 'fk_orders_restaurant', 'restaurant_id', 'restaurants')
    add_foreign_key_if_safe(cursor, 'orders', 'fk_orders_address', 'address_id', 'addresses')
    add_foreign_key_if_safe(cursor, 'order_items', 'fk_order_items_order', 'order_id', 'orders')
    add_foreign_key_if_safe(cursor, 'order_items', 'fk_order_items_food_item', 'food_item_id', 'food_items')
    add_foreign_key_if_safe(cursor, 'payments', 'fk_payments_order', 'order_id', 'orders')
    add_foreign_key_if_safe(cursor, 'order_status_history', 'fk_order_status_history_order', 'order_id', 'orders')

    add_index_if_missing(cursor, 'users', 'idx_users_email', 'email')
    add_index_if_missing(cursor, 'food_items', 'idx_food_items_restaurant_price', 'restaurant_id, price')
    add_index_if_missing(cursor, 'orders', 'idx_orders_user_date', 'user_id, order_date')
    add_index_if_missing(cursor, 'order_items', 'idx_order_items_order_id', 'order_id')
    add_index_if_missing(cursor, 'payments', 'idx_payments_order_id', 'order_id')
    add_index_if_missing(cursor, 'addresses', 'idx_addresses_user_id', 'user_id')
    add_index_if_missing(cursor, 'order_status_history', 'idx_order_status_history_order_id', 'order_id, changed_at')


def bootstrap_sql_files():
    """Backfill the production SQL folder only when canonical files are missing."""

    base_dir = Path(BaseConfig.BASE_DIR)
    sql_dir = Path(BaseConfig.SQL_DIR)
    sql_dir.mkdir(parents=True, exist_ok=True)

    for filename in ('database.sql', 'queries.sql', 'seed_data.sql'):
        target = sql_dir / filename
        source = base_dir / filename
        if not target.exists() and source.exists():
            target.write_text(source.read_text(encoding='utf-8'), encoding='utf-8')


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        initialize_schema(cursor)
        seed_lookup_data(cursor)
        apply_constraints_and_indexes(cursor)
        backfill_default_addresses(cursor)
        create_views(cursor)
        create_programmability(cursor)
        conn.commit()
        bootstrap_sql_files()
        LOGGER.info('Database bootstrap completed successfully.')
    except mysql.connector.Error as exc:
        conn.rollback()
        LOGGER.exception('Database bootstrap failed.')
        raise DatabaseServiceError('Failed to initialize the database schema.') from exc
    finally:
        close_db_resources(conn, cursor)
