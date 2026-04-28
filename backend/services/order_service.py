import logging
import random

import mysql.connector

from services.database_service import ORDER_STATUSES, close_db_resources, get_db_connection
from services.user_service import get_default_address
from utils.validation_helper import validate_payment_method, validate_payment_outcome

LOGGER = logging.getLogger(__name__)
DELIVERY_AGENTS = ['Rahul', 'Amit', 'Suresh', 'Vikram']
NEXT_STATUS = {
    'pending': 'confirmed',
    'confirmed': 'preparing',
    'preparing': 'out_for_delivery',
    'out_for_delivery': 'delivered',
}


class OrderPlacementError(Exception):
    """Raised when the checkout flow cannot be completed safely."""


class PaymentFailure(OrderPlacementError):
    """Raised when the simulated payment step fails."""


def get_restaurants_by_city(city):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('select * from restaurants where lower(city) = lower(%s) order by name', (city,))
        return cursor.fetchall()
    finally:
        close_db_resources(conn, cursor)


def get_restaurant_with_menu(restaurant_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('select * from restaurants where id = %s', (restaurant_id,))
        restaurant = cursor.fetchone()
        cursor.execute('select * from food_items where restaurant_id = %s order by price, name', (restaurant_id,))
        return restaurant, cursor.fetchall()
    finally:
        close_db_resources(conn, cursor)


def get_item_for_cart(item_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            select fi.*, r.name as restaurant_name
            from food_items fi
            join restaurants r on fi.restaurant_id = r.id
            where fi.id = %s
            """,
            (item_id,),
        )
        return cursor.fetchone()
    finally:
        close_db_resources(conn, cursor)


def calculate_cart_totals(cart_items):
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    delivery_fee = 0 if subtotal >= 500 and subtotal > 0 else (40 if subtotal > 0 else 0)
    tax_amount = round(subtotal * 0.05)
    return {
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'tax_amount': tax_amount,
        'total_amount': subtotal + delivery_fee + tax_amount,
    }


def _get_cart_items_from_db(cursor, cart_items):
    item_ids = [item['item_id'] for item in cart_items]
    placeholders = ', '.join(['%s'] * len(item_ids))
    cursor.execute(
        f"""
        select fi.id, fi.restaurant_id, fi.name, fi.price, r.name as restaurant_name
        from food_items fi
        join restaurants r on fi.restaurant_id = r.id
        where fi.id in ({placeholders})
        order by fi.id
        """,
        tuple(item_ids),
    )
    return cursor.fetchall()


def place_order(user_id, cart_items, payment_method, payment_outcome='success'):
    if not cart_items:
        raise OrderPlacementError('Your cart is empty. Add items before placing an order.')

    payment_method = validate_payment_method(payment_method)
    payment_outcome = validate_payment_outcome(payment_outcome)
    default_address = get_default_address(user_id)
    if not default_address:
        raise OrderPlacementError('Please add a delivery address before placing an order.')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        quantity_map = {item['item_id']: item['quantity'] for item in cart_items}
        db_items = _get_cart_items_from_db(cursor, cart_items)
        if len(db_items) != len(cart_items):
            raise OrderPlacementError('One or more items in your cart are no longer available.')

        restaurant_ids = {item['restaurant_id'] for item in db_items}
        if len(restaurant_ids) != 1:
            raise OrderPlacementError('Please order from one restaurant at a time.')

        cart_snapshot = [
            {
                'item_id': item['id'],
                'name': item['name'],
                'price': item['price'],
                'quantity': quantity_map[item['id']],
                'restaurant_id': item['restaurant_id'],
                'restaurant_name': item['restaurant_name'],
            }
            for item in db_items
        ]
        totals = calculate_cart_totals(cart_snapshot)
        restaurant_id = db_items[0]['restaurant_id']
        restaurant_name = db_items[0]['restaurant_name']
        online_payment = payment_method in {'upi', 'card'}
        payment_status = 'paid' if online_payment else 'pending'

        cursor.execute('start transaction')
        LOGGER.info('Started transaction for user %s checkout.', user_id)
        cursor.execute(
            """
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
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                restaurant_id,
                default_address['id'],
                'pending',
                default_address['address_line'],
                default_address['city'],
                totals['subtotal'],
                totals['delivery_fee'],
                totals['tax_amount'],
                totals['total_amount'],
                payment_method,
            ),
        )
        order_id = cursor.lastrowid
        cursor.execute('savepoint after_order_header')

        order_item_rows = [
            (order_id, item['item_id'], item['quantity'], item['price'], item['price'] * item['quantity'])
            for item in cart_snapshot
        ]
        cursor.executemany(
            """
            insert into order_items (order_id, food_item_id, quantity, unit_price, line_total)
            values (%s, %s, %s, %s, %s)
            """,
            order_item_rows,
        )
        cursor.execute('savepoint after_order_items')

        if payment_outcome == 'db_failure':
            raise mysql.connector.Error('simulated database failure during payment step')

        failure_reason = None
        if online_payment and payment_outcome == 'failure':
            payment_status = 'failed'
            failure_reason = 'simulated payment failure'

        cursor.execute(
            """
            insert into payments (
                order_id,
                payment_method,
                payment_status,
                amount,
                paid_at,
                transaction_ref,
                failure_reason
            )
            values (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                order_id,
                payment_method,
                payment_status,
                totals['total_amount'],
                None,
                f'txn-{order_id:05d}',
                failure_reason,
            ),
        )
        cursor.execute(
            """
            update payments
            set paid_at = case when payment_status = 'paid' then now() else null end
            where order_id = %s
            """,
            (order_id,),
        )

        if payment_status == 'failed':
            cursor.execute('rollback to savepoint after_order_items')
            cursor.execute('rollback')
            LOGGER.warning('Rolled back order for user %s because payment failed.', user_id)
            raise PaymentFailure('Payment failed. The transaction was rolled back and no order was created.')

        cursor.execute(
            'insert into order_status_history (order_id, status, notes) values (%s, %s, %s)',
            (order_id, 'pending', f'order placed using {payment_method}'),
        )
        cursor.execute('select subtotal, delivery_fee, tax_amount, total_amount from orders where id = %s', (order_id,))
        final_totals = cursor.fetchone()
        cursor.execute('commit')
        LOGGER.info('Committed order %s for user %s.', order_id, user_id)

        return {
            'order_id': order_id,
            'restaurant_name': restaurant_name,
            'payment_method': payment_method,
            'payment_status': payment_status,
            'agent': random.choice(DELIVERY_AGENTS),
            'subtotal': final_totals['subtotal'],
            'delivery_fee': final_totals['delivery_fee'],
            'tax_amount': final_totals['tax_amount'],
            'total_amount': final_totals['total_amount'],
        }
    except PaymentFailure:
        raise
    except mysql.connector.Error as exc:
        try:
            cursor.execute('rollback')
        except mysql.connector.Error:
            conn.rollback()
        LOGGER.exception('Checkout failed for user %s.', user_id)
        raise OrderPlacementError('We could not place your order right now. Please try again.') from exc
    finally:
        close_db_resources(conn, cursor)


def get_user_orders(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            select order_id, restaurant_name, order_date, status, total_amount, payment_method, payment_status
            from user_order_summary
            where user_id = %s
            order by order_date desc, order_id desc
            """,
            (user_id,),
        )
        return cursor.fetchall()
    finally:
        close_db_resources(conn, cursor)


