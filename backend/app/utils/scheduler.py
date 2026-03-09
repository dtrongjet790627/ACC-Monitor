# -*- coding: utf-8 -*-
"""
ACC Monitor - Background Task Scheduler
Includes offline server probing for reconnection detection
"""
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from config.settings import Config, SERVERS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MonitorScheduler:
    """Background task scheduler for monitoring with reconnection support"""

    def __init__(self, app=None):
        self.scheduler = BackgroundScheduler()
        self.app = app
        # Counter to control frequency of healthy server info logs
        # Key: server_id, Value: check count since last info log
        self._health_check_counter = {}

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
            replace_existing=True,
            max_instances=2  # Allow overlap to avoid skipped checks
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

        # Add offline server probe job - runs at 60s intervals to avoid
        # probe-recovery-timeout death loop (was 15s, caused repeated SSH storms)
        self.scheduler.add_job(
            func=self._probe_offline_servers,
            trigger=IntervalTrigger(seconds=60),  # Probe every 60 seconds
            id='probe_offline_servers',
            name='Probe offline servers for recovery',
            replace_existing=True,
            max_instances=1  # Prevent overlap to avoid compounding SSH load
        )

        # Add periodic health check logging - shows system is actively monitoring
        self.scheduler.add_job(
            func=self._log_health_status,
            trigger=IntervalTrigger(seconds=60),  # Log health status every 60 seconds
            id='log_health_status',
            name='Log system health status',
            replace_existing=True
        )

        # Daily log compression at 00:05 - compress previous day's log files
        self.scheduler.add_job(
            func=self._compress_old_logs,
            trigger=CronTrigger(hour=0, minute=5),
            id='compress_logs',
            name='Compress previous day logs',
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
            from app.services.log_service import LogService
            from app.api.websocket import (
                broadcast_server_status,
                broadcast_process_stopped,
                broadcast_process_restarted,
                broadcast_system_log
            )
            from app.models import Alert
            from app import db

            monitor_service = MonitorService()
            restart_service = RestartService()
            log_service = LogService()

            for server_id in SERVERS.keys():
                server_config = SERVERS[server_id]
                server_name = server_config.get('name_cn', server_config['name'])
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

                        # Add system log for stopped process
                        log_entry = log_service.add_system_log(
                            'critical',
                            server_id,
                            f"{server_name}: Process {process['name']} stopped"
                        )
                        broadcast_system_log(log_entry)

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

                            # Add system log for restart attempt
                            restart_level = 'info' if result['success'] else 'warning'
                            restart_msg = f"{server_name}: Process {process['name']} restarted successfully" if result['success'] else f"{server_name}: Failed to restart {process['name']}"
                            log_entry = log_service.add_system_log(restart_level, server_id, restart_msg)
                            broadcast_system_log(log_entry)

                # If no stopped processes, log a health check pass (every 3rd check per server)
                stopped_processes = [p for p in processes if p.get('status') == 'stopped']
                if not stopped_processes:
                    self._health_check_counter[server_id] = self._health_check_counter.get(server_id, 0) + 1
                    if self._health_check_counter[server_id] >= 3:
                        self._health_check_counter[server_id] = 0
                        log_entry = log_service.add_system_log(
                            'info',
                            server_id,
                            f"{server_name}: Service health check passed"
                        )
                        broadcast_system_log(log_entry)
                else:
                    # Reset counter when there are issues
                    self._health_check_counter[server_id] = 0

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
            from app.services.log_service import LogService
            from app.api.websocket import broadcast_tablespace_warning, broadcast_system_log
            from app.models import Alert
            from app import db
            from config.settings import ORACLE_CONFIGS

            database_service = DatabaseService()
            log_service = LogService()

            for server_id in ORACLE_CONFIGS.keys():
                server_config = SERVERS.get(server_id, {})
                server_name = server_config.get('name_cn', server_config.get('name', server_id))
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

                        # Add system log for tablespace warning
                        level = 'critical' if ts['status'] == 'critical' else 'warning'
                        log_entry = log_service.add_system_log(
                            level,
                            server_id,
                            f"{server_name}: Tablespace {ts['name']} at {ts['used_percent']}%"
                        )
                        broadcast_system_log(log_entry)

                        # Create alert
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
            from app.api.websocket import broadcast_log_alert, broadcast_system_log
            from app.models import Alert
            from app import db

            log_service = LogService()

            for server_id in SERVERS.keys():
                server_config = SERVERS.get(server_id, {})
                server_name = server_config.get('name_cn', server_config.get('name', server_id))
                alerts = log_service.scan_for_alerts(server_id)

                for alert_data in alerts:
                    # Broadcast alert
                    broadcast_log_alert(
                        server_id,
                        alert_data['level'],
                        alert_data['message']
                    )

                    # Add system log for critical/error log alerts
                    if alert_data['level'] in ['critical', 'error']:
                        # Truncate long messages for display
                        short_msg = alert_data['message'][:100] + '...' if len(alert_data['message']) > 100 else alert_data['message']
                        log_entry = log_service.add_system_log(
                            alert_data['level'],
                            server_id,
                            f"{server_name}: {short_msg}"
                        )
                        broadcast_system_log(log_entry)

                        alert = Alert(
                            server_id=server_id,
                            level=alert_data['level'],
                            source='log',
                            message=alert_data['message'][:500]
                        )
                        db.session.add(alert)

                db.session.commit()

    def _probe_offline_servers(self):
        """
        Probe offline servers to detect recovery.
        IMPORTANT: On successful probe, we only update the SSH fallback cache
        to mark the server as 'available'.  We do NOT trigger a full status
        collection here -- that was the root cause of the probe-recovery-timeout
        death loop (probe succeeds -> full SSH collection -> times out -> marked
        offline again -> probe fires again in 15s).
        The next normal _check_processes cycle (or Agent report) will pick up
        the recovered server and broadcast the real status.
        """
        with self.app.app_context():
            from app.services.monitor_service import MonitorService
            from app.services.log_service import LogService
            from app.services.agent_data_service import agent_data_service
            from app.api.websocket import broadcast_system_log

            monitor_service = MonitorService()
            log_service = LogService()

            # Get list of offline servers (no Agent data AND not in last-good cache)
            offline_servers = []
            for server_id in SERVERS.keys():
                if not agent_data_service.is_agent_online(server_id):
                    offline_servers.append(server_id)

            if not offline_servers:
                return  # No offline servers to probe

            logger.info(f"[Scheduler] Probing {len(offline_servers)} offline servers")

            # Probe each offline server with a lightweight echo test
            for server_id in offline_servers:
                try:
                    result = monitor_service.probe_offline_server(server_id)

                    if result.get('success'):
                        # Server is SSH-reachable again.
                        # Only update SSH fallback cache -- do NOT call
                        # _get_single_server_status() to avoid full collection.
                        logger.info(f"[Scheduler] Server {server_id} SSH reachable - "
                                    f"marking available, waiting for next poll cycle")

                        server_config = SERVERS[server_id]
                        server_name = server_config.get('name_cn', server_config['name'])

                        # Reset failure count so next poll cycle will attempt SSH
                        monitor_service._failure_counts[server_id] = 0

                        # Add system log for recovery detection
                        log_entry = log_service.add_system_log(
                            'info',
                            server_id,
                            f"{server_name}: SSH connection recovered (awaiting next poll)"
                        )
                        broadcast_system_log(log_entry)

                        # Log recovery event to DB
                        from app.models import Alert
                        from app import db

                        alert = Alert(
                            server_id=server_id,
                            level='info',
                            source='monitor',
                            message=f"Server {server_config['name']} SSH connection recovered"
                        )
                        db.session.add(alert)
                        db.session.commit()

                except Exception as e:
                    logger.error(f"[Scheduler] Error probing {server_id}: {e}")


    def _compress_old_logs(self):
        """
        Compress previous day's log files.
        Scans the logs directory and gzip-compresses all .log files
        that are not from today. Runs daily at 00:05 via CronTrigger.
        """
        with self.app.app_context():
            from app.services.log_service import system_log_buffer
            try:
                system_log_buffer.compress_old_logs()
                logger.info("[Scheduler] Old log compression completed")
            except Exception as e:
                logger.error(f"[Scheduler] Error compressing old logs: {e}")

    def _log_health_status(self):
        """
        Log periodic health status messages
        This provides visual feedback that monitoring is active
        """
        with self.app.app_context():
            from app.services.monitor_service import MonitorService
            from app.services.log_service import LogService
            from app.services.agent_data_service import agent_data_service
            from app.api.websocket import broadcast_system_log

            monitor_service = MonitorService()
            log_service = LogService()

            # Count online/offline servers
            online_count = 0
            offline_count = 0
            warning_count = 0

            for server_id in SERVERS.keys():
                if agent_data_service.is_agent_online(server_id):
                    online_count += 1
                else:
                    # Check SSH fallback status
                    ssh_status = monitor_service._ssh_connection_status.get(server_id, {})
                    if ssh_status.get('connected'):
                        online_count += 1
                    else:
                        offline_count += 1

            # Generate appropriate log message based on status
            if offline_count == 0:
                # All servers healthy
                log_entry = log_service.add_system_log(
                    'info',
                    'SYSTEM',
                    f"All {online_count} servers healthy"
                )
            elif offline_count > 0 and online_count > 0:
                # Mixed status
                log_entry = log_service.add_system_log(
                    'warning',
                    'SYSTEM',
                    f"Health check: {online_count} online, {offline_count} offline"
                )
            else:
                # All offline
                log_entry = log_service.add_system_log(
                    'critical',
                    'SYSTEM',
                    f"All {offline_count} servers offline"
                )

            broadcast_system_log(log_entry)


# Global scheduler instance
scheduler = MonitorScheduler()
