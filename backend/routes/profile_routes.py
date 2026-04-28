import logging

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from services.user_service import add_address, get_default_address, get_user_profile, set_default_address, update_profile
from utils.validation_helper import ValidationError

profile_bp = Blueprint('profile', __name__)
LOGGER = logging.getLogger(__name__)


def _require_login():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return None


@profile_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    login_redirect = _require_login()
    if login_redirect:
        return login_redirect

    user_id = session['user_id']
    if request.method == 'POST':
        try:
            default_address_id = request.form.get('default_address_id')
            success, message = update_profile(
                user_id=user_id,
                name=request.form.get('name', ''),
                email=request.form.get('email', ''),
                password=request.form.get('new_password', '') or None,
                default_address_id=int(default_address_id) if default_address_id else None,
            )
        except ValidationError as exc:
            flash(str(exc), 'error')
            return redirect(url_for('profile.profile'))

        flash(message, 'success' if success else 'error')
        profile_data = get_user_profile(user_id)
        if success and profile_data:
            session['user_name'] = profile_data['user']['name']
            session['user_city'] = profile_data['user']['city']
            LOGGER.info('User %s updated their profile.', user_id)
        return redirect(url_for('profile.profile'))

    return render_template('profile.html', profile=get_user_profile(user_id))


@profile_bp.route('/profile/addresses', methods=['POST'])
def add_profile_address():
    login_redirect = _require_login()
    if login_redirect:
        return login_redirect

    label = request.form.get('label', 'other') or 'other'
    address_line = request.form.get('address_line', '')
    city = request.form.get('city', '') or 'Pune'

    try:
        make_default = request.form.get('make_default') == 'on'
        success, _ = add_address(session['user_id'], label, address_line, city, make_default)
    except ValidationError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('profile.profile'))
    if success:
        if make_default:
            default_address = get_default_address(session['user_id'])
            session['user_city'] = default_address['city'] if default_address else city
            session['address_id'] = default_address['id'] if default_address else None
        flash('Address added successfully.', 'success')
        LOGGER.info('User %s added a profile address.', session['user_id'])
    else:
        flash('Could not add the address.', 'error')
    return redirect(url_for('profile.profile'))


@profile_bp.route('/profile/addresses/<int:address_id>/default', methods=['POST'])
def make_default_address(address_id):
    login_redirect = _require_login()
    if login_redirect:
        return login_redirect

    if set_default_address(session['user_id'], address_id):
        default_address = get_default_address(session['user_id'])
        session['user_city'] = default_address['city'] if default_address else session.get('user_city', 'Pune')
        session['address_id'] = default_address['id'] if default_address else None
        flash('Default address updated.', 'success')
        LOGGER.info('User %s changed default address to %s.', session['user_id'], address_id)
    else:
        flash('Address could not be updated.', 'error')
    return redirect(url_for('profile.profile'))
