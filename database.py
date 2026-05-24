"""
SMARTFLOW — SQLite Database Layer
All schema definitions, CRUD operations, and seed data.
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from contextlib import contextmanager

import config


def get_connection():
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─── Schema ────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    role_id INTEGER NOT NULL DEFAULT 2,
    status TEXT NOT NULL DEFAULT 'active',
    must_change_password INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    last_login_at TEXT,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,
    page TEXT NOT NULL,
    action TEXT NOT NULL DEFAULT 'view',
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    target TEXT,
    details TEXT,
    ip_address TEXT,
    timestamp TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS scenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    traffic_density TEXT DEFAULT 'Medium',
    pedestrian_density TEXT DEFAULT 'Medium',
    emergency_mode TEXT DEFAULT 'Disabled',
    lane_closure_config TEXT DEFAULT '{}',
    construction_config TEXT DEFAULT '{}',
    accident_config TEXT DEFAULT '{}',
    flooding_config TEXT DEFAULT '{}',
    created_by INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    is_official INTEGER DEFAULT 0,
    is_archived INTEGER DEFAULT 0,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS scenario_constraints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id INTEGER NOT NULL,
    constraint_type TEXT NOT NULL,
    config_json TEXT DEFAULT '{}',
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS simulation_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id INTEGER,
    user_id INTEGER,
    control_mode TEXT DEFAULT 'fixed-time',
    rl_model_id INTEGER,
    status TEXT DEFAULT 'idle',
    start_time TEXT,
    end_time TEXT,
    duration_seconds REAL DEFAULT 0,
    seed INTEGER,
    notes TEXT,
    is_baseline INTEGER DEFAULT 0,
    is_favorite INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS run_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    avg_waiting_time REAL DEFAULT 0,
    avg_queue_length REAL DEFAULT 0,
    max_queue_length INTEGER DEFAULT 0,
    throughput INTEGER DEFAULT 0,
    avg_pedestrian_delay REAL DEFAULT 0,
    emergency_clearance_time REAL DEFAULT 0,
    signal_phase_efficiency REAL DEFAULT 0,
    congestion_severity TEXT DEFAULT 'low',
    raw_metrics_json TEXT DEFAULT '{}',
    recorded_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (run_id) REFERENCES simulation_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS rl_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    algorithm TEXT DEFAULT 'DQN',
    version TEXT DEFAULT '1.0',
    checkpoint_path TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS rl_checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER NOT NULL,
    episode INTEGER DEFAULT 0,
    reward REAL DEFAULT 0,
    loss REAL DEFAULT 0,
    epsilon REAL DEFAULT 1.0,
    path TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (model_id) REFERENCES rl_models(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    message TEXT NOT NULL,
    type TEXT DEFAULT 'info',
    read INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS backups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    created_by INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    size_bytes INTEGER DEFAULT 0,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_users_role_id ON users(role_id);
CREATE INDEX IF NOT EXISTS idx_permissions_role_id ON permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(token);
CREATE INDEX IF NOT EXISTS idx_scenarios_created_by ON scenarios(created_by);
CREATE INDEX IF NOT EXISTS idx_scenario_constraints_scenario_id ON scenario_constraints(scenario_id);
CREATE INDEX IF NOT EXISTS idx_simulation_runs_scenario_id ON simulation_runs(scenario_id);
CREATE INDEX IF NOT EXISTS idx_simulation_runs_user_id ON simulation_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_simulation_runs_status ON simulation_runs(status);
CREATE INDEX IF NOT EXISTS idx_simulation_runs_created_at ON simulation_runs(created_at);
CREATE INDEX IF NOT EXISTS idx_run_metrics_run_id ON run_metrics(run_id);
CREATE INDEX IF NOT EXISTS idx_rl_checkpoints_model_id ON rl_checkpoints(model_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_backups_created_by ON backups(created_by);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
"""


def init_db():
    with get_db() as conn:
        conn.executescript(SCHEMA_SQL)


