# -*- coding: utf-8 -*-
"""
Oracle Ops - Database Models for Oracle Database Operations Monitoring
Stores data reported by execution agents on each server.
"""
import json
from app import db
from datetime import datetime


class OpsTablespaceData(db.Model):
    """Tablespace collection data reported by execution agents"""
    __tablename__ = 'ops_tablespace_data'

    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.String(20), nullable=False, index=True)
    server_name = db.Column(db.String(50))
    tablespace_name = db.Column(db.String(100), nullable=False)
    used_mb = db.Column(db.Float)
    max_mb = db.Column(db.Float)
    usage_pct = db.Column(db.Float)
    # Current active file data for business tablespaces (ACC_DATA, IPLANT_*_DATA)
    # For business tablespaces with multiple data files, only the latest file (max file_id)
    # is the active one. Historical files being full is normal and expected.
    current_file_pct = db.Column(db.Float, nullable=True)
    current_file_used_mb = db.Column(db.Float, nullable=True)
    current_file_max_mb = db.Column(db.Float, nullable=True)
    collected_at = db.Column(db.DateTime, index=True)
    reported_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        result = {
            'id': self.id,
            'server_id': self.server_id,
            'server_name': self.server_name,
            'tablespace_name': self.tablespace_name,
            'used_mb': self.used_mb,
            'max_mb': self.max_mb,
            'usage_pct': self.usage_pct,
            'collected_at': self.collected_at.isoformat() if self.collected_at else None,
            'reported_at': self.reported_at.isoformat() if self.reported_at else None
        }
        # Include current_file data if available (business tablespaces)
        if self.current_file_pct is not None:
            result['current_file_pct'] = self.current_file_pct
            result['current_file_used_mb'] = self.current_file_used_mb
            result['current_file_max_mb'] = self.current_file_max_mb
        return result


class OpsBackupRecord(db.Model):
    """Backup execution records reported by execution agents"""
    __tablename__ = 'ops_backup_records'

    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.String(20), nullable=False, index=True)
    server_name = db.Column(db.String(50))
    backup_type = db.Column(db.String(20))  # audit, data
    status = db.Column(db.String(20))  # success, failed, running
    rows_exported = db.Column(db.Integer)
    file_size_mb = db.Column(db.Float)
    file_path = db.Column(db.String(500))
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)
    error_msg = db.Column(db.Text)
    reported_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'server_id': self.server_id,
            'server_name': self.server_name,
            'backup_type': self.backup_type,
            'status': self.status,
            'rows_exported': self.rows_exported,
            'file_size_mb': self.file_size_mb,
            'file_path': self.file_path,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'error_msg': self.error_msg,
            'reported_at': self.reported_at.isoformat() if self.reported_at else None
        }


class OpsCleanupRecord(db.Model):
    """Cleanup execution records reported by execution agents"""
    __tablename__ = 'ops_cleanup_records'

    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.String(20), nullable=False, index=True)
    server_name = db.Column(db.String(50))
    cleanup_type = db.Column(db.String(20))  # audit, awr, sync
    status = db.Column(db.String(20))  # success, failed, running
    rows_deleted = db.Column(db.Integer)
    space_freed_mb = db.Column(db.Float)
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)
    error_msg = db.Column(db.Text)
    reported_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'server_id': self.server_id,
            'server_name': self.server_name,
            'cleanup_type': self.cleanup_type,
            'status': self.status,
            'rows_deleted': self.rows_deleted,
            'space_freed_mb': self.space_freed_mb,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'error_msg': self.error_msg,
            'reported_at': self.reported_at.isoformat() if self.reported_at else None
        }


class OpsAlertRecord(db.Model):
    """Alert records reported by execution agents"""
    __tablename__ = 'ops_alert_records'

    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.String(20), nullable=False, index=True)
    server_name = db.Column(db.String(50))
    alert_type = db.Column(db.String(50))  # tablespace, backup_failed, xe_limit, etc.
    severity = db.Column(db.String(20))  # warning, critical
    message = db.Column(db.Text)
    detail = db.Column(db.Text)
    triggered_at = db.Column(db.DateTime, index=True)
    reported_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'server_id': self.server_id,
            'server_name': self.server_name,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'message': self.message,
            'detail': self.detail,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'reported_at': self.reported_at.isoformat() if self.reported_at else None
        }
