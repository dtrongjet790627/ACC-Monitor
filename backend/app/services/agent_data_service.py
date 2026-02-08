# -*- coding: utf-8 -*-
"""
ACC Monitor - Agent Data Service
Manages real-time data from monitoring agents, handles offline detection
Supports reconnection detection and state recovery
"""
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentDataService:
    """Service for managing agent reported data with reconnection support"""

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

        # Track server connection states for reconnection detection
        # Key: server_id, Value: {'was_offline': bool, 'offline_since': datetime, 'recovery_count': int}
        self._connection_states: Dict[str, Dict] = {}

        # Reconnection event callbacks
        self._reconnection_callbacks: List[Callable] = []

        # SSH fallback status cache
        # Key: server_id, Value: {'status': str, 'last_check': datetime, 'data': dict}
        self._ssh_fallback_cache: Dict[str, Dict] = {}

        # SSH fallback cache timeout (seconds)
        self.ssh_cache_timeout = 60

        # Grace period after agent reconnects before considering stable (seconds)
        self.reconnection_grace_period = 10

        self._initialized = True

    def register_reconnection_callback(self, callback: Callable) -> None:
        """Register a callback to be called when a server reconnects"""
        if callback not in self._reconnection_callbacks:
            self._reconnection_callbacks.append(callback)

    def unregister_reconnection_callback(self, callback: Callable) -> None:
        """Unregister a reconnection callback"""
        if callback in self._reconnection_callbacks:
            self._reconnection_callbacks.remove(callback)

    def _notify_reconnection(self, server_id: str, offline_duration: float) -> None:
        """Notify all registered callbacks about a server reconnection"""
        for callback in self._reconnection_callbacks:
            try:
                callback(server_id, offline_duration)
            except Exception as e:
                logger.error(f"Error in reconnection callback for {server_id}: {e}")

    def update_agent_data(self, server_id: str, data: Dict) -> None:
        """
        Update agent data from a report
        Called when agent sends metrics to /api/agent/report
        Detects reconnection events and notifies callbacks
        """
        with self._lock:
            now = datetime.utcnow()

            # Check if this is a reconnection (was offline, now receiving data)
            was_offline = False
            offline_duration = 0

            conn_state = self._connection_states.get(server_id, {})
            if conn_state.get('was_offline', False):
                was_offline = True
                offline_since = conn_state.get('offline_since')
                if offline_since:
                    offline_duration = (now - offline_since).total_seconds()

                # Log reconnection event
                logger.info(f"[Reconnection] Server {server_id} reconnected after {offline_duration:.1f}s offline")

                # Update connection state
                self._connection_states[server_id] = {
                    'was_offline': False,
                    'offline_since': None,
                    'recovery_count': conn_state.get('recovery_count', 0) + 1,
                    'last_recovery': now
                }

            # Add received timestamp
            data['received_at'] = now
            data['agent_online'] = True
            data['reconnected'] = was_offline
            data['offline_duration'] = offline_duration if was_offline else 0

            self._agent_data[server_id] = data

            # Extract process data
            processes = data.get('processes', [])
            if processes:
                self._process_data[server_id] = processes

            # Clear SSH fallback cache since we have fresh agent data
            if server_id in self._ssh_fallback_cache:
                del self._ssh_fallback_cache[server_id]

        # Notify reconnection callbacks outside the lock
        if was_offline and offline_duration > 0:
            self._notify_reconnection(server_id, offline_duration)

    def get_agent_data(self, server_id: str) -> Optional[Dict]:
        """Get latest agent data for a server"""
        data = self._agent_data.get(server_id)

        if data:
            # Check if agent is still online (received data within timeout)
            received_at = data.get('received_at')
            if received_at:
                now = datetime.utcnow()
                elapsed = (now - received_at).total_seconds()
                is_online = elapsed < self.offline_timeout
                data['agent_online'] = is_online
                data['last_seen_seconds'] = int(elapsed)

                # Track offline state transition
                if not is_online:
                    self._mark_server_offline(server_id, received_at)

        return data

    def _mark_server_offline(self, server_id: str, last_seen: datetime) -> None:
        """Mark a server as offline and track the offline state"""
        with self._lock:
            conn_state = self._connection_states.get(server_id, {})
            if not conn_state.get('was_offline', False):
                # First time going offline, record it
                self._connection_states[server_id] = {
                    'was_offline': True,
                    'offline_since': last_seen,
                    'recovery_count': conn_state.get('recovery_count', 0),
                    'last_recovery': conn_state.get('last_recovery')
                }
                logger.warning(f"[Offline] Server {server_id} went offline at {last_seen}")

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
        is_online = elapsed < self.offline_timeout

        # Track offline state
        if not is_online:
            self._mark_server_offline(server_id, received_at)

        return is_online

    def get_connection_state(self, server_id: str) -> Dict:
        """Get connection state info for a server"""
        return self._connection_states.get(server_id, {
            'was_offline': False,
            'offline_since': None,
            'recovery_count': 0,
            'last_recovery': None
        })

    def get_offline_servers(self) -> List[str]:
        """Get list of currently offline server IDs"""
        offline = []
        for server_id in self._agent_data.keys():
            if not self.is_agent_online(server_id):
                offline.append(server_id)
        return offline

    def update_ssh_fallback_cache(self, server_id: str, status: str, data: Dict) -> None:
        """
        Update SSH fallback cache for a server
        Used when agent is offline but SSH connection succeeds
        """
        with self._lock:
            self._ssh_fallback_cache[server_id] = {
                'status': status,
                'last_check': datetime.utcnow(),
                'data': data
            }
            logger.info(f"[SSH Fallback] Updated cache for {server_id}: status={status}")

    def get_ssh_fallback_data(self, server_id: str) -> Optional[Dict]:
        """
        Get SSH fallback data if available and not expired
        Returns None if cache expired or not available
        """
        cache = self._ssh_fallback_cache.get(server_id)
        if not cache:
            return None

        last_check = cache.get('last_check')
        if not last_check:
            return None

        elapsed = (datetime.utcnow() - last_check).total_seconds()
        if elapsed > self.ssh_cache_timeout:
            # Cache expired
            return None

        return cache

    def should_use_ssh_fallback(self, server_id: str) -> bool:
        """
        Determine if SSH fallback should be used for a server
        Returns True if agent is offline and SSH might provide data
        """
        if self.is_agent_online(server_id):
            return False

        # Check if we have recent SSH fallback data
        fallback = self.get_ssh_fallback_data(server_id)
        if fallback and fallback.get('status') == 'available':
            return True

        # No recent SSH data, but agent is offline so we should try SSH
        return True

    def clear_server_data(self, server_id: str) -> None:
        """Clear all cached data for a server (for testing/reset)"""
        with self._lock:
            if server_id in self._agent_data:
                del self._agent_data[server_id]
            if server_id in self._process_data:
                del self._process_data[server_id]
            if server_id in self._connection_states:
                del self._connection_states[server_id]
            if server_id in self._ssh_fallback_cache:
                del self._ssh_fallback_cache[server_id]

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

    def get_all_connection_states(self) -> Dict[str, Dict]:
        """Get connection states for all known servers"""
        result = {}
        for server_id in self._agent_data.keys():
            result[server_id] = {
                'agent_online': self.is_agent_online(server_id),
                'connection_state': self.get_connection_state(server_id),
                'has_ssh_fallback': self.get_ssh_fallback_data(server_id) is not None
            }
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