def seed_data():
    with get_db() as conn:
        # Seed roles if empty
        cursor = conn.execute("SELECT COUNT(*) FROM roles")
        if cursor.fetchone()[0] == 0:
            roles = [
                ('admin', 'Full platform access'),
                ('researcher', 'Run experiments and view results'),
                ('researcher_pending', 'Awaiting admin approval'),
                ('disabled', 'Account disabled'),
            ]
            conn.executemany(
                "INSERT INTO roles (name, description) VALUES (?, ?)", roles
            )

        # Seed users if empty
        cursor = conn.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            from auth import hash_password
            admin_hash = hash_password(config.DEFAULT_ADMIN_PASSWORD)
            user_hash = hash_password('Researcher2026!')

            seed_users = [
                ('System Administrator', 'admin',
                 'admin@smartflow.local', admin_hash, 1, 'active', 1),
                ('Lab Manager', 'admin2',
                 'admin2@smartflow.local', admin_hash, 1, 'active', 1),
                ('Juan dela Cruz', 'researcher',
                 'researcher@smartflow.local', user_hash, 2, 'active', 0),
                ('Maria Santos', 'researcher2',
                 'researcher2@smartflow.local', user_hash, 2, 'active', 0),
            ]
            conn.executemany(
                """INSERT INTO users (full_name, username, email, password_hash,
                   role_id, status, must_change_password)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                seed_users
            )

        # Seed system settings if empty
        cursor = conn.execute("SELECT COUNT(*) FROM system_settings")
        if cursor.fetchone()[0] == 0:
            settings = [
                ('registration_mode', config.REGISTRATION_MODE),
                ('session_timeout', str(config.SESSION_TIMEOUT)),
                ('min_password_length', str(config.MIN_PASSWORD_LENGTH)),
                ('app_name', config.APP_NAME),
                ('app_version', config.APP_VERSION),
                ('maintenance_mode', '0'),
                ('logging_level', 'INFO'),
            ]
            conn.executemany(
                "INSERT INTO system_settings (key, value) VALUES (?, ?)",
                settings
            )

        # Seed scenarios if empty
        cursor = conn.execute("SELECT COUNT(*) FROM scenarios")
        if cursor.fetchone()[0] == 0:
            scenarios = [
                ('Tagum City — Main Intersection',
                 'Primary high-volume intersection: Pioneer Ave & Apokon Rd',
                 'High', 'Medium', 'Disabled',
                 '{}', '{}', '{}', '{}', None, 1, 0),
                ('Tagum City — Secondary Route',
                 'Secondary route with moderate traffic volume',
                 'Medium', 'Low', 'Disabled',
                 '{}', '{}', '{}', '{}', None, 1, 0),
                ('Emergency Vehicle Scenario',
                 'High traffic with active emergency vehicle priority',
                 'Very High', 'Medium', 'Enabled (1 Ambulance)',
                 '{}', '{}', '{}', '{}', None, 1, 0),
                ('Lane Closure — Construction',
                 'Moderate traffic with lane closure due to road construction',
                 'Medium', 'Low', 'Disabled',
                 '{"enabled": true, "approach": "north", "lanes_closed": 1}',
                 '{"enabled": true, "approach": "north", "speed_reduction": 0.5}',
                 '{}', '{}', None, 1, 0),
            ]
            conn.executemany(
                """INSERT INTO scenarios (name, description, traffic_density,
                   pedestrian_density, emergency_mode,
                   lane_closure_config, construction_config, accident_config,
                   flooding_config, created_by, is_official, is_archived)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                scenarios
            )

            conn.execute(
                """INSERT INTO audit_logs (user_id, action, target, details)
                   VALUES (?, ?, ?, ?)""",
                (None, 'system', 'database', 'Database initialized with seed data')
            )

        # Seed permissions if empty
        cursor = conn.execute("SELECT COUNT(*) FROM permissions")
        if cursor.fetchone()[0] == 0:
            permissions = [
                # researcher permissions
                (2, 'dashboard', 'view'),
                (2, 'simulation', 'view'),
                (2, 'simulation', 'run'),
                (2, 'scenarios', 'view'),
                (2, 'scenarios', 'create'),
                (2, 'scenarios', 'edit'),
                (2, 'scenarios', 'delete'),
                (2, 'live-traffic', 'view'),
                (2, 'performance', 'view'),
                (2, 'ai-agent', 'view'),
                (2, 'runs-reports', 'view'),
                (2, 'runs-reports', 'export'),
                (2, 'profile', 'view'),
                (2, 'help', 'view'),
            ]
            conn.executemany(
                "INSERT INTO permissions (role_id, page, action) VALUES (?, ?, ?)",
                permissions
            )
            
        # Idempotent inserts for new researcher page permissions
        conn.execute(
            """INSERT INTO permissions (role_id, page, action)
               SELECT 2, 'profile', 'view'
               WHERE NOT EXISTS (
                   SELECT 1 FROM permissions WHERE role_id = 2 AND page = 'profile' AND action = 'view'
               )"""
        )
        conn.execute(
            """INSERT INTO permissions (role_id, page, action)
               SELECT 2, 'help', 'view'
               WHERE NOT EXISTS (
                   SELECT 1 FROM permissions WHERE role_id = 2 AND page = 'help' AND action = 'view'
               )"""
        )


