# -*- coding: utf-8 -*-
"""
ACC Monitor - Local Collector
Collects server metrics locally (on the same machine as Backend),
replacing the need for a standalone Agent on this server.

Used for servers with "local_collect": true in servers.json.
Generates data in the same format as the remote Agent's HTTP POST payload,
then injects it via agent_data_service.update_agent_data().
"""
import socket
import subprocess
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

logger = logging.getLogger(__name__)


def _run_cmd(cmd: str, timeout: int = 15) -> str:
    """Run a shell command and return stdout. Returns empty string on failure."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, encoding="utf-8", errors="replace"
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return ""
    except Exception:
        return ""


class LocalCollector:
    """
    Collects CPU, memory, disk, process and Windows service metrics locally.
    Output format is identical to the remote Agent's report payload.
    """

    def __init__(self, server_id: str, server_config: dict):
        """
        Args:
            server_id: The server identifier (e.g. "165")
            server_config: The server configuration dict from servers.json
        """
        self.server_id = server_id
        self.server_config = server_config
        self.acc_drive = server_config.get("acc_drive", "C")

        # Lists of processes and services to monitor
        self.process_names: List[str] = server_config.get("processes", [])
        self.service_configs: List[dict] = server_config.get("services", [])

        logger.info(
            f"[LocalCollector] Initialized for server {server_id} "
            f"(drive={self.acc_drive}, processes={self.process_names}, "
            f"services={[s.get('service_name', '') for s in self.service_configs]})"
        )

    # ------------------------------------------------------------------
    # Resource collection
    # ------------------------------------------------------------------

    def _get_cpu_usage(self) -> float:
        """Get CPU usage percentage (non-blocking)."""
        if HAS_PSUTIL:
            try:
                return psutil.cpu_percent(interval=0)
            except Exception:
                pass
        return self._cpu_via_wmic()

    def _cpu_via_wmic(self) -> float:
        output = _run_cmd("wmic cpu get LoadPercentage /value", timeout=10)
        for line in output.splitlines():
            if "LoadPercentage" in line:
                try:
                    return float(line.split("=")[1].strip())
                except (ValueError, IndexError):
                    pass
        return 0.0

    def _get_memory_usage(self) -> float:
        """Get memory usage percentage."""
        if HAS_PSUTIL:
            try:
                return round(psutil.virtual_memory().percent, 1)
            except Exception:
                pass
        return self._memory_via_wmic()

    def _memory_via_wmic(self) -> float:
        output = _run_cmd(
            "wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value",
            timeout=10
        )
        total = free = 0
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("TotalVisibleMemorySize"):
                try:
                    total = int(line.split("=")[1])
                except (ValueError, IndexError):
                    pass
            elif line.startswith("FreePhysicalMemory"):
                try:
                    free = int(line.split("=")[1])
                except (ValueError, IndexError):
                    pass
        if total > 0:
            return round((total - free) / total * 100, 1)
        return 0.0

    def _get_disk_usage(self) -> float:
        """Get disk usage percentage for the configured drive."""
        drive = self.acc_drive.rstrip(":") + ":\\"
        if HAS_PSUTIL:
            try:
                return round(psutil.disk_usage(drive).percent, 1)
            except Exception:
                pass
        return self._disk_via_wmic(drive)

    def _disk_via_wmic(self, drive: str) -> float:
        device_id = drive.rstrip("\\")
        output = _run_cmd(
            f'wmic logicaldisk where "DeviceID=\'{device_id}\'" get Size,FreeSpace /value',
            timeout=10
        )
        size = free_space = 0
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("Size"):
                try:
                    size = int(line.split("=")[1])
                except (ValueError, IndexError):
                    pass
            elif line.startswith("FreeSpace"):
                try:
                    free_space = int(line.split("=")[1])
                except (ValueError, IndexError):
                    pass
        if size > 0:
            return round((size - free_space) / size * 100, 1)
        return 0.0

    # ------------------------------------------------------------------
    # Process detection
    # ------------------------------------------------------------------

    def _check_process(self, name: str) -> dict:
        """Check if a process is running. Returns dict with status info."""
        if HAS_PSUTIL:
            result = self._check_process_psutil(name)
            if result:
                return result
        return self._check_process_tasklist(name)

    def _check_process_psutil(self, name: str) -> Optional[dict]:
        """Check process via psutil."""
        search = name.replace(".exe", "").lower()
        try:
            for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
                try:
                    pname = (proc.info["name"] or "").replace(".exe", "").lower()
                    if search == pname or search in pname:
                        mem_mb = 0.0
                        if proc.info["memory_info"]:
                            mem_mb = round(proc.info["memory_info"].rss / 1024 / 1024, 1)
                        try:
                            cpu = proc.cpu_percent(interval=0)
                        except Exception:
                            cpu = 0.0
                        return {
                            "name": name,
                            "status": "running",
                            "pid": proc.info["pid"],
                            "cpu": round(cpu, 1),
                            "memory": mem_mb
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception:
            pass
        return None

    def _check_process_tasklist(self, name: str) -> dict:
        """Fallback: check process via tasklist command."""
        search = name.replace(".exe", "").lower()
        output = _run_cmd("tasklist /FO CSV /NH", timeout=10)
        for line in output.splitlines():
            parts = line.replace('"', '').split(',')
            if len(parts) >= 5:
                proc_name = parts[0].replace(".exe", "").lower()
                if search == proc_name or search in proc_name:
                    try:
                        pid = int(parts[1])
                    except (ValueError, IndexError):
                        pid = 0
                    mem_mb = 0.0
                    try:
                        mem_str = parts[4].replace(" K", "").replace(",", "").strip()
                        mem_mb = round(int(mem_str) / 1024, 1)
                    except (ValueError, IndexError):
                        pass
                    return {
                        "name": name,
                        "status": "running",
                        "pid": pid,
                        "cpu": 0.0,
                        "memory": mem_mb
                    }
        return {
            "name": name,
            "status": "stopped",
            "pid": 0,
            "cpu": 0.0,
            "memory": 0.0
        }

    # ------------------------------------------------------------------
    # Windows service detection
    # ------------------------------------------------------------------

    def _check_service(self, service_name: str, display_name: str = "") -> dict:
        """Query a Windows service by its service_name via sc query."""
        output = _run_cmd(f'sc query "{service_name}"', timeout=10)

        status = "stopped"
        if output:
            for line in output.splitlines():
                line = line.strip()
                if "STATE" in line:
                    upper = line.upper()
                    if "RUNNING" in upper:
                        status = "running"
                    elif "STOPPED" in upper:
                        status = "stopped"
                    elif "PAUSED" in upper:
                        status = "paused"
                    elif "START_PENDING" in upper:
                        status = "starting"
                    elif "STOP_PENDING" in upper:
                        status = "stopping"
                    break
        else:
            status = "not_found"

        return {
            "name": display_name or service_name,
            "service_name": service_name,
            "status": status,
            "pid": 0,
            "cpu": 0.0,
            "memory": 0.0
        }

    # ------------------------------------------------------------------
    # Main collection entry point
    # ------------------------------------------------------------------

    def collect(self) -> dict:
        """
        Collect all metrics and return a dict in the same format
        as the remote Agent's HTTP POST payload.

        Returns dict with keys:
            server_id, hostname, timestamp, resources, processes, containers, alerts
        """
        hostname = socket.gethostname()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

        # Resources
        cpu = self._get_cpu_usage()
        mem = self._get_memory_usage()
        disk = self._get_disk_usage()

        # Processes
        processes = []
        for proc_name in self.process_names:
            info = self._check_process(proc_name)
            processes.append(info)

        # Windows Services
        for svc_cfg in self.service_configs:
            svc_name = svc_cfg.get("service_name", "")
            disp_name = svc_cfg.get("display_name", svc_name)
            if svc_name:
                info = self._check_service(svc_name, disp_name)
                processes.append(info)

        # Build alerts for stopped items
        alerts = []
        for p in processes:
            if p["status"] == "stopped":
                alerts.append({
                    "message": f"{p['name']} is STOPPED on {hostname}",
                    "level": "error",
                    "timestamp": now
                })

        return {
            "server_id": self.server_id,
            "hostname": hostname,
            "timestamp": now,
            "resources": {
                "cpu_usage": cpu,
                "memory_usage": mem,
                "disk_usage": disk
            },
            "processes": processes,
            "containers": [],
            "alerts": alerts
        }
