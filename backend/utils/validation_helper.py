import re
from html import escape

EMAIL_RE = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
SAFE_TEXT_RE = re.compile(r'^[A-Za-z0-9 .,#&()/-]{2,255}$')
PASSWORD_RE = re.compile(r'^(?=.*[A-Za-z])(?=.*\d).{8,128}$')
ALLOWED_PAYMENT_METHODS = {'upi', 'card', 'cash_on_delivery'}
ALLOWED_PAYMENT_OUTCOMES = {'success', 'failure', 'db_failure'}


class ValidationError(ValueError):
    """Raised when user supplied data fails validation."""


def _sanitize_text(value):
    return escape((value or '').strip())


def validate_email(email):
    email = _sanitize_text(email).lower()
    if not EMAIL_RE.match(email):
        raise ValidationError('Please enter a valid email address.')
    return email


def validate_name(name):
    name = _sanitize_text(name)
    if not SAFE_TEXT_RE.match(name):
        raise ValidationError('Name should contain 2 to 255 safe characters.')
    return name


def validate_city(city):
    city = _sanitize_text(city).title()
    if not SAFE_TEXT_RE.match(city):
        raise ValidationError('City should contain 2 to 255 safe characters.')
    return city


def validate_address(address):
    address = _sanitize_text(address)
    if len(address) < 5 or len(address) > 255:
        raise ValidationError('Address must be between 5 and 255 characters long.')
    return address


def validate_label(label):
    label = _sanitize_text(label).lower()
    if not SAFE_TEXT_RE.match(label):
        raise ValidationError('Address label contains unsupported characters.')
    return label


def validate_password(password, required=True):
    password = (password or '').strip()
    if not password and not required:
        return ''
    if not PASSWORD_RE.match(password):
        raise ValidationError('Password must be 8+ characters and include letters and numbers.')
    return password


def validate_payment_method(method):
    method = _sanitize_text(method).lower()
    if method not in ALLOWED_PAYMENT_METHODS:
        raise ValidationError('Unsupported payment method selected.')
    return method


def validate_payment_outcome(outcome):
    outcome = _sanitize_text(outcome).lower()
    if outcome not in ALLOWED_PAYMENT_OUTCOMES:
        raise ValidationError('Unsupported payment outcome selected.')
    return outcome
