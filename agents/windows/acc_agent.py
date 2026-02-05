# -*- coding: utf-8 -*-
"""
ACC Monitor - Windows Agent
Collects server metrics and sends to monitoring center

Usage:
    1. Copy this file to target Windows server
    2. Create config.json with server settings
    3. Install dependencies: pip install psutil requests
    4. Run: python acc_agent.py

    For production, install as Windows Service using NSSM or similar
"""
import os
import sys
import time
import json
import socket
import logging
import subprocess
import requests
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Default configuration
DEFAULT_CONFIG = {
    'server_url': 'http://localhost:5000',  # Monitor center URL
    'server_id': 'local',  # This server's ID
    'report_interval': 10,  # Seconds between reports
    'processes': [
        'Pack.Server',
        'ACC.Server',
        'ACC.MQ',
        'ACC.LogReader',
        'ACC.Packing'
    ],
    'oracle_service': 'OracleServiceXE',  # Oracle Windows service name
    'log_path': 'E:\\ACC\\ACC\\Log',
    'log_level': 'INFO',
    'auto_restart': False,  # Enable auto restart of stopped processes
    'restart_cooldown': 300,  # Seconds between restarts of same process
    'restart_commands': {}  # Custom restart commands per process
}

# Get script directory for relative paths
SCRIPT_DIR = Path(__file__).parent.absolute()


def setup_logging(log_level: str = 'INFO'):
    """Setup logging configuration"""
    log_file = SCRIPT_DIR / 'acc_agent.log'

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


