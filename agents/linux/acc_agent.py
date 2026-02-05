#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ACC Monitor - Linux Agent
Collects server metrics and Docker container status
"""
import os
import sys
import time
import json
import socket
import logging
import subprocess
import requests
from datetime import datetime
from pathlib import Path

# Configuration
CONFIG = {
    'server_url': 'http://172.17.10.xxx:5000',  # Monitor center URL
    'server_id': '163',  # This server's ID (EAI)
    'report_interval': 30,  # Seconds between reports
    'containers': ['hulu-eai', 'redis', 'portainer', 'frpc'],
    'log_path': '/var/eai/logs',
    'log_level': 'INFO'
}

# Setup logging
logging.basicConfig(
    level=getattr(logging, CONFIG['log_level']),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/acc_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AccLinuxAgent:
    """Linux monitoring agent for Docker containers"""

    def __init__(self, config):
        self.config = config
        self.server_url = config['server_url']
        self.server_id = config['server_id']

    def run_command(self, cmd):
        """Run shell command and return output"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout.strip()
        except Exception as e:
            logger.error(f"Error running command '{cmd}': {e}")
            return ""

    def get_cpu_usage(self):
        """Get CPU usage percentage"""
        try:
            output = self.run_command(
                "top -bn1 | grep 'Cpu(s)' | awk '{print $2}'"
            )
            return float(output) if output else 0
        except:
            return 0

    def get_memory_usage(self):
        """Get memory usage percentage"""
        try:
            output = self.run_command(
                "free | grep Mem | awk '{print $3/$2 * 100.0}'"
            )
            return round(float(output), 2) if output else 0
        except:
            return 0

    def get_disk_usage(self, path='/'):
        """Get disk usage percentage"""
        try:
            output = self.run_command(
                f"df {path} | tail -1 | awk '{{print $5}}' | tr -d '%'"
            )
            return float(output) if output else 0
        except:
            return 0

    def get_container_status(self):
        """Get Docker container status"""
        containers = []
        monitored = self.config['containers']

        for container_name in monitored:
            container_info = {
                'name': container_name,
                'status': 'unknown',
                'container_id': '',
                'cpu_percent': 0,
                'memory_usage': 0,
                'memory_limit': 0,
                'restart_count': 0
            }

            try:
                # Get container status
                inspect_cmd = f"docker inspect {container_name} 2>/dev/null"
                output = self.run_command(inspect_cmd)

                if output:
                    data = json.loads(output)
                    if data:
                        container = data[0]
                        state = container.get('State', {})

                        container_info['container_id'] = container.get('Id', '')[:12]
                        container_info['status'] = 'running' if state.get('Running') else 'stopped'
                        container_info['restart_count'] = container.get('RestartCount', 0)

                        # Get resource usage
                        stats_cmd = f"docker stats {container_name} --no-stream --format '{{{{.CPUPerc}}}}|{{{{.MemUsage}}}}'"
                        stats = self.run_command(stats_cmd)

                        if stats:
                            parts = stats.split('|')
                            if len(parts) >= 2:
                                cpu = parts[0].replace('%', '')
                                container_info['cpu_percent'] = float(cpu) if cpu else 0

                                # Parse memory (e.g., "256MiB / 1GiB")
                                mem_parts = parts[1].split('/')
                                if len(mem_parts) >= 2:
                                    container_info['memory_usage'] = self._parse_memory(mem_parts[0])
                                    container_info['memory_limit'] = self._parse_memory(mem_parts[1])
                else:
                    container_info['status'] = 'not_found'

            except Exception as e:
                logger.error(f"Error getting container {container_name} status: {e}")

            containers.append(container_info)

        return containers

    def _parse_memory(self, mem_str):
        """Parse memory string to MB"""
        mem_str = mem_str.strip().upper()
        try:
            if 'GIB' in mem_str or 'GB' in mem_str:
                return float(mem_str.replace('GIB', '').replace('GB', '').strip()) * 1024
            elif 'MIB' in mem_str or 'MB' in mem_str:
                return float(mem_str.replace('MIB', '').replace('MB', '').strip())
            elif 'KIB' in mem_str or 'KB' in mem_str:
                return float(mem_str.replace('KIB', '').replace('KB', '').strip()) / 1024
            else:
                return float(mem_str)
        except:
            return 0

    def scan_recent_logs(self, minutes=5):
        """Scan recent log files for errors"""
        alerts = []
        log_path = Path(self.config['log_path'])

        if not log_path.exists():
            return alerts

        error_keywords = ['Exception', 'Error', 'FATAL', 'CRITICAL', 'Failed']
        cutoff_time = time.time() - (minutes * 60)

        try:
            for log_file in log_path.glob('*.log'):
                if log_file.stat().st_mtime < cutoff_time:
                    continue

                # Use tail to get last 100 lines
                output = self.run_command(f"tail -n 100 {log_file}")

                for line in output.split('\n'):
                    for keyword in error_keywords:
                        if keyword.lower() in line.lower():
                            alerts.append({
                                'file': log_file.name,
                                'keyword': keyword,
                                'message': line[:200],
                                'timestamp': datetime.now().isoformat()
                            })
                            break
        except Exception as e:
            logger.error(f"Error scanning logs: {e}")

        return alerts

    def collect_metrics(self):
        """Collect all metrics"""
        return {
            'server_id': self.server_id,
            'hostname': socket.gethostname(),
            'timestamp': datetime.utcnow().isoformat(),
            'resources': {
                'cpu_usage': self.get_cpu_usage(),
                'memory_usage': self.get_memory_usage(),
                'disk_usage': self.get_disk_usage()
            },
            'containers': self.get_container_status(),
            'alerts': self.scan_recent_logs()
        }

    def report_metrics(self, metrics):
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
            logger.debug("Metrics reported successfully")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error reporting metrics: {e}")
            return False

    def run(self):
        """Main agent loop"""
        logger.info(f"ACC Linux Agent started for server {self.server_id}")
        logger.info(f"Reporting to {self.server_url}")

        while True:
            try:
                metrics = self.collect_metrics()
                self.report_metrics(metrics)

                # Log summary
                containers = metrics['containers']
                running = sum(1 for c in containers if c['status'] == 'running')
                stopped = len(containers) - running

                logger.info(
                    f"CPU: {metrics['resources']['cpu_usage']}% | "
                    f"Memory: {metrics['resources']['memory_usage']}% | "
                    f"Disk: {metrics['resources']['disk_usage']}% | "
                    f"Containers: {running} running, {stopped} stopped"
                )

                # Alert for stopped containers
                for c in containers:
                    if c['status'] == 'stopped':
                        logger.warning(f"Container {c['name']} is STOPPED!")

            except Exception as e:
                logger.error(f"Error in main loop: {e}")

            time.sleep(self.config['report_interval'])


def load_config():
    """Load configuration from file if exists"""
    config_file = Path('/etc/acc-agent/config.json')
    if config_file.exists():
        with open(config_file, 'r') as f:
            user_config = json.load(f)
            CONFIG.update(user_config)
    return CONFIG


if __name__ == '__main__':
    config = load_config()
    agent = AccLinuxAgent(config)

    try:
        agent.run()
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error(f"Agent error: {e}")
        sys.exit(1)
