import logging

import mysql.connector

from services.database_service import close_db_resources, get_db_connection
from utils.password_helper import hash_password, needs_rehash, verify_password
from utils.validation_helper import (
    ValidationError,
    validate_address,
    validate_city,
    validate_email,
    validate_label,
    validate_name,
    validate_password,
)

LOGGER = logging.getLogger(__name__)


def create_user(name, email, password, address_line, city, label='home'):
    name = validate_name(name)
    email = validate_email(email)
    password = validate_password(password)
    address_line = validate_address(address_line)
    city = validate_city(city)
    label = validate_label(label)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute('select id from users where lower(email) = lower(%s)', (email,))
        if cursor.fetchone():
            return False, 'An account with this email already exists.'

        password_hash = hash_password(password)
        cursor.execute(
            """
            insert into users (name, email, password, address, city)
            values (%s, %s, %s, %s, %s)
            """,
            (name, email, password_hash, address_line, city),
        )
        user_id = cursor.lastrowid
        cursor.execute(
            """
            insert into addresses (user_id, label, address_line, city, is_default)
            values (%s, %s, %s, %s, 1)
            """,
            (user_id, label, address_line, city),
        )
        conn.commit()
        LOGGER.info('User %s registered successfully.', email)
        return True, 'Account created successfully.'
    except mysql.connector.Error:
        conn.rollback()
        LOGGER.exception('Failed to create user %s.', email)
        raise
    finally:
        close_db_resources(conn, cursor)


def authenticate_user(email, password):
    email = validate_email(email)
    password = validate_password(password)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute('select * from users where lower(email) = lower(%s)', (email,))
        user = cursor.fetchone()
        if not user or not verify_password(user['password'], password):
            LOGGER.warning('Invalid login attempt for %s.', email)
            return None

        if needs_rehash(user['password']):
            cursor.execute(
                'update users set password = %s where id = %s',
                (hash_password(password), user['id']),
            )
            conn.commit()
            LOGGER.info('Upgraded password hash for user %s.', email)

        cursor.execute(
            """
            select id, label, address_line, city, is_default
            from addresses
            where user_id = %s and is_default = 1
            limit 1
            """,
            (user['id'],),
        )
        default_address = cursor.fetchone()
        if default_address:
            user['address'] = default_address['address_line']
            user['city'] = default_address['city']
            user['address_id'] = default_address['id']

        LOGGER.info('User %s logged in successfully.', email)
        return user
    finally:
        close_db_resources(conn, cursor)


def get_user_profile(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            select id, name, email, address, city
            from users
            where id = %s
            """,
            (user_id,),
        )
        user = cursor.fetchone()
        if not user:
            return None

        cursor.execute(
            """
            select id, label, address_line, city, is_default
            from addresses
            where user_id = %s
            order by is_default desc, created_at asc
            """,
            (user_id,),
        )
        addresses = cursor.fetchall()

        try:
            cursor.execute('select get_user_total_spent(%s) as total_spent', (user_id,))
            total_spent = cursor.fetchone()['total_spent']
        except mysql.connector.Error:
            cursor.execute(
                """
                select coalesce(sum(total_amount), 0) as total_spent
                from orders
                where user_id = %s and status <> 'cancelled'
                """,
                (user_id,),
            )
            total_spent = cursor.fetchone()['total_spent']

        cursor.execute('select count(*) as total_orders from orders where user_id = %s', (user_id,))
        total_orders = cursor.fetchone()['total_orders']

        return {
            'user': user,
            'addresses': addresses,
            'total_spent': total_spent,
            'total_orders': total_orders,
        }
    finally:
        close_db_resources(conn, cursor)


def update_profile(user_id, name, email, password=None, default_address_id=None):
    name = validate_name(name)
    email = validate_email(email)
    if password:
        password = validate_password(password, required=False)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute('select id from users where lower(email) = lower(%s) and id <> %s', (email, user_id))
        if cursor.fetchone():
            return False, 'Another account already uses this email.'

        updates = ['name = %s', 'email = %s']
        params = [name, email]

        default_address = None
        if password:
            updates.append('password = %s')
            params.append(hash_password(password))

        if default_address_id:
            cursor.execute(
                'select id, address_line, city from addresses where id = %s and user_id = %s',
                (default_address_id, user_id),
            )
            default_address = cursor.fetchone()
            if default_address:
                updates.extend(['address = %s', 'city = %s'])
                params.extend([default_address['address_line'], default_address['city']])
                cursor.execute('update addresses set is_default = 0 where user_id = %s', (user_id,))
                cursor.execute('update addresses set is_default = 1 where id = %s and user_id = %s', (default_address_id, user_id))

        params.append(user_id)
        cursor.execute(f"update users set {', '.join(updates)} where id = %s", tuple(params))
        conn.commit()
        LOGGER.info('User %s updated their profile.', user_id)
        return True, 'Profile updated successfully.'
    finally:
        close_db_resources(conn, cursor)


def add_address(user_id, label, address_line, city, make_default=False):
    label = validate_label(label)
    address_line = validate_address(address_line)
    city = validate_city(city)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if make_default:
            cursor.execute('update addresses set is_default = 0 where user_id = %s', (user_id,))

        cursor.execute(
            """
            insert into addresses (user_id, label, address_line, city, is_default)
            values (%s, %s, %s, %s, %s)
            """,
            (user_id, label, address_line, city, 1 if make_default else 0),
        )
        address_id = cursor.lastrowid

        if make_default:
            cursor.execute(
                'update users set address = %s, city = %s where id = %s',
                (address_line, city, user_id),
            )

        conn.commit()
        LOGGER.info('User %s added address %s.', user_id, address_id)
        return True, address_id
    finally:
        close_db_resources(conn, cursor)


def set_default_address(user_id, address_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute('select address_line, city from addresses where id = %s and user_id = %s', (address_id, user_id))
        address = cursor.fetchone()
        if not address:
            return False

        cursor.execute('update addresses set is_default = 0 where user_id = %s', (user_id,))
        cursor.execute('update addresses set is_default = 1 where id = %s and user_id = %s', (address_id, user_id))
        cursor.execute(
            'update users set address = %s, city = %s where id = %s',
            (address['address_line'], address['city'], user_id),
        )
        conn.commit()
        LOGGER.info('User %s set address %s as default.', user_id, address_id)
        return True
    finally:
        close_db_resources(conn, cursor)


def get_default_address(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            select id, label, address_line, city, is_default
            from addresses
            where user_id = %s and is_default = 1
            limit 1
            """,
            (user_id,),
        )
        address = cursor.fetchone()
        if not address:
            cursor.execute(
                """
                select id, label, address_line, city, is_default
                from addresses
                where user_id = %s
                order by created_at asc
                limit 1
                """,
                (user_id,),
            )
            address = cursor.fetchone()
        return address
    finally:
        close_db_resources(conn, cursor)
