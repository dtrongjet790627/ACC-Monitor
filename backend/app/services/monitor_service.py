# -*- coding: utf-8 -*-
"""
ACC Monitor - Server and Process Monitoring Service
Uses Agent data when available, falls back to SSH data otherwise
Supports automatic reconnection detection and recovery
"""
import os
import paramiko
import re
import subprocess
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Callable
from config.settings import SERVERS, SSH_CREDENTIALS, SSH_PORTS, Config
from app.services.agent_data_service import agent_data_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MonitorService:
    """Service for monitoring servers and processes with reconnection support"""

    def __init__(self):
        self._ssh_clients: Dict[str, paramiko.SSHClient] = {}
        self.agent_data = agent_data_service
        # Track restart history and alerts
        self._restart_history: Dict[str, Dict] = {}  # {server_id_process: {last_restart, result, ...}}
        self._alert_cache: Dict[str, Dict] = {}  # {server_id: {alerts, last_update}}

        # Reconnection probe settings
        self._probe_interval = 15  # seconds between probes for offline servers
        self._last_probe_times: Dict[str, datetime] = {}  # {server_id: last_probe_time}
        self._probe_retry_count: Dict[str, int] = {}  # {server_id: retry_count}
        self._max_probe_retries = 3  # max consecutive probe failures before backing off

        # SSH connection cache with timeout
        self._ssh_connection_status: Dict[str, Dict] = {}  # {server_id: {status, last_check, ...}}

        # Register reconnection callback
        self.agent_data.register_reconnection_callback(self._on_server_reconnected)

    def _on_server_reconnected(self, server_id: str, offline_duration: float) -> None:
        """Callback when a server reconnects after being offline"""
        logger.info(f"[MonitorService] Server {server_id} reconnected after {offline_duration:.1f}s")
        # Reset probe retry count
        self._probe_retry_count[server_id] = 0
        # Clear SSH connection status cache to force fresh check
        if server_id in self._ssh_connection_status:
            del self._ssh_connection_status[server_id]

    def _get_or_create_ssh_client(self, server_id: str) -> Optional[paramiko.SSHClient]:
        """Get cached SSH client or create new one with connection pooling"""
        # Check if we have a cached client that's still valid
        if server_id in self._ssh_clients:
            client = self._ssh_clients[server_id]
            try:
                # Test if connection is still alive
                transport = client.get_transport()
                if transport and transport.is_active():
                    return client
            except:
                pass
            # Connection dead, remove from cache
            try:
                client.close()
            except:
                pass
            del self._ssh_clients[server_id]

        # Create new connection
        if server_id not in SERVERS:
            return None

        server = SERVERS[server_id]
        ip = server['ip']
        os_type = server.get('os', 'windows')
        creds = SSH_CREDENTIALS.get(os_type, SSH_CREDENTIALS['windows'])
        ssh_port = SSH_PORTS.get(server_id, 22)

        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            key_file = creds.get('key_file')
            if not key_file or not os.path.exists(key_file):
                return None

            # Load private key
            private_key = None
            try:
                private_key = paramiko.RSAKey.from_private_key_file(key_file)
            except paramiko.SSHException:
                try:
                    private_key = paramiko.Ed25519Key.from_private_key_file(key_file)
                except:
                    pass

            if not private_key:
                return None

            client.connect(
                hostname=ip,
                port=ssh_port,
                username=creds['username'],
                pkey=private_key,
                timeout=10,
                banner_timeout=15,
                auth_timeout=10
            )

            # Cache the client
            self._ssh_clients[server_id] = client
            self._update_ssh_connection_status(server_id, True)
            return client
        except Exception as e:
            logger.debug(f"Paramiko connection failed for {ip}: {e}")
            self._update_ssh_connection_status(server_id, False, str(e))
            return None

    def exec_ssh_command(self, server_id: str, command: str, timeout: int = 5, max_retries: int = 2) -> Optional[str]:
        """Execute SSH command using Paramiko with connection pooling and retry logic"""
        if server_id not in SERVERS:
            return None

        server = SERVERS[server_id]
        ip = server['ip']

        # Skip if server recently failed (avoid repeated connection attempts)
        ssh_status = self._ssh_connection_status.get(server_id, {})
        if not ssh_status.get('connected', True):
            consecutive_failures = ssh_status.get('consecutive_failures', 0)
            last_check = ssh_status.get('last_check')
            if consecutive_failures >= 3 and last_check:
                elapsed = (datetime.utcnow() - last_check).total_seconds()
                # Back off longer for servers with multiple failures
                backoff_time = min(60, 10 * consecutive_failures)
                if elapsed < backoff_time:
                    return None

        import time
        last_error = None

        for attempt in range(max_retries):
            try:
                client = self._get_or_create_ssh_client(server_id)
                if not client:
                    return None

                # Execute command with timeout
                stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
                output = stdout.read().decode('utf-8', errors='ignore').strip()

                if output:
                    self._update_ssh_connection_status(server_id, True)
                    return output

                # Empty output but no exception - try reading stderr
                err_output = stderr.read().decode('utf-8', errors='ignore').strip()
                if err_output:
                    logger.debug(f"SSH command stderr for {ip}: {err_output}")

                return None
            except Exception as e:
                last_error = e
                logger.debug(f"SSH command attempt {attempt+1} failed for {ip}: {e}")
                # Remove failed client from cache
                if server_id in self._ssh_clients:
                    try:
                        self._ssh_clients[server_id].close()
                    except:
                        pass
                    del self._ssh_clients[server_id]

                # Wait before retry (exponential backoff)
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))

        # All retries failed
        self._update_ssh_connection_status(server_id, False, str(last_error) if last_error else "unknown")
        return None

    def _update_ssh_connection_status(self, server_id: str, success: bool, error: str = None) -> None:
        """Update SSH connection status cache"""
        now = datetime.utcnow()
        prev_status = self._ssh_connection_status.get(server_id, {})
        was_offline = not prev_status.get('connected', True)

        self._ssh_connection_status[server_id] = {
            'connected': success,
            'last_check': now,
            'error': error,
            'consecutive_failures': 0 if success else prev_status.get('consecutive_failures', 0) + 1
        }

        # Detect SSH recovery
        if success and was_offline:
            logger.info(f"[SSH Recovery] Server {server_id} SSH connection restored")
            # Update agent data service with SSH fallback info
            self.agent_data.update_ssh_fallback_cache(server_id, 'available', {
                'source': 'ssh',
                'last_check': now.isoformat()
            })

    def probe_offline_server(self, server_id: str) -> Dict:
        """
        Actively probe an offline server to detect recovery
        Returns status dict with connection result
        """
        if server_id not in SERVERS:
            return {'success': False, 'error': 'Unknown server'}

        now = datetime.utcnow()

        # Check if we should probe (respect interval)
        last_probe = self._last_probe_times.get(server_id)
        if last_probe:
            elapsed = (now - last_probe).total_seconds()
            retry_count = self._probe_retry_count.get(server_id, 0)

            # Apply exponential backoff for repeated failures
            backoff_interval = self._probe_interval * (2 ** min(retry_count, 4))
            if elapsed < backoff_interval:
                return {'success': False, 'error': 'Probe too soon', 'next_probe_in': backoff_interval - elapsed}

        self._last_probe_times[server_id] = now

        server = SERVERS[server_id]
        os_type = server.get('os', 'windows')

        # Simple connectivity test
        if os_type == 'windows':
            # Try a quick command
            result = self.exec_ssh_command(server_id, 'echo OK', timeout=5)
        else:
            result = self.exec_ssh_command(server_id, 'echo OK', timeout=5)

        if result and 'OK' in result:
            # Server is reachable via SSH
            logger.info(f"[Probe Success] Server {server_id} is reachable via SSH")
            self._probe_retry_count[server_id] = 0

            # Update SSH fallback cache
            self.agent_data.update_ssh_fallback_cache(server_id, 'available', {
                'source': 'ssh_probe',
                'last_check': now.isoformat()
            })

            return {
                'success': True,
                'server_id': server_id,
                'method': 'ssh_probe',
                'timestamp': now.isoformat()
            }
        else:
            # Probe failed
            retry_count = self._probe_retry_count.get(server_id, 0) + 1
            self._probe_retry_count[server_id] = retry_count
            logger.warning(f"[Probe Failed] Server {server_id} unreachable (attempt {retry_count})")

            return {
                'success': False,
                'server_id': server_id,
                'retry_count': retry_count,
                'timestamp': now.isoformat()
            }

    def probe_all_offline_servers(self) -> List[Dict]:
        """Probe all offline servers to detect recovery"""
        results = []
        offline_servers = self.agent_data.get_offline_servers()

        # Also check servers that never had agent data
        for server_id in SERVERS.keys():
            if server_id not in offline_servers:
                if not self.agent_data.is_agent_online(server_id):
                    offline_servers.append(server_id)

        # Remove duplicates
        offline_servers = list(set(offline_servers))

        logger.info(f"[Probe] Probing {len(offline_servers)} offline servers: {offline_servers}")

        for server_id in offline_servers:
            result = self.probe_offline_server(server_id)
            results.append(result)

        return results

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
        Check Windows service status via SSH - OPTIMIZED: single command for all services
        """
        if server_id not in SERVERS:
            return []

        server_config = SERVERS.get(server_id, {})
        services = server_config.get('services', [])

        if not services:
            return []

        # Build service name list for query
        service_names = [svc.get('service_name', '') for svc in services if svc.get('service_name')]
        if not service_names:
            return []

        # Single SSH command to get all services at once
        # Use powershell to query multiple services efficiently
        service_filter = ','.join([f'"{s}"' for s in service_names])
        cmd = f'powershell -Command "Get-Service -Name {service_filter} -ErrorAction SilentlyContinue | Select-Object Name,Status | ConvertTo-Csv -NoTypeInformation"'
        output = self.exec_ssh_command(server_id, cmd, timeout=5)

        # Parse output and build results
        service_status_map = {}
        if output:
            lines = output.strip().split('\n')
            for line in lines[1:]:  # Skip header
                line = line.strip().strip('"')
                if '","' in line:
                    parts = line.split('","')
                    if len(parts) >= 2:
                        name = parts[0].strip('"')
                        status_str = parts[1].strip('"').upper()
                        if 'RUNNING' in status_str:
                            service_status_map[name.lower()] = 'running'
                        elif 'STOPPED' in status_str:
                            service_status_map[name.lower()] = 'stopped'
                        else:
                            service_status_map[name.lower()] = 'unknown'

        results = []
        for svc in services:
            service_name = svc.get('service_name', '')
            display_name = svc.get('display_name', service_name)
            if not service_name:
                continue

            status = service_status_map.get(service_name.lower(), 'unknown')
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
        process_display_names = server.get('process_display_names', {})  # Custom display names
        results = []

        # Get all processes at once with a single SSH command
        cmd = 'tasklist /FO CSV /NH'
        output = self.exec_ssh_command(server_id, cmd, timeout=5)

        for proc_name in processes_to_check:
            # Get custom display name if available
            display_name = process_display_names.get(proc_name, proc_name)

            # Oracle is handled separately
            if proc_name.lower() == 'oracle':
                results.append({
                    'name': display_name,
                    'process_name': proc_name,
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
                            'name': display_name,
                            'process_name': proc_name,
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
                        'name': display_name,
                        'process_name': proc_name,
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
        """Check process/container status on Linux server with optional resource metrics"""
        if server_id not in SERVERS:
            return []

        server = SERVERS[server_id]
        containers_to_monitor = server.get('containers', [])
        container_metrics_enabled = server.get('container_metrics', False)
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
                                'last_check': datetime.utcnow().isoformat(),
                                'type': 'container'
                            }

                # Get container resource metrics if enabled
                container_metrics = {}
                if container_metrics_enabled:
                    container_metrics = self._get_container_metrics(client, containers_to_monitor)

                # Only return containers that are in the monitor list
                for container_name in containers_to_monitor:
                    if container_name in all_containers:
                        container_data = all_containers[container_name]
                        # Add display name based on container type
                        if container_name == 'hulu-eai':
                            container_data['display_name'] = 'HULU EAI Container'
                        elif container_name == 'redis':
                            container_data['display_name'] = 'HULU EAI Redis'
                        else:
                            container_data['display_name'] = container_name

                        # Add metrics if available
                        if container_name in container_metrics:
                            container_data['metrics'] = container_metrics[container_name]
                        results.append(container_data)
                    else:
                        # Container not found
                        display_name = container_name
                        if container_name == 'hulu-eai':
                            display_name = 'HULU EAI Container'
                        elif container_name == 'redis':
                            display_name = 'HULU EAI Redis'
                        results.append({
                            'name': container_name,
                            'display_name': display_name,
                            'status': 'stopped',
                            'container_id': '',
                            'last_check': datetime.utcnow().isoformat(),
                            'type': 'container'
                        })
            except Exception as e:
                print(f"Error checking Linux processes: {e}")
            finally:
                client.close()
        else:
            # Return simulated data if cannot connect
            for container in containers_to_monitor:
                display_name = container
                if container == 'hulu-eai':
                    display_name = 'HULU EAI Container'
                elif container == 'redis':
                    display_name = 'HULU EAI Redis'
                results.append({
                    'name': container,
                    'display_name': display_name,
                    'status': 'unknown',
                    'container_id': '',
                    'last_check': datetime.utcnow().isoformat(),
                    'type': 'container'
                })

        return results

    def _get_container_metrics(self, client: paramiko.SSHClient, containers: List[str]) -> Dict[str, Dict]:
        """Get CPU, memory, and network I/O metrics for Docker containers"""
        metrics = {}

        try:
            # Use docker stats to get CPU and memory for all containers at once
            # Format: container_name|cpu_percent|mem_usage|mem_limit|net_io
            stats_cmd = 'docker stats --no-stream --format "{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|{{.NetIO}}"'
            stdin, stdout, stderr = client.exec_command(stats_cmd, timeout=10)
            output = stdout.read().decode('utf-8', errors='ignore')

            for line in output.strip().split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        name = parts[0].strip()
                        if name in containers:
                            # Parse CPU percentage (e.g., "0.50%")
                            cpu_str = parts[1].strip().replace('%', '')
                            try:
                                cpu_percent = round(float(cpu_str), 2)
                            except ValueError:
                                cpu_percent = 0.0

                            # Parse memory usage (e.g., "256MiB / 1GiB")
                            mem_str = parts[2].strip()
                            mem_used = 0
                            mem_limit = 0
                            mem_percent = 0.0
                            try:
                                mem_parts = mem_str.split('/')
                                if len(mem_parts) == 2:
                                    mem_used = self._parse_memory_string(mem_parts[0].strip())
                                    mem_limit = self._parse_memory_string(mem_parts[1].strip())
                                    if mem_limit > 0:
                                        mem_percent = round((mem_used / mem_limit) * 100, 2)
                            except (ValueError, IndexError):
                                pass

                            # Parse network I/O (e.g., "1.5GB / 2.3GB")
                            net_str = parts[3].strip()
                            net_rx = 0
                            net_tx = 0
                            try:
                                net_parts = net_str.split('/')
                                if len(net_parts) == 2:
                                    net_rx = self._parse_network_string(net_parts[0].strip())
                                    net_tx = self._parse_network_string(net_parts[1].strip())
                            except (ValueError, IndexError):
                                pass

                            metrics[name] = {
                                'cpu_percent': cpu_percent,
                                'memory_used_mb': round(mem_used / (1024 * 1024), 1) if mem_used > 0 else 0,
                                'memory_limit_mb': round(mem_limit / (1024 * 1024), 1) if mem_limit > 0 else 0,
                                'memory_percent': mem_percent,
                                'network_rx_mb': round(net_rx / (1024 * 1024), 2) if net_rx > 0 else 0,
                                'network_tx_mb': round(net_tx / (1024 * 1024), 2) if net_tx > 0 else 0
                            }
        except Exception as e:
            logger.debug(f"Error getting container metrics: {e}")

        return metrics

    def _parse_memory_string(self, mem_str: str) -> int:
        """Parse memory string like '256MiB' or '1.5GiB' to bytes"""
        mem_str = mem_str.upper()
        multipliers = {
            'B': 1,
            'KIB': 1024,
            'KB': 1000,
            'MIB': 1024 * 1024,
            'MB': 1000 * 1000,
            'GIB': 1024 * 1024 * 1024,
            'GB': 1000 * 1000 * 1000
        }
        for suffix, mult in multipliers.items():
            if suffix in mem_str:
                try:
                    value = float(mem_str.replace(suffix, '').strip())
                    return int(value * mult)
                except ValueError:
                    return 0
        return 0

    def _parse_network_string(self, net_str: str) -> int:
        """Parse network string like '1.5GB' or '256MB' to bytes"""
        return self._parse_memory_string(net_str)

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
        """Check Windows server resources via SSH - OPTIMIZED: single PowerShell command"""
        result = {
            'cpu_usage': 0,
            'memory_usage': 0,
            'disk_usage': 0,
            'last_check': datetime.utcnow().isoformat(),
            'data_source': 'none'
        }

        server_config = SERVERS.get(server_id, {})
        acc_drive = server_config.get('acc_drive', 'D')

        # Use WMIC commands for reliable CPU/Memory/Disk retrieval
        # WMIC is more reliable than PowerShell when executed via SSH as it avoids shell variable parsing issues
        # Note: WMIC CPU query takes ~1 second per core, so 15s timeout needed for servers with 6+ cores
        cpu_cmd = "wmic cpu get loadpercentage /format:value"
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
                    result['data_source'] = 'ssh'
            except (ValueError, IndexError):
                pass

        # Get Memory usage via WMIC
        mem_cmd = "wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /format:value"
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
                    result['data_source'] = 'ssh'
            except (ValueError, IndexError):
                pass

        # Get Disk usage via WMIC
        disk_cmd = f"wmic logicaldisk where DeviceID='{acc_drive}:' get Size,FreeSpace /format:value"
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
                    result['data_source'] = 'ssh'
            except (ValueError, IndexError):
                pass

        # Legacy PowerShell command kept as comment for reference
        # ps_cmd = f'''powershell -Command "$cpu=(Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average; ..."'''


        return result

    def _check_windows_resources_legacy(self, server_id: str) -> Dict:
        """Legacy method - kept for fallback. Check Windows server resources via multiple SSH calls"""
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
        cpu_output = self.exec_ssh_command(server_id, cpu_cmd, timeout=5)
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

        # Disk usage - for EAI server (163), monitor /home partition usage (Docker data location)
        if server_id == '163':
            # Simply use df to get /home partition usage percentage
            # Docker data is in /home/docker, so monitoring /home partition is sufficient
            disk_cmd = "df /home | tail -1 | awk '{print $5}' | tr -d '%'"
            disk_output = self.exec_ssh_command(server_id, disk_cmd, timeout=5)
            if disk_output:
                try:
                    result['disk_usage'] = round(float(disk_output.strip()), 1)
                    result['disk_type'] = 'docker_home'  # Mark as Docker /home monitoring
                except ValueError:
                    pass
        else:
            # Standard disk usage for other Linux servers
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

        # Note: Removed aggressive 15-second skip logic here
        # Now each API call will attempt to check services via SSH
        # The exec_ssh_command still has a 5-second cache to avoid multiple calls within same request

        # For Windows servers, try to use agent data first
        if os_type == 'windows':
            agent_online = self.agent_data.is_agent_online(server_id)
        else:
            agent_online = False

        # Check if we should use SSH fallback for offline agent
        use_ssh_fallback = False
        if not agent_online and self.agent_data.should_use_ssh_fallback(server_id):
            use_ssh_fallback = True
            logger.debug(f"[Fallback] Using SSH fallback for {server_id}")

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
        running_count = sum(1 for p in processes if p.get('status') == 'running')

        # Enhanced status determination with SSH fallback consideration
        if stopped_count > 0:
            status = 'error'
        elif unknown_count == len(processes) and len(processes) > 0:
            # All processes unknown - mark as offline (probe moved to background scheduler)
            status = 'offline'
        elif warning_count > 0:
            status = 'warning'
        elif running_count > 0:
            status = 'normal'
        else:
            # No running processes but not all unknown
            status = 'warning'

        # Get data source info
        data_source = 'ssh'
        if any(p.get('data_source') == 'agent' for p in processes):
            data_source = 'agent'
        elif all(p.get('data_source') == 'none' for p in processes):
            data_source = 'none'

        # Get connection state info
        conn_state = self.agent_data.get_connection_state(server_id)

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
            'last_check': datetime.utcnow().isoformat(),
            # Add reconnection info
            'connection_info': {
                'ssh_reachable': self._ssh_connection_status.get(server_id, {}).get('connected', None),
                'was_offline': conn_state.get('was_offline', False),
                'recovery_count': conn_state.get('recovery_count', 0),
                'last_recovery': conn_state.get('last_recovery').isoformat() if conn_state.get('last_recovery') else None
            }
        }

    def get_all_servers_status(self) -> List[Dict]:
        """Get status of all monitored servers using parallel execution"""
        results = []

        # Use ThreadPoolExecutor for parallel checking
        try:
            with ThreadPoolExecutor(max_workers=8) as executor:
                future_to_server = {
                    executor.submit(self._get_single_server_status, server_id): server_id
                    for server_id in SERVERS.keys()
                }

                try:
                    for future in as_completed(future_to_server, timeout=60):
                        server_id = future_to_server[future]
                        try:
                            result = future.result(timeout=30)
                            results.append(result)
                        except Exception as e:
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

    def _create_offline_result(self, server_id: str, server_config: Dict, os_type: str, reason: str = 'unknown') -> Dict:
        """Create offline status result for a server"""
        return {
            'id': server_id,
            'name': server_config['name'],
            'name_cn': server_config.get('name_cn', ''),
            'ip': server_config['ip'],
            'os_type': os_type,
            'status': 'offline',
            'processes': [],
            'cpu_usage': 0,
            'memory_usage': 0,
            'disk_usage': 0,
            'agent_online': False,
            'data_source': 'none',
            'offline_reason': reason,
            'last_check': datetime.utcnow().isoformat()
        }

    def _add_offline_server(self, results: List[Dict], server_id: str):
        """Add offline status for a server"""
        if any(r['id'] == server_id for r in results):
            return  # Already added
        server_config = SERVERS[server_id]
        results.append(self._create_offline_result(server_id, server_config, server_config.get('os', 'windows'), 'timeout'))

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
        stop_output = self.exec_ssh_command(server_id, stop_cmd, timeout=50)

        # Wait a moment
        import time
        time.sleep(3)

        # Execute start command
        start_output = self.exec_ssh_command(server_id, start_cmd, timeout=50)

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
