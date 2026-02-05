# -*- coding: utf-8 -*-
"""
ACC Monitor - Configuration Settings
"""
import os
from datetime import timedelta

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


# Server configurations
# 排序顺序: 153、164、168、193、194、160、163、165
SERVERS = {
    '153': {
        'name': 'DP EPS Production',
        'name_cn': 'DP_EPS',
        'ip': '172.17.10.153',
        'os': 'windows',
        'acc_drive': 'E',  # 实际部署在E盘
        'log_path': 'E:\\iPlant.ACC\\Log',
        'processes': ['Oracle'],
        'services': [  # NSSM管理的服务
            {'service_name': 'ACC.Server', 'display_name': 'ACC.Server'},
            {'service_name': 'ACC.MQ', 'display_name': 'ACC.MQ'},
            {'service_name': 'ACC.PackServer', 'display_name': 'Pack.Server'},
            {'service_name': 'ACC.LogReader', 'display_name': 'ACC.LogReader'}
        ],
        'has_oracle': True,
        'sort_order': 1
    },
    '164': {
        'name': 'DP EPP Production',
        'name_cn': 'DP EPP',
        'ip': '172.17.10.164',
        'os': 'windows',
        'acc_drive': 'E',  # ACC部署盘符
        'log_path': 'E:\\ACC\\Log',
        'processes': ['Oracle'],  # 仅Oracle保留进程监控
        'services': [  # NSSM管理的服务
            {'service_name': 'ACC.Server', 'display_name': 'ACC.Server'},
            {'service_name': 'ACC.PackServer', 'display_name': 'Pack.Server'},
            {'service_name': 'ACC.MQ', 'display_name': 'ACC.MQ'}
        ],
        'has_oracle': True,
        'sort_order': 2
    },
    '168': {
        'name': 'SMT Line2 Production',
        'name_cn': 'SMT Line2',
        'ip': '172.17.10.168',
        'os': 'windows',
        'acc_drive': 'D',  # ACC部署盘符
        'log_path': 'D:\\ACC\\Log',
        'processes': ['Oracle'],
        'services': [  # NSSM管理的服务
            {'service_name': 'ACC.Server', 'display_name': 'ACC.Server'},
            {'service_name': 'ACC.MQ', 'display_name': 'ACC.MQ'},
            {'service_name': 'ACC.PackServer', 'display_name': 'Pack.Server'},
            {'service_name': 'ACC.LogReader', 'display_name': 'LogReader'}
        ],
        'has_oracle': True,
        'sort_order': 3
    },
    '193': {
        'name': 'C EPS Production',
        'name_cn': 'C_EPS',
        'ip': '172.17.10.193',
        'os': 'windows',
        'acc_drive': 'E',  # ACC部署盘符
        'log_path': 'E:\\ACC\\Log',
        'processes': ['Oracle'],
        'services': [  # NSSM管理的服务
            {'service_name': 'ACC.Server', 'display_name': 'ACC.Server'},
            {'service_name': 'ACC.MQ', 'display_name': 'ACC.MQ'},
            {'service_name': 'ACC.LogReader', 'display_name': 'LogReader'}
        ],
        'has_oracle': True,
        'sort_order': 4
    },
    '194': {
        'name': 'L EPP Production',
        'name_cn': 'L_EPP',
        'ip': '172.17.10.194',
        'os': 'windows',
        'acc_drive': 'E',  # ACC部署盘符
        'log_path': 'E:\\ACC\\ACC\\Log',
        'processes': ['Oracle'],
        'services': [  # NSSM管理的服务
            {'service_name': 'ACC.Server', 'display_name': 'ACC.Server'},
            {'service_name': 'ACC.MQ', 'display_name': 'ACC.MQ'},
            {'service_name': 'ACC.LogReader', 'display_name': 'LogReader'}
        ],
        'has_oracle': True,
        'sort_order': 5
    },
    '160': {
        'name': 'iPlant Server',
        'name_cn': 'iPlant',
        'ip': '172.17.10.160',
        'os': 'windows',
        'acc_drive': 'D',  # ACC部署盘符
        'log_path': 'D:\\iPlant\\Log',
        'processes': [],
        'services': [  # Windows服务（仅监控正常运行的服务）
            {'service_name': 'hulu-workorder', 'display_name': 'hulu-workorder'},
            {'service_name': 'iPlant.Features.WorkOrderSyncService', 'display_name': 'WorkOrderSync'},
            {'service_name': 'redis', 'display_name': 'Redis'}
        ],
        'has_oracle': False,
        'sort_order': 6
    },
    '163': {
        'name': 'EAI Server',
        'name_cn': 'EAI',
        'ip': '172.17.10.163',
        'os': 'linux',
        'log_path': '/var/eai/logs',
        'containers': ['hulu-eai'],  # 仅监控EAI容器
        'has_oracle': False,
        'sort_order': 7
    },
    '165': {
        'name': 'Common Services',
        'name_cn': 'SHARED',
        'ip': '172.17.10.165',
        'os': 'windows',
        'acc_drive': 'D',  # ACC部署盘符
        'log_path': 'D:\\ACC\\ACC\\Log',
        'processes': ['Oracle'],  # 保留Oracle进程检测
        'services': [  # Windows服务（通过服务名检测）
            {'service_name': 'DT.TechTeam_WorkOrderHelper', 'display_name': '工单小管家'},
            {'service_name': 'DT.TechTeam_Label_Inspection', 'display_name': '标签验证'},
            {'service_name': 'DT.TechTeam_C-EPS_Label_Print', 'display_name': 'C-EPS标签打印'},
            {'service_name': 'DT.TechTeam_EAI_Log_Monitor', 'display_name': 'EAI日志监听'},
            {'service_name': 'ACC.LogReader.Sync', 'display_name': 'LogReader同步'},
            {'service_name': 'ACC.LogReader.Async', 'display_name': 'LogReader异步'}
        ],
        'has_oracle': True,
        'oracle_type': 'factory',  # 工厂数据库，非产线数据库
        'sort_order': 8
    }
}

# Oracle database configurations
ORACLE_CONFIGS = {
    '164': {
        'host': '172.17.10.164',
        'port': 1521,
        'service_name': 'ACC_DB',
        'username': 'ACC',
        'tablespaces': ['ACC_DATA', 'USERS', 'SYSAUX', 'SYSTEM']
    },
    '168': {
        'host': '172.17.10.168',
        'port': 1521,
        'service_name': 'ACC_DB',
        'username': 'ACC',
        'tablespaces': ['ACC_DATA', 'USERS', 'SYSAUX', 'SYSTEM']
    },
    '153': {
        'host': '172.17.10.153',
        'port': 1521,
        'service_name': 'ACC_DB',
        'username': 'ACC',
        'tablespaces': ['ACC_DATA', 'USERS', 'SYSAUX', 'SYSTEM']
    },
    '193': {
        'host': '172.17.10.193',
        'port': 1521,
        'service_name': 'ACC_DB',
        'username': 'ACC',
        'tablespaces': ['ACC_DATA', 'USERS', 'SYSAUX', 'SYSTEM']
    },
    '194': {
        'host': '172.17.10.194',
        'port': 1521,
        'service_name': 'ACC_DB',
        'username': 'ACC',
        'tablespaces': ['ACC_DATA', 'USERS', 'SYSAUX', 'SYSTEM']
    },
    '165': {
        'host': '172.17.10.165',
        'port': 1521,
        'service_name': 'COMMON_DB',
        'username': 'ACC',
        'tablespaces': ['ACC_DATA', 'USERS', 'SYSAUX', 'SYSTEM']
    }
}

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
