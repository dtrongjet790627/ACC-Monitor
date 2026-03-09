# -*- coding: utf-8 -*-
"""
Oracle Ops Service - Business logic layer for Oracle database operations monitoring.
Handles data storage from execution agent reports and data retrieval for frontend queries.
"""
import json
import requests
import logging
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from app import db
from app.models.oracle_ops_models import (
    OpsTablespaceData,
    OpsBackupRecord,
    OpsCleanupRecord,
    OpsAlertRecord
)

logger = logging.getLogger(__name__)

# Oracle database server info
ORACLE_SERVERS = {
    '165': {'name': 'Factory (165)', 'ip': '172.17.10.165', 'edition': 'SE', 'limit_gb': None},
    '164': {'name': 'ECU Line1 (164)', 'ip': '172.17.10.164', 'edition': 'XE', 'limit_gb': 11},
    '153': {'name': 'DP Assembly (153)', 'ip': '172.17.10.153', 'edition': 'XE', 'limit_gb': 11},
    '168': {'name': 'ECU Line2 (168)', 'ip': '172.17.10.168', 'edition': 'XE', 'limit_gb': 11},
    '193': {'name': 'C-EPS (193)', 'ip': '172.17.10.193', 'edition': 'XE', 'limit_gb': 11},
    '194': {'name': 'L-EPP (194)', 'ip': '172.17.10.194', 'edition': 'XE', 'limit_gb': 11},
}

AGENT_API_PORT = 5005


