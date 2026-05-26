"""
SMARTFLOW — Authentication & Session Management
"""

import secrets
from datetime import datetime, timedelta
from flask import session

import database
import config


def hash_password(password: str) -> str:
    from werkzeug.security import generate_password_hash
    return generate_password_hash(password)


def verify_password(password: str, hashed: str) -> bool:
    from werkzeug.security import check_password_hash
    return check_password_hash(hashed, password)


def authenticate(username: str, password: str) -> tuple[dict | None, str | None]:
    """Authenticate and return (user_dict, failure_reason).
    failure_reason is None on success, or one of:
      'invalid', 'inactive', 'locked'
    """
    if not username or not password:
        return None, 'invalid'

    if database.is_login_blocked(username):
        return None, 'locked'

    user = database.get_user_by_username(username)
    if not user or not verify_password(password, user['password_hash']):
        database.record_login_attempt(username, False)
        return None, 'invalid'

    if user['status'] == 'inactive':
        return user, 'inactive'

    if user['status'] != 'active':
        return None, 'invalid'

    database.record_login_attempt(username, True)
    return user, None


def create_session(user: dict):
    """Create session, token, and load permissions into Flask session."""
    from flask import session as flask_session

    flask_session['user_id'] = user['id']
    flask_session['username'] = user['username']
    flask_session['full_name'] = user['full_name']
    flask_session['role'] = user['role_name']
    flask_session['must_change_password'] = bool(user['must_change_password'])

    token = secrets.token_hex(32)
    expires_at = (datetime.now() + timedelta(seconds=config.SESSION_TIMEOUT)).isoformat()
    database.create_user_session(user['id'], token, expires_at)
    flask_session['session_token'] = token

    perms = database.get_permissions_for_role(user['role_id'])
    flask_session['permissions'] = [f"{p['page']}:{p['action']}" for p in perms]

    database.update_last_login(user['id'])
    database.log_audit_event(
        user_id=user['id'],
        action='login',
        target='auth',
        details=f"User '{user['username']}' logged in successfully"
    )


def clear_session():
    """Clear session and delete token from database."""
    from flask import session as flask_session
    user_id = flask_session.get('user_id')
    username = flask_session.get('username')
    token = flask_session.get('session_token')

    if token:
        database.delete_session_by_token(token)

    if user_id:
        database.log_audit_event(
            user_id=user_id,
            action='logout',
            target='auth',
            details=f"User '{username}' logged out"
        )

    flask_session.clear()


def validate_current_session() -> bool:
    """Check that the current session is still valid (not expired, user still active)."""
    from flask import session as flask_session
    user_id = flask_session.get('user_id')
    token = flask_session.get('session_token')

    if not user_id or not token:
        return False

    db_sess = database.get_session_by_token(token)
    if not db_sess or db_sess['user_id'] != user_id:
        return False

    user = database.get_user_by_id(user_id)
    if not user or user['status'] != 'active':
        return False

    try:
        if datetime.fromisoformat(db_sess['expires_at']) < datetime.now():
            database.delete_session_by_token(token)
            return False
    except (ValueError, TypeError):
        return False

    new_expiry = (datetime.now() + timedelta(seconds=config.SESSION_TIMEOUT)).isoformat()
    database.update_session_expiry(token, new_expiry)
    return True


def get_current_user() -> dict | None:
    from flask import session as flask_session
    uid = flask_session.get('user_id')
    if not uid:
        return None
    return {
        'id': uid,
        'username': flask_session.get('username'),
        'full_name': flask_session.get('full_name'),
        'role': flask_session.get('role'),
        'must_change_password': flask_session.get('must_change_password', False),
    }


def is_authenticated() -> bool:
    from flask import session as flask_session
    return flask_session.get('user_id') is not None


def is_admin() -> bool:
    from flask import session as flask_session
    return flask_session.get('role') == 'admin'


def has_permission(page: str, action: str = 'view') -> bool:
    if not is_authenticated():
        return False
    if is_admin():
        return True
    from flask import session as flask_session
    perms = flask_session.get('permissions', [])
    return f"{page}:{action}" in perms


def validate_password_strength(password: str) -> list[str]:
    errors = []
    if len(password) < config.MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {config.MIN_PASSWORD_LENGTH} characters")
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")
    return errors