# ─── New Helpers (Permissions, Sessions, Email) ────────────────────

def get_user_by_email(email):
    if not email:
        return None
    with get_db() as conn:
        cursor = conn.execute(
            """SELECT u.*, r.name as role_name FROM users u
               JOIN roles r ON u.role_id = r.id
               WHERE u.email = ?""",
            (email,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_permissions_for_role(role_id):
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT page, action FROM permissions WHERE role_id = ?",
            (role_id,)
        )
        return [dict(row) for row in cursor.fetchall()]


def check_user_permission(user_id, page, action):
    with get_db() as conn:
        cursor = conn.execute(
            """SELECT COUNT(*) FROM users u
               JOIN permissions p ON u.role_id = p.role_id
               WHERE u.id = ? AND p.page = ? AND p.action = ?""",
            (user_id, page, action)
        )
        return cursor.fetchone()[0] > 0


def create_user_session(user_id, token, expires_at):
    with get_db() as conn:
        conn.execute(
            """INSERT INTO user_sessions (user_id, token, expires_at)
               VALUES (?, ?, ?)""",
            (user_id, token, expires_at)
        )


def get_session_by_token(token):
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM user_sessions WHERE token = ?",
            (token,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def delete_session_by_token(token):
    with get_db() as conn:
        conn.execute("DELETE FROM user_sessions WHERE token = ?", (token,))


def update_session_expiry(token, expires_at):
    with get_db() as conn:
        conn.execute(
            "UPDATE user_sessions SET expires_at = ? WHERE token = ?",
            (expires_at, token)
        )


def delete_expired_sessions():
    with get_db() as conn:
        conn.execute(
            "DELETE FROM user_sessions WHERE datetime('now') > datetime(expires_at)"
        )


# ─── User CRUD ─────────────────────────────────────────────────────

def create_user(full_name, username, email, password_hash, role_id=2,
                status='active', must_change_password=0):
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO users (full_name, username, email, password_hash,
               role_id, status, must_change_password)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (full_name, username, email, password_hash, role_id, status,
             must_change_password)
        )
        return cursor.lastrowid


def get_user_by_username(username):
    with get_db() as conn:
        cursor = conn.execute(
            """SELECT u.*, r.name as role_name FROM users u
               JOIN roles r ON u.role_id = r.id
               WHERE u.username = ?""",
            (username,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id):
    with get_db() as conn:
        cursor = conn.execute(
            """SELECT u.*, r.name as role_name FROM users u
               JOIN roles r ON u.role_id = r.id
               WHERE u.id = ?""",
            (user_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def update_user(user_id, **kwargs):
    if not kwargs:
        return
    kwargs['updated_at'] = datetime.now().isoformat()
    set_clause = ', '.join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [user_id]
    with get_db() as conn:
        conn.execute(
            f"UPDATE users SET {set_clause} WHERE id = ?", values
        )


def update_last_login(user_id):
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET last_login_at = ? WHERE id = ?",
            (datetime.now().isoformat(), user_id)
        )


def list_users(role_id=None, status=None):
    with get_db() as conn:
        query = """SELECT u.*, r.name as role_name FROM users u
                   JOIN roles r ON u.role_id = r.id WHERE 1=1"""
        params = []
        if role_id is not None:
            query += " AND u.role_id = ?"
            params.append(role_id)
        if status is not None:
            query += " AND u.status = ?"
            params.append(status)
        query += " ORDER BY u.created_at DESC"
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def delete_user(user_id):
    with get_db() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))


def count_active_admins():
    with get_db() as conn:
        cursor = conn.execute(
            """SELECT COUNT(*) FROM users u
               JOIN roles r ON u.role_id = r.id
               WHERE r.name = 'admin' AND u.status = 'active'"""
        )
        return cursor.fetchone()[0]


# ─── Scenario CRUD ─────────────────────────────────────────────────

def create_scenario(name, description='', traffic_density='Medium',
                    pedestrian_density='Medium', emergency_mode='Disabled',
                    lane_closure_config='{}',
                    construction_config='{}', accident_config='{}',
                    flooding_config='{}', created_by=None,
                    is_official=0, is_archived=0):
    # Validate JSON configs
    for field_name, cfg in [('lane_closure_config', lane_closure_config),
                            ('construction_config', construction_config),
                            ('accident_config', accident_config),
                            ('flooding_config', flooding_config)]:
        try:
            if cfg:
                json.loads(cfg)
        except Exception as e:
            raise ValueError(f"Invalid JSON configuration in '{field_name}': {str(e)}")

    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO scenarios (name, description, traffic_density,
               pedestrian_density, emergency_mode,
               lane_closure_config, construction_config, accident_config,
               flooding_config, created_by, is_official, is_archived)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, description, traffic_density, pedestrian_density,
             emergency_mode, lane_closure_config,
             construction_config, accident_config, flooding_config,
             created_by, is_official, is_archived)
        )
        return cursor.lastrowid


