# -*- coding: utf-8 -*-
"""
ACC Monitor - Agent Data Service
Manages real-time data from monitoring agents, handles offline detection
"""
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class AgentDataService:
    """Service for managing agent reported data"""

    # Singleton instance
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Store latest data from each agent
        # Key: server_id, Value: agent report data with timestamp
        self._agent_data: Dict[str, Dict] = {}

        # Store process data separately for quick access
        # Key: server_id, Value: list of process status
        self._process_data: Dict[str, List[Dict]] = {}

        # Timeout for considering agent offline (seconds)
        self.offline_timeout = 30

        self._initialized = True

    def update_agent_data(self, server_id: str, data: Dict) -> None:
        """
        Update agent data from a report
        Called when agent sends metrics to /api/agent/report
        """
        with self._lock:
            # Add received timestamp
            data['received_at'] = datetime.utcnow()
            data['agent_online'] = True

            self._agent_data[server_id] = data

            # Extract process data
            processes = data.get('processes', [])
            if processes:
                self._process_data[server_id] = processes

    def get_agent_data(self, server_id: str) -> Optional[Dict]:
        """Get latest agent data for a server"""
        data = self._agent_data.get(server_id)

        if data:
            # Check if agent is still online (received data within timeout)
            received_at = data.get('received_at')
            if received_at:
                elapsed = (datetime.utcnow() - received_at).total_seconds()
                data['agent_online'] = elapsed < self.offline_timeout
                data['last_seen_seconds'] = int(elapsed)

        return data

    def get_process_status(self, server_id: str) -> List[Dict]:
        """Get process status for a server from agent data"""
        return self._process_data.get(server_id, [])

    def is_agent_online(self, server_id: str) -> bool:
        """Check if agent for a server is online"""
        data = self._agent_data.get(server_id)

        if not data:
            return False

        received_at = data.get('received_at')
        if not received_at:
            return False

        elapsed = (datetime.utcnow() - received_at).total_seconds()
        return elapsed < self.offline_timeout

    def get_all_agents_status(self) -> List[Dict]:
        """Get status summary of all agents"""
        results = []

        for server_id, data in self._agent_data.items():
            received_at = data.get('received_at')
            if received_at:
                elapsed = (datetime.utcnow() - received_at).total_seconds()
                is_online = elapsed < self.offline_timeout
            else:
                elapsed = -1
                is_online = False

            results.append({
                'server_id': server_id,
                'hostname': data.get('hostname', ''),
                'agent_online': is_online,
                'last_seen_seconds': int(elapsed) if elapsed >= 0 else None,
                'last_report': received_at.isoformat() if received_at else None,
                'resources': data.get('resources', {}),
                'process_count': len(data.get('processes', []))
            })

        return results

    def get_servers_with_agent_data(self) -> Dict[str, bool]:
        """
        Get dict of server_id -> has_recent_agent_data
        Used to determine which servers should use agent data vs simulated
        """
        result = {}
        for server_id in self._agent_data.keys():
            result[server_id] = self.is_agent_online(server_id)
        return result

    def get_merged_server_status(self, server_id: str, config: Dict) -> Dict:
        """
        Get server status, using agent data if available, otherwise config defaults

        Args:
            server_id: Server identifier
            config: Server configuration from settings.py

        Returns:
            Server status dict with processes, resources, etc.
        """
        agent_data = self.get_agent_data(server_id)

        if agent_data and agent_data.get('agent_online'):
            # Use real agent data
            processes = agent_data.get('processes', [])
            resources = agent_data.get('resources', {})

            # Determine status based on processes
            stopped_count = sum(1 for p in processes if p.get('status') == 'stopped')
            if stopped_count > 0:
                status = 'error'
            elif resources.get('cpu_usage', 0) > 90 or resources.get('memory_usage', 0) > 90:
                status = 'warning'
            else:
                status = 'normal'

            return {
                'id': server_id,
                'name': config.get('name', f'Server {server_id}'),
                'name_cn': config.get('name_cn', ''),
                'ip': config.get('ip', ''),
                'os_type': config.get('os', 'windows'),
                'status': status,
                'processes': processes,
                'cpu_usage': resources.get('cpu_usage', 0),
                'memory_usage': resources.get('memory_usage', 0),
                'disk_usage': resources.get('disk_usage', 0),
                'agent_online': True,
                'data_source': 'agent',
                'last_check': agent_data.get('timestamp', datetime.utcnow().isoformat())
            }
        else:
            # No agent data or agent offline - return placeholder with offline status
            # The processes list comes from config, all marked as unknown
            processes_config = config.get('processes', [])
            processes = []
            for proc_name in processes_config:
                processes.append({
                    'name': proc_name,
                    'status': 'unknown',
                    'pid': 0,
                    'cpu': 0,
                    'memory': 0
                })

            # Check if we have stale agent data
            if agent_data:
                last_seen = agent_data.get('received_at')
                last_seen_str = last_seen.isoformat() if last_seen else None
            else:
                last_seen_str = None

            return {
                'id': server_id,
                'name': config.get('name', f'Server {server_id}'),
                'name_cn': config.get('name_cn', ''),
                'ip': config.get('ip', ''),
                'os_type': config.get('os', 'windows'),
                'status': 'offline',
                'processes': processes,
                'cpu_usage': 0,
                'memory_usage': 0,
                'disk_usage': 0,
                'agent_online': False,
                'data_source': 'none',
                'last_check': last_seen_str
            }


# Global singleton instance
agent_data_service = AgentDataService()
