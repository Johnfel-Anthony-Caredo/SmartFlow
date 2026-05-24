"""
SMARTFLOW — Authentication & Session Management
"""

import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import session, redirect
from werkzeug.security import generate_password_hash, check_password_hash

import database
import config


def hash_password(password: str) -> str:
    """Hash password using Werkzeug's default secure algorithm."""
    return generate_password_hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against its Werkzeug hash."""
    return check_password_hash(hashed, password)


def authenticate(username: str, password: str) -> dict | None:
    """Authenticate username and password against the database."""
    user = database.get_user_by_username(username)
    if not user:
        return None
    if user['status'] != 'active':
        return None
    if not verify_password(password, user['password_hash']):
        return None
    return user


def create_session(user: dict):
    """Create user session, token, and load permissions."""
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['full_name'] = user['full_name']
    session['role'] = user['role_name']
    session['must_change_password'] = bool(user['must_change_password'])
    
    # Generate and store session token in database for active session tracking
    token = secrets.token_hex(24)
    expires_at = (datetime.now() + timedelta(seconds=config.SESSION_TIMEOUT)).isoformat()
    database.create_user_session(user['id'], token, expires_at)
    session['session_token'] = token
    
    # Load and cache permissions in Flask session
    perms = database.get_permissions_for_role(user['role_id'])
    session['permissions'] = [f"{p['page']}:{p['action']}" for p in perms]
    
    database.update_last_login(user['id'])
    database.log_audit_event(
        user_id=user['id'],
        action='login',
        target='auth',
        details=f"User {user['username']} logged in"
    )


def clear_session():
    """Clear Flask session and delete token from database."""
    user_id = session.get('user_id')
    username = session.get('username')
    token = session.get('session_token')
    
    if token:
        try:
            database.delete_session_by_token(token)
        except Exception:
            pass
            
    if user_id:
        database.log_audit_event(
            user_id=user_id,
            action='logout',
            target='auth',
            details=f"User {username} logged out"
        )
    session.clear()


def validate_current_session() -> bool:
    """Active session timeout and status validation."""
    user_id = session.get('user_id')
    token = session.get('session_token')
    
    if not user_id or not token:
        return False
        
    db_sess = database.get_session_by_token(token)
    if not db_sess or db_sess['user_id'] != user_id:
        return False
        
    # Real-time check of user status (for immediate deactivation logout)
    user = database.get_user_by_id(user_id)
    if not user or user['status'] != 'active':
        return False
        
    # Check if session is expired
    try:
        expires_at = datetime.fromisoformat(db_sess['expires_at'])
        if datetime.now() > expires_at:
            database.delete_session_by_token(token)
            return False
    except Exception:
        return False
        
    # Sliding window: update expiration time
    new_expiry = (datetime.now() + timedelta(seconds=config.SESSION_TIMEOUT)).isoformat()
    database.update_session_expiry(token, new_expiry)
    return True


def get_current_user() -> dict | None:
    """Retrieve currently logged in user info from Flask session."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return {
        'id': user_id,
        'username': session.get('username'),
        'full_name': session.get('full_name'),
        'role': session.get('role'),
        'must_change_password': session.get('must_change_password', False),
    }


def is_authenticated() -> bool:
    """Check if a user is authenticated."""
    return session.get('user_id') is not None


def is_admin() -> bool:
    """Check if the current user has the admin role."""
    return session.get('role') == 'admin'


def has_permission(page: str, action: str = 'view') -> bool:
    """Verify if the current user session has specific page/action permissions."""
    if not is_authenticated():
        return False
    # Admins bypass all permission checks
    if is_admin():
        return True
    perms = session.get('permissions', [])
    return f"{page}:{action}" in perms


def validate_password_strength(password: str) -> list[str]:
    """Validate that the password meets security strength requirements."""
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