def get_scenarios(include_archived=False, official_only=False):
    with get_db() as conn:
        query = "SELECT * FROM scenarios WHERE 1=1"
        params = []
        if not include_archived:
            query += " AND is_archived = 0"
        if official_only:
            query += " AND is_official = 1"
        query += " ORDER BY name"
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def get_scenario_by_id(scenario_id):
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM scenarios WHERE id = ?", (scenario_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def update_scenario(scenario_id, **kwargs):
    if not kwargs:
        return
    # Validate JSON configs if updated
    json_fields = ['lane_closure_config', 'construction_config', 'accident_config', 'flooding_config']
    for field in json_fields:
        if field in kwargs and kwargs[field]:
            try:
                json.loads(kwargs[field])
            except Exception as e:
                raise ValueError(f"Invalid JSON configuration in '{field}': {str(e)}")

    kwargs['updated_at'] = datetime.now().isoformat()
    set_clause = ', '.join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [scenario_id]
    with get_db() as conn:
        conn.execute(
            f"UPDATE scenarios SET {set_clause} WHERE id = ?", values
        )


def delete_scenario(scenario_id):
    with get_db() as conn:
        conn.execute("DELETE FROM scenarios WHERE id = ?", (scenario_id,))


# ─── Simulation Runs CRUD ──────────────────────────────────────────

def create_run(scenario_id, user_id, control_mode='fixed-time',
               rl_model_id=None, status='running', seed=None, notes=None):
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO simulation_runs (scenario_id, user_id, control_mode,
               rl_model_id, status, start_time, seed, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (scenario_id, user_id, control_mode, rl_model_id, status,
             datetime.now().isoformat(), seed, notes)
        )
        return cursor.lastrowid


