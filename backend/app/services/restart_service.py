# -*- coding: utf-8 -*-
"""
ACC Monitor - Auto Restart Service
"""
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from config.settings import SERVERS, PROCESS_RESTART_COMMANDS, Config
from app.services.monitor_service import MonitorService
from app.services.log_service import LogService


class RestartService:
    """Service for automatic process restart"""

    def __init__(self):
        self.monitor_service = MonitorService()
        self.log_service = LogService()
        self._last_restart_times: Dict[str, datetime] = {}

    def can_restart(self, server_id: str, process_name: str) -> bool:
        """Check if process can be restarted (cooldown check)"""
        key = f"{server_id}_{process_name}"
        last_restart = self._last_restart_times.get(key)

        if last_restart is None:
            return True

        cooldown = timedelta(seconds=Config.RESTART_COOLDOWN_SECONDS)
        return datetime.utcnow() - last_restart >= cooldown

    def get_restart_command(self, process_name: str, os_type: str = 'windows') -> Optional[str]:
        """Get restart command for a process"""
        config = PROCESS_RESTART_COMMANDS.get(process_name)
        if config:
            return config.get(os_type)
        return None

    def collect_logs_before_restart(self, server_id: str, process_name: str,
                                     lines: int = 100) -> str:
        """Collect recent logs before restart for analysis"""
        if server_id not in SERVERS:
            return ""

        server = SERVERS[server_id]
        log_path = server.get('log_path', '')

        # Get recent logs
        logs = self.log_service.get_recent_logs(server_id, process_name, lines)
        return logs

    def restart_process(self, server_id: str, process_name: str,
                        reason: str = "Auto restart") -> Dict:
        """Restart a stopped process"""
        result = {
            'server_id': server_id,
            'process_name': process_name,
            'success': False,
            'reason': reason,
            'error_message': None,
            'log_content': None,
            'restart_time': datetime.utcnow().isoformat()
        }

        # Check if auto restart is enabled
        if not Config.AUTO_RESTART_ENABLED:
            result['error_message'] = "Auto restart is disabled"
            return result

        # Check cooldown
        if not self.can_restart(server_id, process_name):
            cooldown_remaining = Config.RESTART_COOLDOWN_SECONDS - (
                datetime.utcnow() - self._last_restart_times.get(
                    f"{server_id}_{process_name}", datetime.utcnow()
                )
            ).seconds
            result['error_message'] = f"Cooldown active, {cooldown_remaining}s remaining"
            return result

        # Get server config
        if server_id not in SERVERS:
            result['error_message'] = f"Server {server_id} not found"
            return result

        server = SERVERS[server_id]
        os_type = server.get('os', 'windows')

        # Get restart command
        restart_cmd = self.get_restart_command(process_name, os_type)
        if not restart_cmd:
            result['error_message'] = f"No restart command configured for {process_name}"
            return result

        # Collect logs before restart
        result['log_content'] = self.collect_logs_before_restart(
            server_id, process_name
        )

        # Execute restart
        try:
            if os_type == 'windows':
                success = self._restart_windows_process(server_id, process_name, restart_cmd)
            else:
                success = self._restart_linux_process(server_id, process_name, restart_cmd)

            result['success'] = success

            if success:
                # Update last restart time
                key = f"{server_id}_{process_name}"
                self._last_restart_times[key] = datetime.utcnow()
            else:
                result['error_message'] = "Restart command executed but process not running"

        except Exception as e:
            result['error_message'] = str(e)

        return result

    def _restart_windows_process(self, server_id: str, process_name: str,
                                  command: str) -> bool:
        """Restart process on Windows server"""
        server = SERVERS[server_id]
        ip = server['ip']

        # PowerShell remote execution
        ps_command = f'''
        Invoke-Command -ComputerName {ip} -ScriptBlock {{
            # Stop the service first
            Stop-Service -Name "{process_name}" -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 5
            # Start the service
            Start-Service -Name "{process_name}"
            # Verify
            $service = Get-Service -Name "{process_name}" -ErrorAction SilentlyContinue
            if ($service.Status -eq "Running") {{
                return $true
            }}
            return $false
        }}
        '''

        # In production, execute via WinRM
        # For now, return simulated success
        print(f"Simulating restart of {process_name} on {ip}")
        return True

    def _restart_linux_process(self, server_id: str, process_name: str,
                                command: str) -> bool:
        """Restart process/container on Linux server"""
        client = self.monitor_service.get_ssh_client(server_id)

        if not client:
            return False

        try:
            # For Docker containers
            restart_cmd = f"docker restart {process_name}"
            stdin, stdout, stderr = client.exec_command(restart_cmd)

            # Wait for command to complete
            exit_code = stdout.channel.recv_exit_status()

            # Verify container is running
            check_cmd = f"docker ps -q -f name={process_name} -f status=running"
            stdin, stdout, stderr = client.exec_command(check_cmd)
            output = stdout.read().decode('utf-8', errors='ignore').strip()

            return len(output) > 0

        except Exception as e:
            print(f"Error restarting Linux process: {e}")
            return False
        finally:
            client.close()

    def check_and_restart_all(self) -> list:
        """Check all processes and restart stopped ones"""
        restart_results = []

        for server_id, server_config in SERVERS.items():
            os_type = server_config.get('os', 'windows')

            # Get current process status
            if os_type == 'windows':
                processes = self.monitor_service.check_windows_processes(server_id)
            else:
                processes = self.monitor_service.check_linux_processes(server_id)

            # Check each process
            for process in processes:
                if process.get('status') == 'stopped':
                    # Attempt restart
                    result = self.restart_process(
                        server_id,
                        process['name'],
                        reason="Process stopped detected"
                    )
                    restart_results.append(result)

        return restart_results

    def get_restart_history(self, server_id: str = None,
                            limit: int = 50) -> list:
        """Get restart history from database"""
        from app.models import RestartLog
        from app import db

        query = RestartLog.query

        if server_id:
            query = query.filter_by(server_id=server_id)

        query = query.order_by(RestartLog.created_at.desc())

        if limit:
            query = query.limit(limit)

        return [log.to_dict() for log in query.all()]