def get_order_tracking(order_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            select
                o.id,
                o.order_date,
                o.status,
                o.total_amount,
                o.subtotal,
                o.delivery_fee,
                o.tax_amount,
                o.delivery_address,
                o.city,
                o.payment_method,
                r.name as restaurant_name,
                p.payment_status
            from orders o
            join restaurants r on o.restaurant_id = r.id
            left join payments p on p.order_id = o.id
            where o.id = %s and o.user_id = %s
            """,
            (order_id, user_id),
        )
        order = cursor.fetchone()
        if not order:
            return None

        cursor.execute(
            """
            select f.name, oi.quantity, oi.unit_price, oi.line_total
            from order_items oi
            join food_items f on f.id = oi.food_item_id
            where oi.order_id = %s
            order by oi.id
            """,
            (order_id,),
        )
        items = cursor.fetchall()

        cursor.execute(
            """
            select status, notes, changed_at
            from order_status_history
            where order_id = %s
            order by changed_at asc, id asc
            """,
            (order_id,),
        )
        history = cursor.fetchall()

        return {'order': order, 'items': items, 'history': history, 'all_statuses': ORDER_STATUSES}
    finally:
        close_db_resources(conn, cursor)


def advance_order_status(order_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('select status, payment_method from orders where id = %s and user_id = %s', (order_id, user_id))
        order = cursor.fetchone()
        if not order:
            return False, 'Order not found.'
        if order['status'] in {'delivered', 'cancelled'}:
            return False, 'This order can no longer be updated.'

        new_status = NEXT_STATUS.get(order['status'])
        if not new_status:
            return False, 'No further status update is available.'

        cursor.execute('update orders set status = %s where id = %s', (new_status, order_id))
        cursor.execute(
            'insert into order_status_history (order_id, status, notes) values (%s, %s, %s)',
            (order_id, new_status, 'status updated from tracking page'),
        )
        if new_status == 'delivered' and order['payment_method'] == 'cash_on_delivery':
            cursor.execute(
                """
                update payments
                set payment_status = 'paid', paid_at = now(), failure_reason = null
                where order_id = %s
                """,
                (order_id,),
            )
        conn.commit()
        LOGGER.info('Advanced order %s to %s.', order_id, new_status)
        return True, f'Order status updated to {new_status}.'
    finally:
        close_db_resources(conn, cursor)


def cancel_order(order_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('select status from orders where id = %s and user_id = %s', (order_id, user_id))
        order = cursor.fetchone()
        if not order:
            return False, 'Order not found.'
        if order['status'] in {'delivered', 'cancelled'}:
            return False, 'Delivered or cancelled orders cannot be cancelled again.'

        cursor.execute('update orders set status = %s where id = %s', ('cancelled', order_id))
        cursor.execute(
            'update payments set payment_status = %s, failure_reason = %s where order_id = %s and payment_status = %s',
            ('failed', 'order cancelled by user', order_id, 'pending'),
        )
        cursor.execute(
            'insert into order_status_history (order_id, status, notes) values (%s, %s, %s)',
            (order_id, 'cancelled', 'order cancelled from tracking page'),
        )
        conn.commit()
        LOGGER.info('Cancelled order %s for user %s.', order_id, user_id)
        return True, 'Order cancelled successfully.'
    finally:
        close_db_resources(conn, cursor)