def get_runs(scenario_id=None, user_id=None, control_mode=None,
             status=None, limit=100):
    with get_db() as conn:
        query = """SELECT r.*, s.name as scenario_name,
                   u.username as user_name
                   FROM simulation_runs r
                   LEFT JOIN scenarios s ON r.scenario_id = s.id
                   LEFT JOIN users u ON r.user_id = u.id
                   WHERE 1=1"""
        params = []
        if scenario_id is not None:
            query += " AND r.scenario_id = ?"
            params.append(scenario_id)
        if user_id is not None:
            query += " AND r.user_id = ?"
            params.append(user_id)
        if control_mode is not None:
            query += " AND r.control_mode = ?"
            params.append(control_mode)
        if status is not None:
            query += " AND r.status = ?"
            params.append(status)
        query += " ORDER BY r.created_at DESC LIMIT ?"
        params.append(limit)
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def get_run_by_id(run_id):
    with get_db() as conn:
        cursor = conn.execute(
            """SELECT r.*, s.name as scenario_name,
               u.username as user_name
               FROM simulation_runs r
               LEFT JOIN scenarios s ON r.scenario_id = s.id
               LEFT JOIN users u ON r.user_id = u.id
               WHERE r.id = ?""",
            (run_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def update_run(run_id, **kwargs):
    if not kwargs:
        return
    set_clause = ', '.join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [run_id]
    with get_db() as conn:
        conn.execute(
            f"UPDATE simulation_runs SET {set_clause} WHERE id = ?", values
        )


def save_run_metrics(run_id, avg_waiting_time=0, avg_queue_length=0,
                     max_queue_length=0, throughput=0,
                     avg_pedestrian_delay=0, emergency_clearance_time=0,
                     signal_phase_efficiency=0, congestion_severity='low',
                     raw_metrics_json='{}'):
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO run_metrics (run_id, avg_waiting_time,
               avg_queue_length, max_queue_length, throughput,
               avg_pedestrian_delay, emergency_clearance_time,
               signal_phase_efficiency, congestion_severity,
               raw_metrics_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (run_id, avg_waiting_time, avg_queue_length, max_queue_length,
             throughput, avg_pedestrian_delay, emergency_clearance_time,
             signal_phase_efficiency, congestion_severity, raw_metrics_json)
        )
        return cursor.lastrowid


def get_run_metrics(run_id):
    with get_db() as conn:
        cursor = conn.execute(
            """SELECT * FROM run_metrics WHERE run_id = ?
               ORDER BY recorded_at DESC LIMIT 1""",
            (run_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


# ─── Audit Logs ────────────────────────────────────────────────────

def log_audit_event(user_id=None, action='', target='', details=''):
    with get_db() as conn:
        conn.execute(
            """INSERT INTO audit_logs (user_id, action, target, details)
               VALUES (?, ?, ?, ?)""",
            (user_id, action, target, details)
        )


def get_audit_logs(user_id=None, action=None, limit=200):
    with get_db() as conn:
        query = """SELECT a.*, u.username FROM audit_logs a
                   LEFT JOIN users u ON a.user_id = u.id WHERE 1=1"""
        params = []
        if user_id is not None:
            query += " AND a.user_id = ?"
            params.append(user_id)
        if action is not None:
            query += " AND a.action = ?"
            params.append(action)
        query += " ORDER BY a.timestamp DESC LIMIT ?"
        params.append(limit)
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


# ─── System Settings ───────────────────────────────────────────────

def get_setting(key, default=None):
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT value FROM system_settings WHERE key = ?", (key,)
        )
        row = cursor.fetchone()
        return row['value'] if row else default


def set_setting(key, value):
    with get_db() as conn:
        conn.execute(
            """INSERT INTO system_settings (key, value, updated_at)
               VALUES (?, ?, datetime('now'))
               ON CONFLICT(key) DO UPDATE SET
               value = excluded.value, updated_at = datetime('now')""",
            (key, value)
        )


# ─── Notifications ─────────────────────────────────────────────────

def get_notifications(user_id, unread_only=False, limit=50):
    with get_db() as conn:
        query = "SELECT * FROM notifications WHERE user_id = ?"
        params = [user_id]
        if unread_only:
            query += " AND read = 0"
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def create_notification(user_id, message, notif_type='info'):
    with get_db() as conn:
        conn.execute(
            """INSERT INTO notifications (user_id, message, type)
               VALUES (?, ?, ?)""",
            (user_id, message, notif_type)
        )


def mark_notification_read(notif_id):
    with get_db() as conn:
        conn.execute(
            "UPDATE notifications SET read = 1 WHERE id = ?", (notif_id,)
        )


# ─── Roles ─────────────────────────────────────────────────────────

def get_roles():
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM roles ORDER BY id")
        return [dict(row) for row in cursor.fetchall()]


def get_role_by_name(name):
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM roles WHERE name = ?", (name,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


# ─── Constraints CRUD ──────────────────────────────────────────────

def get_scenario_constraints(scenario_id):
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM scenario_constraints WHERE scenario_id = ?",
            (scenario_id,)
        )
        return [dict(row) for row in cursor.fetchall()]


def save_scenario_constraint(scenario_id, constraint_type, config_json):
    # Validate JSON constraint config
    try:
        if config_json:
            json.loads(config_json)
    except Exception as e:
        raise ValueError(f"Invalid JSON configuration in constraint '{constraint_type}': {str(e)}")

    with get_db() as conn:
        conn.execute(
            """INSERT INTO scenario_constraints (scenario_id, constraint_type, config_json)
               VALUES (?, ?, ?)""",
            (scenario_id, constraint_type, config_json)
        )


def delete_scenario_constraints(scenario_id):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM scenario_constraints WHERE scenario_id = ?",
            (scenario_id,)
        )


def delete_run(run_id):
    with get_db() as conn:
        conn.execute("DELETE FROM simulation_runs WHERE id = ?", (run_id,))


# ─── Dynamic Permissions CRUD ──────────────────────────────────────

def update_role_permission(role_id, page, action, enabled):
    with get_db() as conn:
        if enabled:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM permissions WHERE role_id = ? AND page = ? AND action = ?",
                (role_id, page, action)
            )
            if cursor.fetchone()[0] == 0:
                conn.execute(
                    "INSERT INTO permissions (role_id, page, action) VALUES (?, ?, ?)",
                    (role_id, page, action)
                )
        else:
            conn.execute(
                "DELETE FROM permissions WHERE role_id = ? AND page = ? AND action = ?",
                (role_id, page, action)
            )


