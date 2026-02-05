# -*- coding: utf-8 -*-
"""
ACC Monitor - Server and Process Monitoring Service
Uses Agent data when available, falls back to simulated/SSH data otherwise
"""
import os
import paramiko
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from config.settings import SERVERS, SSH_CREDENTIALS, SSH_PORTS, Config
from app.services.agent_data_service import agent_data_service


class MonitorService:
    """Service for monitoring servers and processes"""

    def __init__(self):
        self._ssh_clients: Dict[str, paramiko.SSHClient] = {}
        self.agent_data = agent_data_service
        # Track restart history and alerts
        self._restart_history: Dict[str, Dict] = {}  # {server_id_process: {last_restart, result, ...}}
        self._alert_cache: Dict[str, Dict] = {}  # {server_id: {alerts, last_update}}

    def exec_ssh_command(self, server_id: str, command: str, timeout: int = 8) -> Optional[str]:
        """Execute SSH command using subprocess (more reliable for Windows SSH)"""
        if server_id not in SERVERS:
            return None

        server = SERVERS[server_id]
        ip = server['ip']
        os_type = server.get('os', 'windows')
        creds = SSH_CREDENTIALS.get(os_type, SSH_CREDENTIALS['windows'])
        ssh_port = SSH_PORTS.get(server_id, 22)

        ssh_cmd = [
            'ssh',
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'BatchMode=yes',
            '-o', 'ServerAliveInterval=2',
            '-o', 'ServerAliveCountMax=1',
            '-p', str(ssh_port),
            f"{creds['username']}@{ip}",
            command
        ]

        try:
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='ignore'
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except subprocess.TimeoutExpired:
            print(f"SSH timeout for {ip}")
            return None
        except Exception as e:
            print(f"SSH error for {ip}: {e}")
            return None

    def get_ssh_client(self, server_id: str) -> Optional[paramiko.SSHClient]:
        """Get or create SSH client for a server using key-based authentication"""
        if server_id not in SERVERS:
            return None

        server = SERVERS[server_id]
        ip = server['ip']
        os_type = server.get('os', 'windows')

        # Get credentials based on OS type
        creds = SSH_CREDENTIALS.get(os_type, SSH_CREDENTIALS['windows'])

        # Get SSH port (default 22, but 163 uses 2200)
        ssh_port = SSH_PORTS.get(server_id, 22)

        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            key_file = creds.get('key_file')
            if not key_file or not os.path.exists(key_file):
                print(f"SSH key file not found: {key_file}")
                return None

            # Try to load private key (support both RSA and Ed25519)
            private_key = None
            try:
                private_key = paramiko.RSAKey.from_private_key_file(key_file)
            except paramiko.SSHException:
                try:
                    private_key = paramiko.Ed25519Key.from_private_key_file(key_file)
                except Exception:
                    pass

            if not private_key:
                print(f"Failed to load SSH key: {key_file}")
                return None

            client.connect(
                hostname=ip,
                port=ssh_port,
                username=creds['username'],
                pkey=private_key,
                timeout=15,
                banner_timeout=30,
                auth_timeout=15
            )

            return client
        except Exception as e:
            print(f"SSH connection error for {ip}:{ssh_port}: {e}")
            return None

    def check_windows_services(self, server_id: str, ssh_client=None) -> List[Dict]:
        """
        Check Windows service status via SSH
        Uses subprocess SSH for reliability
        """
        if server_id not in SERVERS:
            return []

        server_config = SERVERS.get(server_id, {})
        services = server_config.get('services', [])

        if not services:
            return []

        results = []

        for svc in services:
            service_name = svc.get('service_name', '')
            display_name = svc.get('display_name', service_name)

            if not service_name:
                continue

            # Use sc query to check service status
            cmd = f'sc query "{service_name}"'
            output = self.exec_ssh_command(server_id, cmd)

            status = 'unknown'
            if output:
                output_upper = output.upper()
                if 'RUNNING' in output_upper:
                    status = 'running'
                elif 'STOPPED' in output_upper:
                    status = 'stopped'
                elif 'PENDING' in output_upper:
                    status = 'pending'
                elif 'does not exist' in output.lower() or 'FAILED' in output_upper:
                    status = 'not_found'

            results.append({
                'name': display_name,
                'service_name': service_name,
                'status': status,
                'type': 'service',
                'last_check': datetime.utcnow().isoformat(),
                'data_source': 'ssh' if output else 'none'
            })

        return results

    def check_windows_processes(self, server_id: str) -> List[Dict]:
        """
        Check process status on Windows server using single SSH command
        """
        if server_id not in SERVERS:
            return []

        # Try to get real data from agent first
        agent_processes = self.agent_data.get_process_status(server_id)
        if agent_processes and self.agent_data.is_agent_online(server_id):
            for proc in agent_processes:
                proc['last_check'] = datetime.utcnow().isoformat()
            return agent_processes

        server = SERVERS[server_id]
        processes_to_check = server.get('processes', [])
        results = []

        # Get all processes at once with a single SSH command
        cmd = 'tasklist /FO CSV /NH'
        output = self.exec_ssh_command(server_id, cmd, timeout=15)

        for proc_name in processes_to_check:
            # Oracle is handled separately
            if proc_name.lower() == 'oracle':
                results.append({
                    'name': proc_name,
                    'status': 'running',
                    'pid': 0,
                    'cpu': 0,
                    'memory': 0,
                    'type': 'process',
                    'last_check': datetime.utcnow().isoformat(),
                    'data_source': 'db'
                })
                continue

            if output:
                # Search for process in output
                proc_found = False
                proc_name_lower = f'{proc_name}.exe'.lower()
                for line in output.split('\n'):
                    if proc_name_lower in line.lower():
                        proc_found = True
                        try:
                            parts = line.split(',')
                            if len(parts) >= 5:
                                pid = int(parts[1].strip('"'))
                                mem_str = parts[4].strip('"').replace(' K', '').replace(',', '')
                                memory = int(mem_str) // 1024
                            else:
                                pid = 0
                                memory = 0
                        except (ValueError, IndexError):
                            pid = 0
                            memory = 0

                        results.append({
                            'name': proc_name,
                            'status': 'running',
                            'pid': pid,
                            'cpu': 0,
                            'memory': memory,
                            'type': 'process',
                            'last_check': datetime.utcnow().isoformat(),
                            'data_source': 'ssh'
                        })
                        break

                if not proc_found:
                    results.append({
                        'name': proc_name,
                        'status': 'stopped',
                        'pid': 0,
                        'cpu': 0,
                        'memory': 0,
                        'type': 'process',
                        'last_check': datetime.utcnow().isoformat(),
                        'data_source': 'ssh'
                    })
            else:
                results.append({
                    'name': proc_name,
                    'status': 'unknown',
                    'pid': 0,
                    'cpu': 0,
                    'memory': 0,
                    'type': 'process',
                    'last_check': datetime.utcnow().isoformat(),
                    'data_source': 'none'
                })

        return results

    def check_linux_processes(self, server_id: str) -> List[Dict]:
        """Check process/container status on Linux server"""
        if server_id not in SERVERS:
            return []

        server = SERVERS[server_id]
        containers_to_monitor = server.get('containers', [])
        results = []

        # Docker command to check containers
        docker_cmd = 'docker ps -a --format "{{.Names}}|{{.Status}}|{{.ID}}"'

        client = self.get_ssh_client(server_id)
        if client:
            try:
                stdin, stdout, stderr = client.exec_command(docker_cmd)
                output = stdout.read().decode('utf-8', errors='ignore')

                # Build a dict of all container statuses
                all_containers = {}
                for line in output.strip().split('\n'):
                    if line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            name, status, container_id = parts[0], parts[1], parts[2]
                            is_running = 'Up' in status
                            all_containers[name] = {
                                'name': name,
                                'status': 'running' if is_running else 'stopped',
                                'container_id': container_id,
                                'last_check': datetime.utcnow().isoformat()
                            }

                # Only return containers that are in the monitor list
                for container_name in containers_to_monitor:
                    if container_name in all_containers:
                        results.append(all_containers[container_name])
                    else:
                        # Container not found
                        results.append({
                            'name': container_name,
                            'status': 'stopped',
                            'container_id': '',
                            'last_check': datetime.utcnow().isoformat()
                        })
            except Exception as e:
                print(f"Error checking Linux processes: {e}")
            finally:
                client.close()
        else:
            # Return simulated data if cannot connect
            for container in containers_to_monitor:
                results.append({
                    'name': container,
                    'status': 'unknown',
                    'container_id': '',
                    'last_check': datetime.utcnow().isoformat()
                })

        return results

    def check_server_resources(self, server_id: str) -> Dict:
        """Check CPU, memory, disk usage of a server"""
        if server_id not in SERVERS:
            return {}

        server = SERVERS[server_id]
        os_type = server.get('os', 'windows')

        if os_type == 'windows':
            return self._check_windows_resources(server_id)
        else:
            return self._check_linux_resources(server_id)

    def _check_windows_resources(self, server_id: str) -> Dict:
        """Check Windows server resources via SSH"""
        result = {
            'cpu_usage': 0,
            'memory_usage': 0,
            'disk_usage': 0,
            'last_check': datetime.utcnow().isoformat(),
            'data_source': 'none'
        }

        server_config = SERVERS.get(server_id, {})

        # Get CPU usage via wmic (average of all cores)
        cpu_cmd = 'wmic cpu get loadpercentage /value'
        cpu_output = self.exec_ssh_command(server_id, cpu_cmd, timeout=15)
        if cpu_output:
            try:
                cpu_values = []
                for line in cpu_output.replace('\r', '').split('\n'):
                    if 'LoadPercentage=' in line:
                        val = line.split('=')[1].strip()
                        if val and val.isdigit():
                            cpu_values.append(int(val))
                if cpu_values:
                    result['cpu_usage'] = round(sum(cpu_values) / len(cpu_values), 1)
            except (ValueError, IndexError):
                pass

        # Get Memory usage via wmic
        mem_cmd = 'wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /value'
        mem_output = self.exec_ssh_command(server_id, mem_cmd, timeout=5)
        if mem_output:
            try:
                free_mem = 0
                total_mem = 0
                for line in mem_output.replace('\r', '').split('\n'):
                    line = line.strip()
                    if 'FreePhysicalMemory=' in line:
                        val = line.split('=')[1].strip()
                        if val and val.isdigit():
                            free_mem = int(val)
                    elif 'TotalVisibleMemorySize=' in line:
                        val = line.split('=')[1].strip()
                        if val and val.isdigit():
                            total_mem = int(val)
                if total_mem > 0:
                    result['memory_usage'] = round((total_mem - free_mem) / total_mem * 100, 1)
            except (ValueError, IndexError):
                pass

        # Get Disk usage for ACC drive
        acc_drive = server_config.get('acc_drive', 'D')
        disk_cmd = f'wmic logicaldisk where "DeviceID=\'{acc_drive}:\'" get Size,FreeSpace /value'
        disk_output = self.exec_ssh_command(server_id, disk_cmd, timeout=5)
        if disk_output:
            try:
                free_space = 0
                total_size = 0
                for line in disk_output.replace('\r', '').split('\n'):
                    line = line.strip()
                    if 'FreeSpace=' in line:
                        val = line.split('=')[1].strip()
                        if val and val.isdigit():
                            free_space = int(val)
                    elif 'Size=' in line:
                        val = line.split('=')[1].strip()
                        if val and val.isdigit():
                            total_size = int(val)
                if total_size > 0:
                    result['disk_usage'] = round((total_size - free_space) / total_size * 100, 1)
            except (ValueError, IndexError):
                pass

        if result['cpu_usage'] > 0 or result['memory_usage'] > 0 or result['disk_usage'] > 0:
            result['data_source'] = 'ssh'

        return result

    def _check_linux_resources(self, server_id: str) -> Dict:
        """Check Linux server resources via SSH"""
        result = {
            'cpu_usage': 0,
            'memory_usage': 0,
            'disk_usage': 0,
            'last_check': datetime.utcnow().isoformat(),
            'data_source': 'none'
        }

        # CPU usage - use vmstat for more reliable output
        cpu_output = self.exec_ssh_command(server_id, "vmstat 1 2 | tail -1 | awk '{print 100-$15}'", timeout=10)
        if cpu_output:
            try:
                result['cpu_usage'] = round(float(cpu_output.replace(',', '.')), 1)
            except ValueError:
                pass

        # Memory usage
        mem_output = self.exec_ssh_command(server_id, "free | grep Mem | awk '{print $3/$2 * 100.0}'", timeout=5)
        if mem_output:
            try:
                result['memory_usage'] = round(float(mem_output), 1)
            except ValueError:
                pass

        # Disk usage
        disk_output = self.exec_ssh_command(server_id, "df / | tail -1 | awk '{print $5}' | tr -d '%'", timeout=5)
        if disk_output:
            try:
                result['disk_usage'] = round(float(disk_output), 1)
            except ValueError:
                pass

        if result['cpu_usage'] > 0 or result['memory_usage'] > 0:
            result['data_source'] = 'ssh'

        return result

    def get_server_status(self, server_id: str, processes: List[Dict] = None) -> str:
        """Determine overall server status based on processes"""
        if server_id not in SERVERS:
            return 'unknown'

        # Use provided processes or fetch new ones
        if processes is None:
            server = SERVERS[server_id]
            os_type = server.get('os', 'windows')
            if os_type == 'windows':
                processes = self.check_windows_processes(server_id)
                services = self.check_windows_services(server_id)
                if services:
                    processes.extend(services)
            else:
                processes = self.check_linux_processes(server_id)

        # Check if any process is stopped
        stopped_count = sum(1 for p in processes if p.get('status') == 'stopped')

        if stopped_count > 0:
            return 'error'

        # Check if all processes are unknown (no agent data)
        unknown_count = sum(1 for p in processes if p.get('status') == 'unknown')
        if unknown_count == len(processes) and len(processes) > 0:
            return 'offline'

        # Check if any process has warning status
        warning_count = sum(1 for p in processes if p.get('status') == 'warning')
        if warning_count > 0:
            return 'warning'

        return 'normal'

    def _get_single_server_status(self, server_id: str) -> Dict:
        """Get status of a single server (for parallel execution)"""
        server_config = SERVERS[server_id]
        os_type = server_config.get('os', 'windows')

        # For Windows servers, try to use agent data first
        if os_type == 'windows':
            agent_online = self.agent_data.is_agent_online(server_id)
        else:
            agent_online = False

        # Get processes
        if os_type == 'windows':
            processes = self.check_windows_processes(server_id)
            services = self.check_windows_services(server_id)
            if services:
                processes.extend(services)
        else:
            processes = self.check_linux_processes(server_id)

        # Get resources
        resources = self.check_server_resources(server_id)

        # Check for stopped processes and auto restart, also add alert info
        processes = self.check_and_auto_restart(server_id, processes)

        # Determine status based on processes
        stopped_count = sum(1 for p in processes if p.get('status') == 'stopped')
        unknown_count = sum(1 for p in processes if p.get('status') == 'unknown')
        warning_count = sum(1 for p in processes if p.get('status') == 'warning')

        if stopped_count > 0:
            status = 'error'
        elif unknown_count == len(processes) and len(processes) > 0:
            status = 'offline'
        elif warning_count > 0:
            status = 'warning'
        else:
            status = 'normal'

        # Get data source info
        data_source = 'ssh'
        if any(p.get('data_source') == 'agent' for p in processes):
            data_source = 'agent'
        elif all(p.get('data_source') == 'none' for p in processes):
            data_source = 'none'

        return {
            'id': server_id,
            'name': server_config['name'],
            'name_cn': server_config.get('name_cn', ''),
            'ip': server_config['ip'],
            'os_type': os_type,
            'status': status,
            'processes': processes,
            'cpu_usage': resources.get('cpu_usage', 0),
            'memory_usage': resources.get('memory_usage', 0),
            'disk_usage': resources.get('disk_usage', 0),
            'agent_online': agent_online,
            'data_source': data_source,
            'last_check': datetime.utcnow().isoformat()
        }

    def get_all_servers_status(self) -> List[Dict]:
        """Get status of all monitored servers using parallel execution"""
        results = []

        # Use ThreadPoolExecutor for parallel checking
        try:
            with ThreadPoolExecutor(max_workers=7) as executor:
                future_to_server = {
                    executor.submit(self._get_single_server_status, server_id): server_id
                    for server_id in SERVERS.keys()
                }

                try:
                    for future in as_completed(future_to_server, timeout=60):
                        server_id = future_to_server[future]
                        try:
                            result = future.result(timeout=45)
                            results.append(result)
                        except Exception as e:
                            # Use ascii encoding with replace to avoid console encoding issues
                            error_msg = str(e).encode('ascii', errors='replace').decode('ascii')
                            print(f"Error for {server_id}: {error_msg}")
                            self._add_offline_server(results, server_id)
                except TimeoutError:
                    # Some futures didn't complete, add them as offline
                    for future, server_id in future_to_server.items():
                        if not future.done():
                            future.cancel()
                            self._add_offline_server(results, server_id)
        except Exception as e:
            print(f"ThreadPool error: {e}")

        # Sort by sort_order from config
        results.sort(key=lambda x: SERVERS.get(x['id'], {}).get('sort_order', 99))
        return results

    def _add_offline_server(self, results: List[Dict], server_id: str):
        """Add offline status for a server"""
        if any(r['id'] == server_id for r in results):
            return  # Already added
        server_config = SERVERS[server_id]
        results.append({
            'id': server_id,
            'name': server_config['name'],
            'name_cn': server_config.get('name_cn', ''),
            'ip': server_config['ip'],
            'os_type': server_config.get('os', 'windows'),
            'status': 'offline',
            'processes': [],
            'cpu_usage': 0,
            'memory_usage': 0,
            'disk_usage': 0,
            'agent_online': False,
            'data_source': 'none',
            'last_check': datetime.utcnow().isoformat()
        })

    # ============ Auto Restart Methods ============

    def can_restart(self, server_id: str, process_name: str) -> bool:
        """Check if process can be restarted (cooldown check)"""
        key = f"{server_id}_{process_name}"
        history = self._restart_history.get(key)

        if history is None:
            return True

        last_restart = history.get('last_restart')
        if last_restart is None:
            return True

        cooldown = timedelta(seconds=Config.RESTART_COOLDOWN_SECONDS)
        return datetime.utcnow() - last_restart >= cooldown

    def restart_windows_service(self, server_id: str, service_name: str) -> Dict:
        """Restart a Windows service via SSH"""
        result = {
            'success': False,
            'message': '',
            'restart_time': datetime.utcnow().isoformat()
        }

        if not Config.AUTO_RESTART_ENABLED:
            result['message'] = 'Auto restart is disabled'
            return result

        if not self.can_restart(server_id, service_name):
            key = f"{server_id}_{service_name}"
            history = self._restart_history.get(key, {})
            last_restart = history.get('last_restart', datetime.utcnow())
            remaining = Config.RESTART_COOLDOWN_SECONDS - (datetime.utcnow() - last_restart).seconds
            result['message'] = f'Cooldown active, {remaining}s remaining'
            return result

        # Try to restart using sc command
        stop_cmd = f'sc stop "{service_name}"'
        start_cmd = f'sc start "{service_name}"'

        # Execute stop command
        stop_output = self.exec_ssh_command(server_id, stop_cmd, timeout=30)

        # Wait a moment
        import time
        time.sleep(3)

        # Execute start command
        start_output = self.exec_ssh_command(server_id, start_cmd, timeout=30)

        if start_output and 'START_PENDING' in start_output.upper():
            result['success'] = True
            result['message'] = 'Service restart initiated'
        elif start_output and 'RUNNING' in start_output.upper():
            result['success'] = True
            result['message'] = 'Service restarted successfully'
        else:
            result['message'] = f'Restart failed: {start_output or "No response"}'

        # Record restart history
        key = f"{server_id}_{service_name}"
        self._restart_history[key] = {
            'last_restart': datetime.utcnow(),
            'success': result['success'],
            'message': result['message']
        }

        return result

    def restart_windows_process(self, server_id: str, process_name: str) -> Dict:
        """Restart a Windows process via SSH"""
        result = {
            'success': False,
            'message': '',
            'restart_time': datetime.utcnow().isoformat()
        }

        if not Config.AUTO_RESTART_ENABLED:
            result['message'] = 'Auto restart is disabled'
            return result

        if not self.can_restart(server_id, process_name):
            key = f"{server_id}_{process_name}"
            history = self._restart_history.get(key, {})
            last_restart = history.get('last_restart', datetime.utcnow())
            remaining = Config.RESTART_COOLDOWN_SECONDS - (datetime.utcnow() - last_restart).seconds
            result['message'] = f'Cooldown active, {remaining}s remaining'
            return result

        # Get process path from settings
        server = SERVERS.get(server_id, {})
        acc_drive = server.get('acc_drive', 'D')

        # Common ACC process paths - each process has its own subdirectory
        process_paths = {
            'ACC.Server': f'{acc_drive}:\\ACC\\ACC.Server\\ACC.Server.exe',
            'ACC.MQ': f'{acc_drive}:\\ACC\\ACC.MQ\\ACC.MQ.exe',
            'Pack.Server': f'{acc_drive}:\\ACC\\ACC.Packing.Server\\Pack.Server.exe',
            'ACC.LogReader': f'{acc_drive}:\\ACC\\ACC.Server\\ACC.LogReader.exe',
            'ACC.Packing': f'{acc_drive}:\\ACC\\ACC.Packing\\ACC.Packing.exe'
        }

        exe_path = process_paths.get(process_name)
        if not exe_path:
            result['message'] = f'Unknown process: {process_name}'
            return result

        # Kill existing process
        kill_cmd = f'taskkill /F /IM "{process_name}.exe" 2>nul'
        kill_output = self.exec_ssh_command(server_id, kill_cmd, timeout=10)
        print(f"[AutoRestart] Kill {process_name}: {kill_output or 'N/A'}")

        # Wait a moment
        import time
        time.sleep(2)

        # Start process using PowerShell Start-Process (more reliable via SSH)
        # Use -WindowStyle Hidden to run in background
        start_cmd = f'powershell -Command "Start-Process -FilePath \'{exe_path}\' -WindowStyle Hidden"'
        start_output = self.exec_ssh_command(server_id, start_cmd, timeout=15)
        print(f"[AutoRestart] Start {process_name}: {start_output or 'OK'}")

        # Verify process started
        time.sleep(3)
        check_cmd = f'tasklist /FI "IMAGENAME eq {process_name}.exe" /NH'
        check_output = self.exec_ssh_command(server_id, check_cmd, timeout=10)
        # Safe print to avoid encoding issues
        safe_output = (check_output or 'N/A').encode('ascii', errors='replace').decode('ascii')
        print(f"[AutoRestart] Check {process_name}: {safe_output}")

        if check_output and process_name.lower() in check_output.lower():
            result['success'] = True
            result['message'] = 'Process restarted successfully'
        else:
            result['message'] = f'Process restart failed'

        # Record restart history
        key = f"{server_id}_{process_name}"
        self._restart_history[key] = {
            'last_restart': datetime.utcnow(),
            'success': result['success'],
            'message': result['message']
        }

        return result

    def restart_linux_container(self, server_id: str, container_name: str) -> Dict:
        """Restart a Docker container via SSH"""
        result = {
            'success': False,
            'message': '',
            'restart_time': datetime.utcnow().isoformat()
        }

        if not Config.AUTO_RESTART_ENABLED:
            result['message'] = 'Auto restart is disabled'
            return result

        if not self.can_restart(server_id, container_name):
            key = f"{server_id}_{container_name}"
            history = self._restart_history.get(key, {})
            last_restart = history.get('last_restart', datetime.utcnow())
            remaining = Config.RESTART_COOLDOWN_SECONDS - (datetime.utcnow() - last_restart).seconds
            result['message'] = f'Cooldown active, {remaining}s remaining'
            return result

        client = self.get_ssh_client(server_id)
        if not client:
            result['message'] = 'Cannot connect to server'
            return result

        try:
            # Restart container
            restart_cmd = f'docker restart {container_name}'
            stdin, stdout, stderr = client.exec_command(restart_cmd, timeout=60)
            exit_code = stdout.channel.recv_exit_status()

            if exit_code == 0:
                result['success'] = True
                result['message'] = 'Container restarted successfully'
            else:
                error = stderr.read().decode('utf-8', errors='ignore')
                result['message'] = f'Container restart failed: {error}'

        except Exception as e:
            result['message'] = f'Error: {str(e)}'
        finally:
            client.close()

        # Record restart history
        key = f"{server_id}_{container_name}"
        self._restart_history[key] = {
            'last_restart': datetime.utcnow(),
            'success': result['success'],
            'message': result['message']
        }

        return result

    def auto_restart_stopped_item(self, server_id: str, item_name: str,
                                   item_type: str) -> Optional[Dict]:
        """Automatically restart a stopped process/service/container"""
        if item_type == 'service':
            return self.restart_windows_service(server_id, item_name)
        elif item_type == 'process':
            return self.restart_windows_process(server_id, item_name)
        elif item_type == 'container':
            return self.restart_linux_container(server_id, item_name)
        return None

    # ============ Log Error Reading Methods ============

    def get_today_error_logs(self, server_id: str, service_name: str = None) -> List[Dict]:
        """Get today's error logs for a server/service"""
        if server_id not in SERVERS:
            return []

        server = SERVERS[server_id]
        log_path = server.get('log_path', '')
        os_type = server.get('os', 'windows')
        today = datetime.now().strftime('%Y-%m-%d')

        errors = []

        if os_type == 'windows':
            errors = self._get_windows_error_logs(server_id, log_path, service_name, today)
        else:
            errors = self._get_linux_error_logs(server_id, log_path, service_name, today)

        return errors

    def _get_windows_error_logs(self, server_id: str, log_path: str,
                                 service_name: str, date_str: str) -> List[Dict]:
        """Get error logs from Windows server for today"""
        errors = []

        # Build log file pattern
        if service_name:
            # Service-specific log: ServiceName_YYYY-MM-DD.log or ServiceName.log
            log_patterns = [
                f'{log_path}\\{service_name}_{date_str}.log',
                f'{log_path}\\{service_name}.log'
            ]
        else:
            # General ACC log
            log_patterns = [
                f'{log_path}\\ACC.Server_{date_str}.log',
                f'{log_path}\\ACC.Server.log'
            ]

        for log_file in log_patterns:
            # Use findstr to search for errors in log file
            cmd = f'findstr /I /C:"Error" /C:"Exception" /C:"Failed" /C:"ORA-" "{log_file}" 2>nul | more +0'
            output = self.exec_ssh_command(server_id, cmd, timeout=15)

            if output:
                lines = output.strip().split('\n')
                for line in lines[:20]:  # Limit to 20 errors
                    line = line.strip()
                    if line and len(line) > 10:
                        # Try to extract timestamp
                        timestamp = self._extract_timestamp(line)
                        errors.append({
                            'message': line[:300],  # Limit message length
                            'level': self._classify_error_level(line),
                            'timestamp': timestamp or date_str,
                            'source': service_name or 'ACC.Server'
                        })
                break  # Stop after finding a valid log file

        return errors

    def _get_linux_error_logs(self, server_id: str, log_path: str,
                               container_name: str, date_str: str) -> List[Dict]:
        """Get error logs from Linux server for today"""
        errors = []

        client = self.get_ssh_client(server_id)
        if not client:
            return errors

        try:
            # Get Docker container logs for today
            if container_name:
                cmd = f'docker logs {container_name} --since {date_str}T00:00:00 2>&1 | grep -iE "error|exception|failed" | tail -20'
            else:
                cmd = f'grep -iE "error|exception|failed" {log_path}/*.log 2>/dev/null | tail -20'

            stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
            output = stdout.read().decode('utf-8', errors='ignore')

            if output:
                lines = output.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 10:
                        timestamp = self._extract_timestamp(line)
                        errors.append({
                            'message': line[:300],
                            'level': self._classify_error_level(line),
                            'timestamp': timestamp or date_str,
                            'source': container_name or 'system'
                        })

        except Exception as e:
            print(f"Error reading Linux logs: {e}")
        finally:
            client.close()

        return errors

    def _extract_timestamp(self, log_line: str) -> Optional[str]:
        """Extract timestamp from log line"""
        # Common timestamp patterns
        patterns = [
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',  # 2026-01-31 10:30:45
            r'(\d{2}:\d{2}:\d{2})',  # 10:30:45
            r'\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\]',  # [2026-01-31T10:30:45]
        ]

        for pattern in patterns:
            match = re.search(pattern, log_line)
            if match:
                return match.group(1)

        return None

    def _classify_error_level(self, message: str) -> str:
        """Classify error level based on message content"""
        message_lower = message.lower()

        critical_keywords = ['ora-00600', 'ora-04031', 'outofmemoryexception', 'crash', 'fatal']
        error_keywords = ['exception', 'error', 'ora-', 'failed']
        warning_keywords = ['warning', 'timeout', 'retry']

        for keyword in critical_keywords:
            if keyword in message_lower:
                return 'critical'

        for keyword in error_keywords:
            if keyword in message_lower:
                return 'error'

        for keyword in warning_keywords:
            if keyword in message_lower:
                return 'warning'

        return 'info'

    # ============ Alert Info Methods ============

    def get_process_alert_info(self, server_id: str, process_name: str,
                                process_type: str = 'process') -> Dict:
        """Get alert info for a process/service including errors and restart status"""
        alert_info = {
            'has_alert': False,
            'errors': [],
            'restart_info': None,
            'last_update': datetime.utcnow().isoformat()
        }

        # Get today's errors for this process
        errors = self.get_today_error_logs(server_id, process_name)
        if errors:
            alert_info['has_alert'] = True
            alert_info['errors'] = errors[:5]  # Limit to 5 errors

        # Get restart history
        key = f"{server_id}_{process_name}"
        history = self._restart_history.get(key)
        if history:
            alert_info['has_alert'] = True
            alert_info['restart_info'] = {
                'last_restart': history.get('last_restart', datetime.utcnow()).isoformat(),
                'success': history.get('success', False),
                'message': history.get('message', '')
            }

        return alert_info

    def check_and_auto_restart(self, server_id: str, processes: List[Dict]) -> List[Dict]:
        """Check processes and auto restart stopped ones, return updated list with alerts"""
        updated_processes = []

        for proc in processes:
            proc_name = proc.get('name', '')
            proc_status = proc.get('status', '')
            proc_type = proc.get('type', 'process')

            # Add alert info to each process
            alert_info = self.get_process_alert_info(server_id, proc_name, proc_type)
            proc['has_alert'] = alert_info['has_alert']
            proc['alert_info'] = alert_info

            # Auto restart if stopped
            if proc_status == 'stopped' and Config.AUTO_RESTART_ENABLED:
                # Skip Oracle - it's a database, not a restartable process
                if proc_name.lower() == 'oracle':
                    updated_processes.append(proc)
                    continue

                restart_result = self.auto_restart_stopped_item(
                    server_id, proc_name, proc_type
                )

                if restart_result:
                    proc['has_alert'] = True
                    if not proc.get('alert_info'):
                        proc['alert_info'] = alert_info

                    proc['alert_info']['restart_info'] = {
                        'last_restart': restart_result.get('restart_time'),
                        'success': restart_result.get('success', False),
                        'message': restart_result.get('message', '')
                    }

                    # If restart was successful, update status after verification
                    if restart_result.get('success'):
                        # Re-check status after a short delay
                        import time
                        time.sleep(2)

            updated_processes.append(proc)

        return updated_processes
