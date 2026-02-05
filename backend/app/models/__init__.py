# -*- coding: utf-8 -*-
"""
ACC Monitor - Database Models
"""
from app import db
from datetime import datetime


class Server(db.Model):
    """Server information model"""
    __tablename__ = 'servers'

    id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_cn = db.Column(db.String(50))
    ip = db.Column(db.String(15), nullable=False)
    os_type = db.Column(db.String(20), default='windows')
    status = db.Column(db.String(20), default='unknown')  # normal, warning, error, unknown
    cpu_usage = db.Column(db.Float, default=0)
    memory_usage = db.Column(db.Float, default=0)
    disk_usage = db.Column(db.Float, default=0)
    last_check = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    processes = db.relationship('Process', backref='server', lazy='dynamic')
    tablespaces = db.relationship('Tablespace', backref='server', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'name_cn': self.name_cn,
            'ip': self.ip,
            'os_type': self.os_type,
            'status': self.status,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'last_check': self.last_check.isoformat() if self.last_check else None
        }


class Process(db.Model):
    """Process status model"""
    __tablename__ = 'processes'

    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.String(10), db.ForeignKey('servers.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='unknown')  # running, stopped, warning
    pid = db.Column(db.Integer)
    cpu_usage = db.Column(db.Float, default=0)
    memory_mb = db.Column(db.Float, default=0)
    last_check = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'server_id': self.server_id,
            'name': self.name,
            'status': self.status,
            'pid': self.pid,
            'cpu': self.cpu_usage,
            'memory': self.memory_mb,
            'last_check': self.last_check.isoformat() if self.last_check else None
        }


class Tablespace(db.Model):
    """Oracle tablespace status model"""
    __tablename__ = 'tablespaces'

    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.String(10), db.ForeignKey('servers.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    total_mb = db.Column(db.Float, default=0)
    used_mb = db.Column(db.Float, default=0)
    used_percent = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='normal')  # normal, warning, critical
    last_check = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'server_id': self.server_id,
            'name': self.name,
            'total_mb': self.total_mb,
            'used_mb': self.used_mb,
            'used_percent': self.used_percent,
            'status': self.status,
            'last_check': self.last_check.isoformat() if self.last_check else None
        }


class Alert(db.Model):
    """Alert record model"""
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.String(10), db.ForeignKey('servers.id'))
    level = db.Column(db.String(20), nullable=False)  # critical, error, warning, info
    source = db.Column(db.String(50))  # process, database, log, container
    message = db.Column(db.Text, nullable=False)
    acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_by = db.Column(db.String(50))
    acknowledged_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'server_id': self.server_id,
            'level': self.level,
            'source': self.source,
            'message': self.message,
            'acknowledged': self.acknowledged,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class RestartLog(db.Model):
    """Process restart history model"""
    __tablename__ = 'restart_logs'

    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.String(10), db.ForeignKey('servers.id'), nullable=False)
    process_name = db.Column(db.String(100), nullable=False)
    reason = db.Column(db.Text)
    success = db.Column(db.Boolean, default=False)
    error_message = db.Column(db.Text)
    log_content = db.Column(db.Text)  # Related log content before restart
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'server_id': self.server_id,
            'process_name': self.process_name,
            'reason': self.reason,
            'success': self.success,
            'error_message': self.error_message,
            'log_content': self.log_content,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Container(db.Model):
    """Docker container status model (for EAI server)"""
    __tablename__ = 'containers'

    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.String(10), db.ForeignKey('servers.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    container_id = db.Column(db.String(64))
    status = db.Column(db.String(20), default='unknown')  # running, stopped, restarting
    cpu_percent = db.Column(db.Float, default=0)
    memory_usage = db.Column(db.Float, default=0)
    memory_limit = db.Column(db.Float, default=0)
    restart_count = db.Column(db.Integer, default=0)
    last_check = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'server_id': self.server_id,
            'name': self.name,
            'container_id': self.container_id,
            'status': self.status,
            'cpu_percent': self.cpu_percent,
            'memory_usage': self.memory_usage,
            'memory_limit': self.memory_limit,
            'restart_count': self.restart_count,
            'last_check': self.last_check.isoformat() if self.last_check else None
        }


class StationAlert(db.Model):
    """Station alert from device logs"""
    __tablename__ = 'station_alerts'

    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.String(10), db.ForeignKey('servers.id'), nullable=False)
    station_name = db.Column(db.String(100), nullable=False)
    device_name = db.Column(db.String(100))
    alert_type = db.Column(db.String(50))
    message = db.Column(db.Text, nullable=False)
    log_file = db.Column(db.String(255))
    occurred_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'server_id': self.server_id,
            'station_name': self.station_name,
            'device_name': self.device_name,
            'alert_type': self.alert_type,
            'message': self.message,
            'log_file': self.log_file,
            'occurred_at': self.occurred_at.isoformat() if self.occurred_at else None,
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }
