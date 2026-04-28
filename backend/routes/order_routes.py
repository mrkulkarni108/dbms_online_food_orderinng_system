import logging

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from services.order_service import (
    OrderPlacementError,
    PaymentFailure,
    advance_order_status,
    calculate_cart_totals,
    cancel_order,
    get_item_for_cart,
    get_order_tracking,
    get_restaurants_by_city,
    get_restaurant_with_menu,
    get_user_orders,
    place_order,
)
from utils.validation_helper import ValidationError

order_bp = Blueprint('orders', __name__)
LOGGER = logging.getLogger(__name__)


def _require_login():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return None


@order_bp.route('/restaurants')
def restaurants():
    login_redirect = _require_login()
    if login_redirect:
        return login_redirect

    city = session.get('user_city', 'Pune')
    restaurants_list = get_restaurants_by_city(city)
    return render_template('restaurants.html', restaurants=restaurants_list, city=city, name=session.get('user_name', 'User'))


@order_bp.route('/menu/<int:restaurant_id>')
def menu(restaurant_id):
    login_redirect = _require_login()
    if login_redirect:
        return login_redirect

    restaurant, food_items = get_restaurant_with_menu(restaurant_id)
    if not restaurant:
        flash('Restaurant not found.', 'error')
        return redirect(url_for('orders.restaurants'))

    return render_template('menu.html', restaurant=restaurant, food_items=food_items, name=session.get('user_name', 'User'))


@order_bp.route('/add_to_cart/<int:item_id>')
def add_to_cart(item_id):
    login_redirect = _require_login()
    if login_redirect:
        return login_redirect

    item = get_item_for_cart(item_id)
    if not item:
        flash('Food item not found.', 'error')
        return redirect(url_for('orders.restaurants'))

    cart = session.get('cart', [])
    if cart and cart[0]['restaurant_id'] != item['restaurant_id']:
        flash('Please order from one restaurant at a time.', 'error')
        return redirect(url_for('orders.cart'))

    for cart_item in cart:
        if cart_item['item_id'] == item['id']:
            cart_item['quantity'] += 1
            session['cart'] = cart
            session.modified = True
            flash(f"Updated quantity for {item['name']}.", 'success')
            LOGGER.info('User %s increased quantity for item %s.', session['user_id'], item['id'])
            return redirect(url_for('orders.cart'))

    cart.append({
        'item_id': item['id'],
        'restaurant_id': item['restaurant_id'],
        'restaurant_name': item['restaurant_name'],
        'name': item['name'],
        'price': item['price'],
        'quantity': 1,
    })
    session['cart'] = cart
    session.modified = True
    flash(f"Added {item['name']} to your cart.", 'success')
    LOGGER.info('User %s added item %s to cart.', session['user_id'], item['id'])
    return redirect(url_for('orders.cart'))


@order_bp.route('/cart')
def cart():
    login_redirect = _require_login()
    if login_redirect:
        return login_redirect

    cart_items = session.get('cart', [])
    return render_template('cart.html', cart_items=cart_items, totals=calculate_cart_totals(cart_items))


@order_bp.route('/remove_item/<int:item_id>')
def remove_item(item_id):
    login_redirect = _require_login()
    if login_redirect:
        return login_redirect

    if 'cart' in session:
        session['cart'] = [item for item in session['cart'] if item['item_id'] != item_id]
        session.modified = True
        flash('Item removed from cart.', 'success')
        LOGGER.info('User %s removed item %s from cart.', session['user_id'], item_id)
    return redirect(url_for('orders.cart'))


@order_bp.route('/place_order', methods=['POST'])
def place_order_route():
    login_redirect = _require_login()
    if login_redirect:
        return login_redirect

    try:
        order_data = place_order(
            session['user_id'],
            session.get('cart', []),
            request.form.get('payment_method', 'cash_on_delivery'),
            request.form.get('payment_outcome', 'success'),
        )
        session.pop('cart', None)
        LOGGER.info('User %s placed order %s.', session['user_id'], order_data['order_id'])
        return render_template('order_success.html', **order_data)
    except ValidationError as err:
        flash(str(err), 'error')
    except PaymentFailure as err:
        flash(str(err), 'error')
    except OrderPlacementError as err:
        flash(str(err), 'error')

    return redirect(url_for('orders.cart'))


@order_bp.route('/orders')
def my_orders():
    login_redirect = _require_login()
    if login_redirect:
        return login_redirect

    return render_template('my_orders.html', orders=get_user_orders(session['user_id']))


@order_bp.route('/orders/<int:order_id>')
def order_status(order_id):
    login_redirect = _require_login()
    if login_redirect:
        return login_redirect

    tracking = get_order_tracking(order_id, session['user_id'])
    if not tracking:
        flash('Order not found.', 'error')
        return redirect(url_for('orders.my_orders'))

    return render_template('order_status.html', tracking=tracking)


@order_bp.route('/orders/<int:order_id>/advance', methods=['POST'])
def advance_status(order_id):
    login_redirect = _require_login()
    if login_redirect:
        return login_redirect

    success, message = advance_order_status(order_id, session['user_id'])
    flash(message, 'success' if success else 'error')
    return redirect(url_for('orders.order_status', order_id=order_id))


@order_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
def cancel_status(order_id):
    login_redirect = _require_login()
    if login_redirect:
        return login_redirect

    success, message = cancel_order(order_id, session['user_id'])
    flash(message, 'success' if success else 'error')
    return redirect(url_for('orders.order_status', order_id=order_id))
