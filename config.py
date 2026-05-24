"""
SMARTFLOW — Configuration Constants
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = os.environ.get('SMARTFLOW_SECRET_KEY', 'smartflow-dev-secret-key-change-in-prod')

DB_PATH = os.path.join(BASE_DIR, 'data', 'smartflow.db')

SESSION_TIMEOUT = 3600

DEFAULT_ADMIN_USERNAME = 'admin'
DEFAULT_ADMIN_PASSWORD = 'SmartFlow2026!'

APP_NAME = 'SmartFlow Traffic'
APP_VERSION = '1.0.0'
APP_TAGLINE = 'AI-Driven Traffic Simulation & Decision Support'

REGISTRATION_MODE = 'approval-only'

MIN_PASSWORD_LENGTH = 8

LOGGING_LEVEL = 'INFO'
