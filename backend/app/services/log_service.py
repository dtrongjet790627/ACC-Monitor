# -*- coding: utf-8 -*-
"""
ACC Monitor - Log Monitoring Service
Supports persistent file-based logging with daily rotation and gzip compression.
"""
import os
import re
import json
import gzip
import shutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque
from config.settings import SERVERS, LOG_ALERT_KEYWORDS
from app.services.monitor_service import MonitorService

# Log file directory (absolute path based on backend root)
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')


class SystemLogBuffer:
    """
    Thread-safe circular buffer for system logs with file persistence.
    - In-memory deque for real-time WebSocket push
    - Daily log files in JSON Lines format
    - Automatic gzip compression on day rollover
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._logs = deque(maxlen=100)  # Keep last 100 logs
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._current_date = datetime.now().strftime('%Y-%m-%d')
            self._file_lock = threading.Lock()
            # Ensure logs directory exists
            os.makedirs(LOG_DIR, exist_ok=True)

    def _get_log_file_path(self, date_str: str) -> str:
        """Get log file path for a given date string (YYYY-MM-DD)"""
        return os.path.join(LOG_DIR, f'system_{date_str}.log')

    def _check_day_rollover(self):
        """
        Check if the date has changed since the last log write.
        If so, compress yesterday's log file and update current date.
        """
        today = datetime.now().strftime('%Y-%m-%d')
        if today != self._current_date:
            old_date = self._current_date
            self._current_date = today
            # Compress the old day's log file in a background thread
            old_file = self._get_log_file_path(old_date)
            if os.path.exists(old_file):
                self._compress_log_file(old_file)

    def _compress_log_file(self, file_path: str):
        """Compress a log file to .gz and remove the original"""
        try:
            gz_path = file_path + '.gz'
            with open(file_path, 'rb') as f_in:
                with gzip.open(gz_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(file_path)
        except Exception as e:
            print(f"[LogService] Error compressing {file_path}: {e}")

    def _write_to_file(self, log_entry: Dict):
        """Append a log entry to the current day's log file (thread-safe)"""
        with self._file_lock:
            self._check_day_rollover()
            file_path = self._get_log_file_path(self._current_date)
            try:
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            except Exception as e:
                print(f"[LogService] Error writing log to file: {e}")

    def add_log(self, level: str, server_id: str, message: str) -> Dict:
        """
        Add a new log entry.
        1. Write to in-memory deque (real-time push)
        2. Append to daily log file (persistence)
        Returns the created log entry
        """
        now = datetime.now()
        log_entry = {
            'time': now.strftime('%H:%M:%S'),
            'timestamp': now.isoformat(),
            'level': level.lower(),  # critical, warning, info
            'server_id': server_id,
            'message': message
        }
        self._logs.appendleft(log_entry)
        self._write_to_file(log_entry)
        return log_entry

    def get_recent_logs(self, count: int = 50) -> List[Dict]:
        """Get most recent logs from memory"""
        return list(self._logs)[:count]

    def get_logs_by_date(self, date_str: str) -> List[Dict]:
        """
        Get logs for a specific date.
        - If date is today, return from memory.
        - If historical, read from .log or .log.gz file.
        Args:
            date_str: Date in YYYY-MM-DD format
        Returns:
            List of log entries (newest first)
        """
        today = datetime.now().strftime('%Y-%m-%d')
        if date_str == today:
            return list(self._logs)

        # Try plain log file first
        log_file = self._get_log_file_path(date_str)
        if os.path.exists(log_file):
            return self._read_log_file(log_file)

        # Try gzipped file
        gz_file = log_file + '.gz'
        if os.path.exists(gz_file):
            return self._read_gz_log_file(gz_file)

        return []

    def _read_log_file(self, file_path: str) -> List[Dict]:
        """Read log entries from a plain log file"""
        logs = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            logs.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"[LogService] Error reading log file {file_path}: {e}")
        # Return newest first (reverse chronological)
        logs.reverse()
        return logs

    def _read_gz_log_file(self, gz_path: str) -> List[Dict]:
        """Read log entries from a gzipped log file"""
        logs = []
        try:
            with gzip.open(gz_path, 'rt', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            logs.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"[LogService] Error reading gzip log file {gz_path}: {e}")
        logs.reverse()
        return logs

    def load_today_from_file(self):
        """
        Load today's logs from file into memory deque.
        Called on startup to restore logs after a restart.
        """
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self._get_log_file_path(today)
        if not os.path.exists(log_file):
            return

        logs = self._read_log_file(log_file)
        # _read_log_file returns newest-first; deque expects newest at front
        # Load up to 100 most recent entries
        recent = logs[:100]
        self._logs.clear()
        for entry in recent:
            self._logs.append(entry)

    def compress_old_logs(self):
        """
        Compress all non-today .log files in the logs directory.
        Called by the scheduler daily at 00:05.
        """
        today = datetime.now().strftime('%Y-%m-%d')
        try:
            for filename in os.listdir(LOG_DIR):
                if filename.startswith('system_') and filename.endswith('.log'):
                    # Extract date from filename: system_YYYY-MM-DD.log
                    date_part = filename.replace('system_', '').replace('.log', '')
                    if date_part != today:
                        file_path = os.path.join(LOG_DIR, filename)
                        self._compress_log_file(file_path)
                        print(f"[LogService] Compressed old log: {filename}")
        except Exception as e:
            print(f"[LogService] Error during old log compression: {e}")

    def clear(self):
        """Clear all in-memory logs"""
        self._logs.clear()


# Global singleton instance
system_log_buffer = SystemLogBuffer()


def initialize_system_logs():
    """
    Initialize system log buffer with startup messages.
    - First loads any existing today's logs from file (survives restart)
    - Then adds startup messages
    """
    buffer = system_log_buffer

    # Load today's persisted logs from file (restore after restart)
    buffer.load_today_from_file()

    # Add startup messages (always, to mark each startup)
    buffer.add_log('info', 'SYSTEM', 'System monitoring initialized')
    buffer.add_log('info', 'SYSTEM', 'WebSocket server ready')
    buffer.add_log('info', 'SYSTEM', 'Connecting to servers...')


class LogService:
    """Service for log monitoring and analysis"""

    def __init__(self):
        self.monitor_service = MonitorService()
        self.log_buffer = system_log_buffer

    def add_system_log(self, level: str, server_id: str, message: str) -> Dict:
        """
        Add a system monitoring log
        This is the main entry point for generating real-time system logs
        """
        return self.log_buffer.add_log(level, server_id, message)

    def get_system_logs(self, count: int = 50) -> List[Dict]:
        """Get recent system logs for display"""
        return self.log_buffer.get_recent_logs(count)

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
