import logging

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from services.user_service import authenticate_user, create_user
from utils.validation_helper import ValidationError

auth_bp = Blueprint('auth', __name__)
LOGGER = logging.getLogger(__name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('orders.restaurants'))

    if request.method == 'POST':
        try:
            email = request.form.get('email', '')
            user = authenticate_user(email, request.form.get('password', ''))
        except ValidationError as exc:
            flash(str(exc), 'error')
            return render_template('login.html')

        if user:
            session.clear()
            session.permanent = True
            session['user_id'] = user['id']
            session['user_name'] = user.get('name', 'User')
            session['user_city'] = user.get('city', 'Pune')
            session['address_id'] = user.get('address_id')
            flash('Welcome back! You are logged in.', 'success')
            return redirect(url_for('orders.restaurants'))

        LOGGER.warning('Rejected login request for %s.', email)
        flash('Invalid email or password.', 'error')

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('orders.restaurants'))

    if request.method == 'POST':
        try:
            success, message = create_user(
                request.form.get('name', ''),
                request.form.get('email', ''),
                request.form.get('password', ''),
                request.form.get('address', ''),
                request.form.get('city', '') or 'Pune',
                request.form.get('label', 'home') or 'home',
            )
        except ValidationError as exc:
            flash(str(exc), 'error')
            return render_template('register.html')

        flash(message, 'success' if success else 'error')
        if success:
            return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/logout')
def logout():
    user_id = session.get('user_id')
    session.clear()
    if user_id:
        LOGGER.info('User %s logged out.', user_id)
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))