class OracleOpsService:
    """Oracle Ops business logic service"""

    # =========================================
    # Data ingestion (from execution agents)
    # =========================================

    def store_report_data(self, data):
        """
        Process and store a full report from an execution agent.
        A report may contain tablespaces, backups, cleanups, and alerts.
        """
        server_id = data.get('server_id')
        server_name = data.get('server_name', ORACLE_SERVERS.get(server_id, {}).get('name', ''))
        timestamp_str = data.get('timestamp')
        collected_at = None
        if timestamp_str:
            try:
                collected_at = datetime.fromisoformat(timestamp_str)
            except (ValueError, TypeError):
                collected_at = datetime.utcnow()

        stored = {'tablespaces': 0, 'backups': 0, 'cleanups': 0, 'alerts': 0}

        # Store tablespace data
        tablespaces = data.get('tablespaces', [])
        for ts in tablespaces:
            record = OpsTablespaceData(
                server_id=server_id,
                server_name=server_name,
                tablespace_name=ts.get('tablespace_name', ''),
                used_mb=ts.get('used_mb', 0),
                max_mb=ts.get('max_mb', 0),
                usage_pct=ts.get('usage_pct', 0),
                # Store current active file data for business tablespaces
                current_file_pct=ts.get('current_file_pct'),
                current_file_used_mb=ts.get('current_file_used_mb'),
                current_file_max_mb=ts.get('current_file_max_mb'),
                collected_at=collected_at or datetime.utcnow()
            )
            db.session.add(record)
            stored['tablespaces'] += 1

        # Store backup records
        backups = data.get('backups', [])
        for bk in backups:
            record = OpsBackupRecord(
                server_id=server_id,
                server_name=server_name,
                backup_type=bk.get('backup_type', ''),
                status=bk.get('status', ''),
                rows_exported=bk.get('rows_exported', 0),
                file_size_mb=bk.get('file_size_mb', 0),
                file_path=bk.get('file_path', ''),
                started_at=self._parse_dt(bk.get('started_at')),
                finished_at=self._parse_dt(bk.get('finished_at')),
                error_msg=bk.get('error_msg')
            )
            db.session.add(record)
            stored['backups'] += 1

        # Store cleanup records
        cleanups = data.get('cleanups', [])
        for cl in cleanups:
            record = OpsCleanupRecord(
                server_id=server_id,
                server_name=server_name,
                cleanup_type=cl.get('cleanup_type', ''),
                status=cl.get('status', ''),
                rows_deleted=cl.get('rows_deleted', 0),
                space_freed_mb=cl.get('space_freed_mb', 0),
                started_at=self._parse_dt(cl.get('started_at')),
                finished_at=self._parse_dt(cl.get('finished_at')),
                error_msg=cl.get('error_msg')
            )
            db.session.add(record)
            stored['cleanups'] += 1

        # Store alert records
        alerts = data.get('alerts', [])
        for al in alerts:
            record = OpsAlertRecord(
                server_id=server_id,
                server_name=server_name,
                alert_type=al.get('alert_type', ''),
                severity=al.get('severity', 'warning'),
                message=al.get('message', ''),
                detail=al.get('detail', ''),
                triggered_at=self._parse_dt(al.get('triggered_at')) or datetime.utcnow()
            )
            db.session.add(record)
            stored['alerts'] += 1

        db.session.commit()
        return stored

    # =========================================
    # Frontend query methods
    # =========================================

    def get_overview(self):
        """
        Get overview data for all 6 Oracle databases.
        Returns: server status, max tablespace usage, latest backup, recent alerts.
        """
        overview = []

        for server_id, info in ORACLE_SERVERS.items():
            server_data = {
                'server_id': server_id,
                'server_name': info['name'],
                'server_ip': info['ip'],
                'edition': info['edition'],
                'limit_gb': info['limit_gb'],
                'status': 'normal',
                'max_tablespace_usage': 0,
                'max_tablespace_name': '',
                'tablespace_count': 0,
                'latest_backup': None,
                'latest_backup_time': None,
                'recent_alerts_count': 0,
                'last_report_time': None,
            }

            # Get the latest tablespace data for this server
            latest_ts = OpsTablespaceData.query.filter_by(
                server_id=server_id
            ).order_by(
                OpsTablespaceData.collected_at.desc()
            ).limit(50).all()

            if latest_ts:
                # Get the most recent collection timestamp
                latest_time = latest_ts[0].collected_at
                server_data['last_report_time'] = latest_time.isoformat() if latest_time else None

                # Filter to only the most recent collection batch
                recent_ts = [t for t in latest_ts if t.collected_at == latest_time]
                server_data['tablespace_count'] = len(recent_ts)

                # Find the featured tablespace: prioritize business data tablespaces
                # Business tablespace rules:
                #   - Name contains 'ACC_DATA'
                #   - Name matches IPLANT_*_DATA pattern (e.g., IPLANT_DPEPP1_DATA, IPLANT_DPEPS_DATA)
                if recent_ts:
                    featured_ts = self._select_featured_tablespace(recent_ts)

                    # For business tablespaces with current_file_pct data,
                    # use the current active file usage instead of total usage.
                    # Business tablespaces may have multiple data files; historical
                    # files being full is normal. Only the latest file matters.
                    display_pct = featured_ts.usage_pct or 0
                    if (self._is_business_tablespace(featured_ts.tablespace_name)
                            and featured_ts.current_file_pct is not None):
                        display_pct = featured_ts.current_file_pct

                    server_data['max_tablespace_usage'] = display_pct
                    server_data['max_tablespace_name'] = featured_ts.tablespace_name
                    # Also include the raw total usage for reference
                    server_data['total_usage_pct'] = featured_ts.usage_pct or 0
                    # Include current_file data if available
                    if featured_ts.current_file_pct is not None:
                        server_data['current_file_pct'] = featured_ts.current_file_pct
                        server_data['current_file_used_mb'] = featured_ts.current_file_used_mb
                        server_data['current_file_max_mb'] = featured_ts.current_file_max_mb

                    # Determine status based on the display percentage
                    if display_pct >= 95:
                        server_data['status'] = 'critical'
                    elif display_pct >= 85:
                        server_data['status'] = 'warning'
            else:
                server_data['status'] = 'unknown'

            # Get latest backup record
            latest_backup = OpsBackupRecord.query.filter_by(
                server_id=server_id
            ).order_by(OpsBackupRecord.finished_at.desc()).first()

            if latest_backup:
                server_data['latest_backup'] = latest_backup.status
                server_data['latest_backup_time'] = (
                    latest_backup.finished_at.isoformat() if latest_backup.finished_at else None
                )

            # Count recent alerts (last 24 hours), excluding info-level alerts
            # (e.g., SYSAUX alerts that have been downgraded to info)
            since_24h = datetime.utcnow() - timedelta(hours=24)
            alert_count = OpsAlertRecord.query.filter(
                OpsAlertRecord.server_id == server_id,
                OpsAlertRecord.triggered_at >= since_24h,
                OpsAlertRecord.severity.in_(['warning', 'critical'])
            ).count()
            server_data['recent_alerts_count'] = alert_count

            overview.append(server_data)

        return overview

    def get_tablespaces(self, server_id=None):
        """Get tablespace details, optionally filtered by server_id"""
        query = OpsTablespaceData.query

        if server_id:
            query = query.filter_by(server_id=server_id)

        # Get the latest collection for each server+tablespace combination
        subquery = db.session.query(
            OpsTablespaceData.server_id,
            OpsTablespaceData.tablespace_name,
            func.max(OpsTablespaceData.collected_at).label('max_collected')
        ).group_by(
            OpsTablespaceData.server_id,
            OpsTablespaceData.tablespace_name
        )

        if server_id:
            subquery = subquery.filter(OpsTablespaceData.server_id == server_id)

        subquery = subquery.subquery()

        results = OpsTablespaceData.query.join(
            subquery,
            db.and_(
                OpsTablespaceData.server_id == subquery.c.server_id,
                OpsTablespaceData.tablespace_name == subquery.c.tablespace_name,
                OpsTablespaceData.collected_at == subquery.c.max_collected
            )
        ).order_by(
            OpsTablespaceData.server_id,
            OpsTablespaceData.usage_pct.desc()
        ).all()

        return [r.to_dict() for r in results]

    def get_tablespace_trends(self, server_id=None, days=7):
        """
        Get tablespace usage trends for ECharts.
        Returns data grouped by tablespace name with time series.
        """
        since = datetime.utcnow() - timedelta(days=days)
        query = OpsTablespaceData.query.filter(
            OpsTablespaceData.collected_at >= since
        )

        if server_id:
            query = query.filter_by(server_id=server_id)

        data = query.order_by(OpsTablespaceData.collected_at.asc()).all()

        # Group by tablespace_name
        trends = {}
        for record in data:
            key = f"{record.server_id}_{record.tablespace_name}"
            if key not in trends:
                trends[key] = {
                    'server_id': record.server_id,
                    'server_name': record.server_name,
                    'tablespace_name': record.tablespace_name,
                    'is_business': self._is_business_tablespace(record.tablespace_name),
                    'data_points': []
                }

            # For business tablespaces, use current_file_pct when available
            display_pct = record.usage_pct
            display_used_mb = record.used_mb
            display_max_mb = record.max_mb
            if (self._is_business_tablespace(record.tablespace_name)
                    and record.current_file_pct is not None):
                display_pct = record.current_file_pct
                display_used_mb = record.current_file_used_mb
                display_max_mb = record.current_file_max_mb

            trends[key]['data_points'].append({
                'time': record.collected_at.isoformat() if record.collected_at else None,
                'usage_pct': display_pct,
                'used_mb': display_used_mb,
                'max_mb': display_max_mb,
                # Include raw total values for reference
                'total_usage_pct': record.usage_pct,
                'total_used_mb': record.used_mb,
                'total_max_mb': record.max_mb,
            })

        return list(trends.values())

    def get_backups(self, server_id=None, status=None, page=1, page_size=20):
        """Get backup execution records with pagination and filters"""
        query = OpsBackupRecord.query

        if server_id:
            query = query.filter_by(server_id=server_id)
        if status:
            query = query.filter_by(status=status)

        query = query.order_by(OpsBackupRecord.finished_at.desc())

        total = query.count()
        records = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'records': [r.to_dict() for r in records]
        }

    def get_cleanups(self, server_id=None, status=None, page=1, page_size=20):
        """Get cleanup execution records with pagination and filters"""
        query = OpsCleanupRecord.query

        if server_id:
            query = query.filter_by(server_id=server_id)
        if status:
            query = query.filter_by(status=status)

        query = query.order_by(OpsCleanupRecord.finished_at.desc())

        total = query.count()
        records = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'records': [r.to_dict() for r in records]
        }

    def get_alerts(self, server_id=None, severity=None, page=1, page_size=20):
        """Get alert records with pagination and filters"""
        query = OpsAlertRecord.query

        if server_id:
            query = query.filter_by(server_id=server_id)
        if severity:
            query = query.filter_by(severity=severity)

        query = query.order_by(OpsAlertRecord.triggered_at.desc())

        total = query.count()
        records = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'records': [r.to_dict() for r in records]
        }

    # =========================================
    # Configuration management
    # =========================================

    def get_agent_config(self, server_id):
        """Fetch current config from execution agent"""
        info = ORACLE_SERVERS.get(server_id)
        if not info:
            return None

        url = f"http://{info['ip']}:{AGENT_API_PORT}/config"
        try:
            resp = requests.get(url, timeout=10, headers={'X-Oracle-Ops-Key': 'acc-monitor-ops'})
            if resp.status_code == 200:
                return resp.json()
            else:
                return {'error': f'Agent returned status {resp.status_code}'}
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to get config from agent {server_id}: {e}")
            return {'error': f'Agent unreachable: {str(e)}'}

    def push_agent_config(self, server_id, config_data):
        """Push configuration to execution agent"""
        info = ORACLE_SERVERS.get(server_id)
        if not info:
            return {'success': False, 'error': f'Unknown server_id: {server_id}'}

        url = f"http://{info['ip']}:{AGENT_API_PORT}/config"
        try:
            resp = requests.post(
                url,
                json=config_data,
                timeout=10,
                headers={'X-Oracle-Ops-Key': 'acc-monitor-ops'}
            )
            if resp.status_code == 200:
                return {'success': True, 'agent_response': resp.json()}
            else:
                return {'success': False, 'error': f'Agent returned status {resp.status_code}'}
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to push config to agent {server_id}: {e}")
            return {'success': False, 'error': f'Agent unreachable: {str(e)}'}

    # =========================================
    # Helper methods
    # =========================================

    @staticmethod
    def _is_business_tablespace(ts_name):
        """
        Check if a tablespace name is a business data tablespace.
        Business tablespace rules:
          - Name contains 'ACC_DATA'
          - Name matches IPLANT_*_DATA pattern (e.g. IPLANT_DPEPP1_DATA, IPLANT_DPEPS_DATA)
        """
        if not ts_name:
            return False
        name_upper = ts_name.upper()
        if 'ACC_DATA' in name_upper:
            return True
        if name_upper.startswith('IPLANT_') and name_upper.endswith('_DATA'):
            return True
        return False

    # System/non-business tablespaces that should be excluded from featured display
    _EXCLUDED_TABLESPACES = {'SYSAUX', 'TEMP', 'UNDOTBS1', 'UNDOTBS2', 'UNDO'}

    @classmethod
    def _select_featured_tablespace(cls, tablespace_list):
        """
        Select the featured tablespace for card display.
        Priority:
          1. Business data tablespace with highest usage (ACC_DATA, IPLANT_*_DATA)
          2. Non-system tablespace with highest usage (exclude SYSAUX, TEMP, UNDO*)
          3. Fallback: tablespace with highest usage overall
        """
        # Priority 1: Business data tablespaces
        business_ts = [t for t in tablespace_list if cls._is_business_tablespace(t.tablespace_name)]
        if business_ts:
            return max(business_ts, key=lambda t: t.usage_pct or 0)

        # Priority 2: Non-system tablespaces (exclude SYSAUX, TEMP, UNDO*)
        non_system_ts = [
            t for t in tablespace_list
            if t.tablespace_name and t.tablespace_name.upper() not in cls._EXCLUDED_TABLESPACES
            and not t.tablespace_name.upper().startswith('UNDO')
        ]
        if non_system_ts:
            return max(non_system_ts, key=lambda t: t.usage_pct or 0)

        # Priority 3: Fallback to max usage overall
        return max(tablespace_list, key=lambda t: t.usage_pct or 0)

    @staticmethod
    def _parse_dt(dt_str):
        """Parse a datetime string, return None if invalid"""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str)
        except (ValueError, TypeError):
            return None


# Singleton instance
oracle_ops_service = OracleOpsService()
