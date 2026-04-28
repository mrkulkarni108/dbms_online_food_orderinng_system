import bcrypt
from werkzeug.security import check_password_hash

BCRYPT_PREFIXES = ('$2a$', '$2b$', '$2y$')
LEGACY_PREFIXES = ('pbkdf2:', 'scrypt:')


class PasswordHashError(RuntimeError):
    """Raised when password hashing or verification cannot be completed."""


def hash_password(password):
    try:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
    except Exception as exc:
        raise PasswordHashError('Failed to hash the password.') from exc


def needs_rehash(stored_password):
    return not stored_password.startswith(BCRYPT_PREFIXES)


def verify_password(stored_password, candidate_password):
    if stored_password.startswith(BCRYPT_PREFIXES):
        return bcrypt.checkpw(candidate_password.encode('utf-8'), stored_password.encode('utf-8'))
    if stored_password.startswith(LEGACY_PREFIXES):
        return check_password_hash(stored_password, candidate_password)
    return stored_password == candidate_password
