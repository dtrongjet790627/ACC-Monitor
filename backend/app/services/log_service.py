# -*- coding: utf-8 -*-
"""
ACC Monitor - Log Monitoring Service
"""
import os
import re
from datetime import datetime
from typing import Dict, List, Optional
from config.settings import SERVERS, LOG_ALERT_KEYWORDS
from app.services.monitor_service import MonitorService


class LogService:
    """Service for log monitoring and analysis"""

    def __init__(self):
        self.monitor_service = MonitorService()

    def get_log_path(self, server_id: str) -> Optional[str]:
        """Get log path for a server"""
        if server_id not in SERVERS:
            return None
        return SERVERS[server_id].get('log_path')

    def get_recent_logs(self, server_id: str, process_name: str = None,
                        lines: int = 100) -> str:
        """Get recent log content from a server"""
        if server_id not in SERVERS:
            return ""

        server = SERVERS[server_id]
        log_path = server.get('log_path', '')
        os_type = server.get('os', 'windows')

        if os_type == 'windows':
            return self._get_windows_logs(server_id, log_path, process_name, lines)
        else:
            return self._get_linux_logs(server_id, log_path, process_name, lines)

    def _get_windows_logs(self, server_id: str, log_path: str,
                          process_name: str, lines: int) -> str:
        """Get logs from Windows server"""
        # PowerShell command to read log file
        log_file = f"{process_name}.log" if process_name else "ACC.Server.log"
        full_path = f"{log_path}\\{log_file}"

        ps_command = f'''
        Get-Content -Path "{full_path}" -Tail {lines} -ErrorAction SilentlyContinue
        '''

        # In production, execute via WinRM
        # Return simulated data for now
        return f"[Simulated log content for {process_name} on server {server_id}]"

    def _get_linux_logs(self, server_id: str, log_path: str,
                        process_name: str, lines: int) -> str:
        """Get logs from Linux server"""
        client = self.monitor_service.get_ssh_client(server_id)

        if not client:
            return ""

        try:
            log_file = f"{log_path}/{process_name}.log" if process_name else f"{log_path}/*.log"
            cmd = f"tail -n {lines} {log_file} 2>/dev/null"

            stdin, stdout, stderr = client.exec_command(cmd)
            output = stdout.read().decode('utf-8', errors='ignore')

            return output
        except Exception as e:
            print(f"Error reading Linux logs: {e}")
            return ""
        finally:
            client.close()

    def scan_for_alerts(self, server_id: str, log_content: str = None) -> List[Dict]:
        """Scan log content for alert keywords"""
        if log_content is None:
            log_content = self.get_recent_logs(server_id)

        alerts = []

        for level, keywords in LOG_ALERT_KEYWORDS.items():
            for keyword in keywords:
                # Find lines containing the keyword
                pattern = re.compile(rf'.*{re.escape(keyword)}.*', re.IGNORECASE)
                matches = pattern.findall(log_content)

                for match in matches:
                    alerts.append({
                        'server_id': server_id,
                        'level': level,
                        'keyword': keyword,
                        'message': match.strip()[:500],  # Limit message length
                        'detected_at': datetime.utcnow().isoformat()
                    })

        return alerts

    def get_device_logs(self, server_id: str) -> List[Dict]:
        """Get device/station logs from Device directory"""
        if server_id not in SERVERS:
            return []

        server = SERVERS[server_id]
        log_path = server.get('log_path', '')
        device_path = f"{log_path}\\Device"

        # List all device log files and scan for alerts
        # In production, read actual device logs
        # Return simulated data for now
        return []

    def get_station_alerts(self, server_id: str) -> List[Dict]:
        """Parse station alerts from device logs"""
        device_logs = self.get_device_logs(server_id)
        station_alerts = []

        for log in device_logs:
            # Parse station name from file name or content
            # Example: Device_OP10_2026-01-29.log

            alerts = self.scan_for_alerts(server_id, log.get('content', ''))

            for alert in alerts:
                alert['station_name'] = log.get('station_name', 'Unknown')
                alert['device_name'] = log.get('device_name', '')
                alert['log_file'] = log.get('file_name', '')
                station_alerts.append(alert)

        return station_alerts

    def search_logs(self, keyword: str, server_ids: List[str] = None,
                    start_time: datetime = None, end_time: datetime = None,
                    page: int = 1, page_size: int = 50) -> Dict:
        """Search logs across servers"""
        if server_ids is None:
            server_ids = list(SERVERS.keys())

        all_results = []

        for server_id in server_ids:
            if server_id not in SERVERS:
                continue

            # Get log content
            log_content = self.get_recent_logs(server_id, lines=1000)

            # Search for keyword
            pattern = re.compile(rf'.*{re.escape(keyword)}.*', re.IGNORECASE)
            matches = pattern.findall(log_content)

            for match in matches:
                all_results.append({
                    'server_id': server_id,
                    'server_name': SERVERS[server_id].get('name', ''),
                    'server_ip': SERVERS[server_id].get('ip', ''),
                    'message': match.strip()[:500],
                    'level': self._classify_log_level(match)
                })

        # Pagination
        total = len(all_results)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_results = all_results[start_idx:end_idx]

        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'logs': paginated_results
        }

    def _classify_log_level(self, message: str) -> str:
        """Classify log message level based on keywords"""
        message_lower = message.lower()

        for keyword in LOG_ALERT_KEYWORDS['critical']:
            if keyword.lower() in message_lower:
                return 'critical'

        for keyword in LOG_ALERT_KEYWORDS['error']:
            if keyword.lower() in message_lower:
                return 'error'

        for keyword in LOG_ALERT_KEYWORDS['warning']:
            if keyword.lower() in message_lower:
                return 'warning'

        return 'info'

    def get_log_statistics(self, server_id: str = None,
                           hours: int = 24) -> Dict:
        """Get log statistics (error counts, etc.)"""
        stats = {
            'critical_count': 0,
            'error_count': 0,
            'warning_count': 0,
            'info_count': 0,
            'total_count': 0,
            'by_server': {}
        }

        target_servers = [server_id] if server_id else list(SERVERS.keys())

        for sid in target_servers:
            if sid not in SERVERS:
                continue

            alerts = self.scan_for_alerts(sid)

            server_stats = {
                'critical': 0,
                'error': 0,
                'warning': 0,
                'info': 0
            }

            for alert in alerts:
                level = alert.get('level', 'info')
                server_stats[level] = server_stats.get(level, 0) + 1

            stats['by_server'][sid] = server_stats
            stats['critical_count'] += server_stats['critical']
            stats['error_count'] += server_stats['error']
            stats['warning_count'] += server_stats['warning']

        stats['total_count'] = (
            stats['critical_count'] +
            stats['error_count'] +
            stats['warning_count'] +
            stats['info_count']
        )

        return stats
