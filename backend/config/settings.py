# -*- coding: utf-8 -*-
"""
ACC Monitor - Configuration Settings
"""
import os
import json
from datetime import timedelta

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# JSON config file path
SERVERS_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'servers.json')


def load_servers_from_json():
    """Load server configurations from JSON file"""
    try:
        with open(SERVERS_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('servers', {}), data.get('oracle_configs', {})
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[Warning] Failed to load servers.json: {e}, using defaults")
        return {}, {}


def save_servers_to_json(servers, oracle_configs=None):
    """Save server configurations to JSON file"""
    try:
        # Load existing data to preserve oracle_configs if not provided
        existing_data = {}
        if os.path.exists(SERVERS_JSON_PATH):
            with open(SERVERS_JSON_PATH, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)

        data = {
            'servers': servers,
            'oracle_configs': oracle_configs if oracle_configs is not None else existing_data.get('oracle_configs', {})
        }
        with open(SERVERS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[Error] Failed to save servers.json: {e}")
        return False


def reload_servers():
    """Reload SERVERS and ORACLE_CONFIGS from JSON file"""
    global SERVERS, ORACLE_CONFIGS
    SERVERS, ORACLE_CONFIGS = load_servers_from_json()
    return SERVERS, ORACLE_CONFIGS


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'acc-monitor-secret-key-2026')

    # SQLite for local storage
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(BASE_DIR, "data", "acc_monitor.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # WebSocket
    SOCKETIO_ASYNC_MODE = 'eventlet'

    # Monitoring intervals (seconds)
    PROCESS_CHECK_INTERVAL = 30
    DATABASE_CHECK_INTERVAL = 300  # 5 minutes
    LOG_SCAN_INTERVAL = 60

    # Alert thresholds
    TABLESPACE_WARNING_THRESHOLD = 85
    TABLESPACE_CRITICAL_THRESHOLD = 95
    DISK_WARNING_THRESHOLD = 80
    DISK_CRITICAL_THRESHOLD = 90

    # Auto restart settings
    AUTO_RESTART_ENABLED = True
    RESTART_COOLDOWN_SECONDS = 300  # 5 minutes between restarts

    # Reconnection detection settings
    AGENT_OFFLINE_TIMEOUT = 30  # seconds before agent considered offline
    OFFLINE_PROBE_INTERVAL = 15  # seconds between offline server probes
    PROBE_RETRY_BACKOFF = True  # enable exponential backoff for probe failures
    MAX_PROBE_BACKOFF = 240  # max backoff interval in seconds (4 minutes)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


# Server configurations - loaded from JSON file
# 排序顺序: 153、164、168、193、194、160、163、165
SERVERS, ORACLE_CONFIGS = load_servers_from_json()

# SSH credentials (using key-based authentication)
SSH_CREDENTIALS = {
    'windows': {
        'username': os.environ.get('SSH_WIN_USER', 'administrator'),
        'key_file': os.environ.get('SSH_KEY_FILE', os.path.expanduser('~/.ssh/id_rsa'))
    },
    'linux': {
        'username': os.environ.get('SSH_LINUX_USER', 'root'),
        'key_file': os.environ.get('SSH_KEY_FILE', os.path.expanduser('~/.ssh/id_rsa'))
    }
}

# Server-specific SSH port configurations
SSH_PORTS = {
    '163': 2200,  # Linux server uses port 2200
    # Other servers use default port 22
}

# Alert keywords for log monitoring
LOG_ALERT_KEYWORDS = {
    'critical': ['ORA-00600', 'ORA-04031', 'System.OutOfMemoryException'],
    'error': ['Exception', 'Error', 'ORA-', 'Failed'],
    'warning': ['Warning', 'Connection refused', 'Timeout', 'Retry']
}

# Process restart commands
PROCESS_RESTART_COMMANDS = {
    'ACC.Server': {
        'windows': 'net start "ACC Server"',
        'stop': 'net stop "ACC Server"'
    },
    'ACC.MQ': {
        'windows': 'net start "ACC MQ"',
        'stop': 'net stop "ACC MQ"'
    },
    'Pack.Server': {
        'windows': 'net start "Pack Server"',
        'stop': 'net stop "Pack Server"'
    }
}

# Get configuration by environment
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