class AccAgent:
    """Windows monitoring agent for ACC services"""

    def __init__(self, config: Dict):
        self.config = config
        self.server_url = config['server_url']
        self.server_id = config['server_id']
        self.logger = setup_logging(config.get('log_level', 'INFO'))
        self.last_restart_times: Dict[str, float] = {}  # Track restart cooldowns

        # Try to import WMI (optional, for Oracle service check)
        try:
            import wmi
            self.wmi = wmi.WMI()
            self.has_wmi = True
        except ImportError:
            self.wmi = None
            self.has_wmi = False
            self.logger.warning("WMI module not available, Oracle service check disabled")

    def get_cpu_usage(self) -> float:
        """Get CPU usage percentage"""
        try:
            return psutil.cpu_percent(interval=1)
        except Exception as e:
            self.logger.error(f"Error getting CPU usage: {e}")
            return 0.0

    def get_memory_usage(self) -> float:
        """Get memory usage percentage"""
        try:
            mem = psutil.virtual_memory()
            return round(mem.percent, 2)
        except Exception as e:
            self.logger.error(f"Error getting memory usage: {e}")
            return 0.0

    def get_disk_usage(self, drive: str = 'C:') -> float:
        """Get disk usage percentage"""
        try:
            disk = psutil.disk_usage(drive)
            return round(disk.percent, 2)
        except Exception as e:
            self.logger.error(f"Error getting disk usage for {drive}: {e}")
            return 0.0

    def check_process_by_name(self, process_name: str) -> Optional[Dict]:
        """
        Check if a process is running by name
        Returns process info if found, None otherwise
        """
        try:
            # Handle .exe extension
            search_name = process_name.replace('.exe', '').lower()

            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'create_time']):
                try:
                    proc_name = proc.info['name']
                    if proc_name:
                        # Match process name (with or without .exe)
                        proc_base = proc_name.replace('.exe', '').lower()
                        if search_name == proc_base or search_name in proc_base:
                            # Get CPU percent (need to call it twice for accurate reading)
                            try:
                                cpu = proc.cpu_percent(interval=0.1)
                            except:
                                cpu = 0.0

                            # Get memory in MB
                            mem_mb = 0.0
                            if proc.info['memory_info']:
                                mem_mb = round(proc.info['memory_info'].rss / 1024 / 1024, 2)

                            return {
                                'name': process_name,
                                'status': 'running',
                                'pid': proc.info['pid'],
                                'cpu': cpu,
                                'memory': mem_mb,
                                'uptime': int(time.time() - proc.info['create_time']) if proc.info['create_time'] else 0
                            }
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

        except Exception as e:
            self.logger.error(f"Error checking process {process_name}: {e}")

        return None

    def check_processes(self) -> List[Dict]:
        """Check status of all monitored processes"""
        processes = []
        monitored = self.config.get('processes', [])

        for proc_name in monitored:
            proc_info = self.check_process_by_name(proc_name)

            if proc_info:
                processes.append(proc_info)
            else:
                # Process not running
                processes.append({
                    'name': proc_name,
                    'status': 'stopped',
                    'pid': 0,
                    'cpu': 0,
                    'memory': 0,
                    'uptime': 0
                })

        return processes

    def check_oracle_process(self) -> Dict:
        """Check Oracle process/service status"""
        # First try to find oracle.exe process
        oracle_info = self.check_process_by_name('oracle')
        if oracle_info:
            oracle_info['name'] = 'Oracle'
            return oracle_info

        # Try TNSLSNR (listener)
        listener_info = self.check_process_by_name('tnslsnr')
        if listener_info:
            return {
                'name': 'Oracle',
                'status': 'running',
                'pid': listener_info['pid'],
                'cpu': listener_info['cpu'],
                'memory': listener_info['memory'],
                'uptime': listener_info.get('uptime', 0),
                'note': 'Listener running'
            }

        # Try WMI service check if available
        if self.has_wmi:
            try:
                service_name = self.config.get('oracle_service', 'OracleServiceXE')
                services = self.wmi.Win32_Service(Name=service_name)
                if services:
                    service = services[0]
                    is_running = service.State == 'Running'
                    return {
                        'name': 'Oracle',
                        'status': 'running' if is_running else 'stopped',
                        'pid': service.ProcessId if is_running else 0,
                        'cpu': 0,
                        'memory': 0,
                        'start_mode': service.StartMode
                    }
            except Exception as e:
                self.logger.error(f"Error checking Oracle service via WMI: {e}")

        return {
            'name': 'Oracle',
            'status': 'unknown',
            'pid': 0,
            'cpu': 0,
            'memory': 0
        }

    def scan_recent_logs(self, minutes: int = 5) -> List[Dict]:
        """Scan recent log files for errors"""
        alerts = []
        log_path = Path(self.config.get('log_path', ''))

        if not log_path.exists():
            return alerts

        error_keywords = ['Exception', 'Error', 'ORA-', 'Failed', 'Critical']
        cutoff_time = time.time() - (minutes * 60)

        try:
            for log_file in log_path.glob('*.log'):
                try:
                    if log_file.stat().st_mtime < cutoff_time:
                        continue

                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        # Read last 100 lines
                        lines = f.readlines()[-100:]

                        for line in lines:
                            for keyword in error_keywords:
                                if keyword.lower() in line.lower():
                                    alerts.append({
                                        'file': log_file.name,
                                        'keyword': keyword,
                                        'message': line.strip()[:200],
                                        'timestamp': datetime.now().isoformat()
                                    })
                                    break
                except Exception as e:
                    self.logger.debug(f"Error reading log file {log_file}: {e}")

        except Exception as e:
            self.logger.error(f"Error scanning logs: {e}")

        return alerts[:10]  # Limit to 10 alerts

    def restart_process(self, process_name: str) -> bool:
        """Attempt to restart a stopped process"""
        if not self.config.get('auto_restart', False):
            return False

        # Check cooldown
        cooldown = self.config.get('restart_cooldown', 300)
        last_restart = self.last_restart_times.get(process_name, 0)
        if time.time() - last_restart < cooldown:
            self.logger.info(f"Skipping restart of {process_name}, cooldown active")
            return False

        # Get restart command
        restart_commands = self.config.get('restart_commands', {})

        if process_name in restart_commands:
            cmd = restart_commands[process_name]
        else:
            # Default: try to start as Windows service
            cmd = f'net start "{process_name}"'

        try:
            self.logger.info(f"Attempting to restart {process_name}")
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            self.last_restart_times[process_name] = time.time()

            if result.returncode == 0:
                self.logger.info(f"Successfully restarted {process_name}")
                return True
            else:
                self.logger.error(f"Failed to restart {process_name}: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Error restarting {process_name}: {e}")
            return False

    def collect_metrics(self) -> Dict:
        """Collect all metrics for reporting"""
        hostname = socket.gethostname()

        # Get process status
        processes = self.check_processes()

        # Add Oracle check
        oracle_status = self.check_oracle_process()
        if oracle_status['status'] != 'unknown':
            # Check if Oracle is already in the list
            oracle_exists = any(p['name'].lower() == 'oracle' for p in processes)
            if not oracle_exists:
                processes.append(oracle_status)
            else:
                # Update existing Oracle entry
                for i, p in enumerate(processes):
                    if p['name'].lower() == 'oracle':
                        processes[i] = oracle_status
                        break

        # Check for stopped processes and attempt restart
        for proc in processes:
            if proc['status'] == 'stopped':
                self.restart_process(proc['name'])

        # Scan for log errors
        alerts = self.scan_recent_logs()

        return {
            'server_id': self.server_id,
            'hostname': hostname,
            'timestamp': datetime.utcnow().isoformat(),
            'resources': {
                'cpu_usage': self.get_cpu_usage(),
                'memory_usage': self.get_memory_usage(),
                'disk_usage': self.get_disk_usage()
            },
            'processes': processes,
            'alerts': alerts
        }

    def report_metrics(self, metrics: Dict) -> bool:
        """Send metrics to monitoring center"""
        try:
            url = f"{self.server_url}/api/agent/report"
            response = requests.post(
                url,
                json=metrics,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
            self.logger.debug("Metrics reported successfully")
            return True
        except requests.exceptions.ConnectionError:
            self.logger.warning(f"Cannot connect to monitoring center: {self.server_url}")
            return False
        except requests.exceptions.Timeout:
            self.logger.warning("Timeout connecting to monitoring center")
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error reporting metrics: {e}")
            return False

    def run(self):
        """Main agent loop"""
        self.logger.info("=" * 50)
        self.logger.info(f"ACC Agent starting...")
        self.logger.info(f"Server ID: {self.server_id}")
        self.logger.info(f"Hostname: {socket.gethostname()}")
        self.logger.info(f"Report URL: {self.server_url}")
        self.logger.info(f"Report interval: {self.config['report_interval']}s")
        self.logger.info(f"Monitoring processes: {self.config.get('processes', [])}")
        self.logger.info(f"Auto restart: {self.config.get('auto_restart', False)}")
        self.logger.info("=" * 50)

        consecutive_failures = 0

        while True:
            try:
                metrics = self.collect_metrics()
                success = self.report_metrics(metrics)

                if success:
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1

                # Log summary
                processes = metrics['processes']
                running = sum(1 for p in processes if p['status'] == 'running')
                stopped = sum(1 for p in processes if p['status'] == 'stopped')
                unknown = len(processes) - running - stopped

                status_emoji = '✓' if stopped == 0 else '!'
                self.logger.info(
                    f"[{status_emoji}] CPU: {metrics['resources']['cpu_usage']}% | "
                    f"Memory: {metrics['resources']['memory_usage']}% | "
                    f"Disk: {metrics['resources']['disk_usage']}% | "
                    f"Processes: {running} up, {stopped} down"
                )

                # Alert for stopped processes
                for p in processes:
                    if p['status'] == 'stopped':
                        self.logger.warning(f"[ALERT] Process {p['name']} is STOPPED!")

                # If too many consecutive failures, log warning
                if consecutive_failures >= 5:
                    self.logger.warning(
                        f"Cannot reach monitoring center after {consecutive_failures} attempts. "
                        "Continuing to collect metrics locally..."
                    )

            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")

            time.sleep(self.config['report_interval'])


def load_config() -> Dict:
    """Load configuration from file if exists, otherwise use defaults"""
    config = DEFAULT_CONFIG.copy()
    config_file = SCRIPT_DIR / 'config.json'

    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                config.update(user_config)
                print(f"Loaded configuration from {config_file}")
        except Exception as e:
            print(f"Error loading config file: {e}, using defaults")
    else:
        # Create sample config file
        print(f"Creating sample config file at {config_file}")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)

    return config


def main():
    """Entry point"""
    print("ACC Monitor Agent - Windows Edition")
    print("=" * 40)

    # Check dependencies
    try:
        import psutil
        import requests
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install: pip install psutil requests")
        sys.exit(1)

    config = load_config()
    agent = AccAgent(config)

    try:
        agent.run()
    except KeyboardInterrupt:
        print("\nAgent stopped by user")
    except Exception as e:
        print(f"Agent error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