# ─── Backup & Restore CRUD ─────────────────────────────────────────

def list_backups():
    with get_db() as conn:
        cursor = conn.execute(
            """SELECT b.*, u.username FROM backups b
               LEFT JOIN users u ON b.created_by = u.id
               ORDER BY b.created_at DESC"""
        )
        return [dict(row) for row in cursor.fetchall()]


def create_backup(created_by):
    import shutil
    from datetime import datetime
    
    # Ensure backups directory exists
    backups_dir = os.path.join(os.path.dirname(config.DB_PATH), 'backups')
    os.makedirs(backups_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"smartflow_backup_{timestamp}.db"
    dest_path = os.path.join(backups_dir, filename)
    
    # Copy active DB file to backup path
    shutil.copy2(config.DB_PATH, dest_path)
    
    size_bytes = os.path.getsize(dest_path)
    
    with get_db() as conn:
        conn.execute(
            """INSERT INTO backups (filename, created_by, size_bytes)
               VALUES (?, ?, ?)""",
            (filename, created_by, size_bytes)
        )
    return filename


def restore_backup(backup_id):
    import shutil
    with get_db() as conn:
        cursor = conn.execute("SELECT filename FROM backups WHERE id = ?", (backup_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError("Backup not found")
        filename = row['filename']
        
    backups_dir = os.path.join(os.path.dirname(config.DB_PATH), 'backups')
    src_path = os.path.join(backups_dir, filename)
    
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Backup file '{filename}' does not exist on disk.")
        
    # Copy backup file over active DB
    shutil.copy2(src_path, config.DB_PATH)
    return filename


def delete_backup_from_db(backup_id):
    with get_db() as conn:
        cursor = conn.execute("SELECT filename FROM backups WHERE id = ?", (backup_id,))
        row = cursor.fetchone()
        if not row:
            return
        filename = row['filename']
        conn.execute("DELETE FROM backups WHERE id = ?", (backup_id,))
        
    backups_dir = os.path.join(os.path.dirname(config.DB_PATH), 'backups')
    file_path = os.path.join(backups_dir, filename)
    if os.path.exists(file_path):
        os.remove(file_path)


# ─── Login Attempt Tracking ──────────────────────────────────────

MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 300

def record_login_attempt(username: str, success: bool):
    with get_db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                timestamp TEXT DEFAULT (datetime('now')),
                success INTEGER NOT NULL DEFAULT 0
            )"""
        )
        conn.execute(
            "INSERT INTO login_attempts (username, success) VALUES (?, ?)",
            (username, 1 if success else 0)
        )


def is_login_blocked(username: str) -> bool:
    with get_db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                timestamp TEXT DEFAULT (datetime('now')),
                success INTEGER NOT NULL DEFAULT 0
            )"""
        )
        cutoff = (datetime.now() - timedelta(seconds=LOGIN_LOCKOUT_SECONDS)).isoformat()
        cursor = conn.execute(
            "SELECT COUNT(*) FROM login_attempts WHERE username = ? AND success = 0 AND timestamp >= ?",
            (username, cutoff)
        )
        failures = cursor.fetchone()[0]
        return failures >= MAX_LOGIN_ATTEMPTS
