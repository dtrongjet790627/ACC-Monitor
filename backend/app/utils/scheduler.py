# -*- coding: utf-8 -*-
"""
ACC Monitor - Background Task Scheduler
"""
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from config.settings import Config, SERVERS


class MonitorScheduler:
    """Background task scheduler for monitoring"""

    def __init__(self, app=None):
        self.scheduler = BackgroundScheduler()
        self.app = app

        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize scheduler with Flask app"""
        self.app = app

        # Add jobs
        self.scheduler.add_job(
            func=self._check_processes,
            trigger=IntervalTrigger(seconds=Config.PROCESS_CHECK_INTERVAL),
            id='check_processes',
            name='Check server processes',
            replace_existing=True
        )

        self.scheduler.add_job(
            func=self._check_databases,
            trigger=IntervalTrigger(seconds=Config.DATABASE_CHECK_INTERVAL),
            id='check_databases',
            name='Check database status',
            replace_existing=True
        )

        self.scheduler.add_job(
            func=self._scan_logs,
            trigger=IntervalTrigger(seconds=Config.LOG_SCAN_INTERVAL),
            id='scan_logs',
            name='Scan logs for alerts',
            replace_existing=True
        )

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            print(f"Scheduler started at {datetime.utcnow()}")

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print(f"Scheduler stopped at {datetime.utcnow()}")

    def _check_processes(self):
        """Check all server processes"""
        with self.app.app_context():
            from app.services.monitor_service import MonitorService
            from app.services.restart_service import RestartService
            from app.api.websocket import (
                broadcast_server_status,
                broadcast_process_stopped,
                broadcast_process_restarted
            )
            from app.models import Alert
            from app import db

            monitor_service = MonitorService()
            restart_service = RestartService()

            for server_id in SERVERS.keys():
                server_config = SERVERS[server_id]
                os_type = server_config.get('os', 'windows')

                # Get processes
                if os_type == 'windows':
                    processes = monitor_service.check_windows_processes(server_id)
                else:
                    processes = monitor_service.check_linux_processes(server_id)

                # Check for stopped processes
                for process in processes:
                    if process.get('status') == 'stopped':
                        # Broadcast stopped event
                        broadcast_process_stopped(server_id, process['name'])

                        # Create alert
                        alert = Alert(
                            server_id=server_id,
                            level='critical',
                            source='process',
                            message=f"Process {process['name']} stopped on server {server_id}"
                        )
                        db.session.add(alert)

                        # Auto restart if enabled
                        if Config.AUTO_RESTART_ENABLED:
                            result = restart_service.restart_process(
                                server_id,
                                process['name'],
                                reason="Auto restart - process stopped"
                            )
                            broadcast_process_restarted(
                                server_id,
                                process['name'],
                                result['success']
                            )

                db.session.commit()

                # Broadcast updated status
                status = {
                    'id': server_id,
                    'name': server_config['name'],
                    'ip': server_config['ip'],
                    'status': monitor_service.get_server_status(server_id),
                    'processes': processes,
                    'last_check': datetime.utcnow().isoformat()
                }
                broadcast_server_status(status)

    def _check_databases(self):
        """Check all database status"""
        with self.app.app_context():
            from app.services.database_service import DatabaseService
            from app.api.websocket import broadcast_tablespace_warning
            from app.models import Alert
            from app import db
            from config.settings import ORACLE_CONFIGS

            database_service = DatabaseService()

            for server_id in ORACLE_CONFIGS.keys():
                db_status = database_service.get_database_status(server_id)

                # Check tablespace usage
                for ts in db_status.get('tablespaces', []):
                    if ts['status'] in ['warning', 'critical']:
                        # Broadcast warning
                        broadcast_tablespace_warning(
                            server_id,
                            ts['name'],
                            ts['used_percent']
                        )

                        # Create alert
                        level = 'critical' if ts['status'] == 'critical' else 'warning'
                        alert = Alert(
                            server_id=server_id,
                            level=level,
                            source='database',
                            message=f"Tablespace {ts['name']} usage: {ts['used_percent']}%"
                        )
                        db.session.add(alert)

                db.session.commit()

    def _scan_logs(self):
        """Scan logs for alerts"""
        with self.app.app_context():
            from app.services.log_service import LogService
            from app.api.websocket import broadcast_log_alert
            from app.models import Alert
            from app import db

            log_service = LogService()

            for server_id in SERVERS.keys():
                alerts = log_service.scan_for_alerts(server_id)

                for alert_data in alerts:
                    # Broadcast alert
                    broadcast_log_alert(
                        server_id,
                        alert_data['level'],
                        alert_data['message']
                    )

                    # Only create DB record for critical/error
                    if alert_data['level'] in ['critical', 'error']:
                        alert = Alert(
                            server_id=server_id,
                            level=alert_data['level'],
                            source='log',
                            message=alert_data['message'][:500]
                        )
                        db.session.add(alert)

                db.session.commit()


# Global scheduler instance
scheduler = MonitorScheduler()
