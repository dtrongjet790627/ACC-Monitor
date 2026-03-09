# -*- coding: utf-8 -*-
"""
ACC Monitor - Lightweight Windows Agent
Collects server metrics and pushes to monitoring center every 30 seconds.

Features:
  - CPU / Memory / Disk collection (psutil preferred, wmic fallback)
  - Process detection via tasklist
  - Windows Service detection via sc query
  - Configurable via agent_config.json
  - Optional: can run as a Windows Service (pywin32)
  - Robust: network failures do not crash the agent

Dependencies (minimal):
  Required: Python 3.6+
  Optional: psutil (for higher accuracy), pywin32 (for Windows Service mode)

Usage:
  1. Edit agent_config.json with correct server_id and monitor_url
  2. Run:  python acc_monitor_agent_windows.py
  3. Or install as Windows Service: install_windows_service.bat
"""

import os
import sys
import time
import json
import socket
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from logging.handlers import RotatingFileHandler

# ---------------------------------------------------------------------------
# Try optional imports
# ---------------------------------------------------------------------------
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import requests as _requests_lib
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# stdlib fallback for HTTP POST
if not HAS_REQUESTS:
    import urllib.request
    import urllib.error

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = SCRIPT_DIR / "agent_config.json"
LOG_FILE = SCRIPT_DIR / "acc_monitor_agent.log"
VERSION = "2.0.0"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging(level_name: str = "INFO") -> logging.Logger:
    """Configure rotating file + console logging."""
    logger = logging.getLogger("acc_agent")
    logger.setLevel(getattr(logging, level_name.upper(), logging.INFO))

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")

    # Rotating file handler: 5 MB per file, keep 3 backups
    fh = RotatingFileHandler(str(LOG_FILE), maxBytes=5*1024*1024,
                             backupCount=3, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
    "monitor_url": "http://172.17.10.165:5004",
    "server_id": "CHANGE_ME",
    "report_interval": 30,
    "log_level": "INFO",
    "processes": [],
    "services": [],
    "acc_drive": "C"
}


def load_config() -> dict:
    """Load config from agent_config.json, merge with defaults."""
    config = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            config.update(user_cfg)
        except Exception as exc:
            print(f"[WARN] Failed to load {CONFIG_FILE}: {exc}, using defaults")
    else:
        print(f"[WARN] Config file not found: {CONFIG_FILE}")
        print("       Creating default config. Please edit server_id and monitor_url.")
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
    return config


# ---------------------------------------------------------------------------
# Helper: run subprocess safely
# ---------------------------------------------------------------------------

def run_cmd(cmd: str, timeout: int = 15) -> str:
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


# ---------------------------------------------------------------------------
# Helper: HTTP POST (with requests or urllib fallback)
# ---------------------------------------------------------------------------

def http_post(url: str, data: dict, timeout: int = 10) -> bool:
    """POST JSON data to url. Returns True on success."""
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")

    if HAS_REQUESTS:
        try:
            resp = _requests_lib.post(
                url, data=payload,
                headers={"Content-Type": "application/json"},
                timeout=timeout
            )
            return 200 <= resp.status_code < 300
        except Exception:
            return False
    else:
        try:
            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return 200 <= resp.status < 300
        except Exception:
            return False


# ===========================================================================
# Collectors
# ===========================================================================

class ResourceCollector:
    """Collect CPU, memory, disk usage. Uses psutil if available, wmic fallback."""

    def __init__(self, acc_drive: str = "C"):
        self.acc_drive = acc_drive

    # ----- CPU -----
    def get_cpu_usage(self) -> float:
        if HAS_PSUTIL:
            try:
                return psutil.cpu_percent(interval=1)
            except Exception:
                pass
        return self._cpu_via_wmic()

    def _cpu_via_wmic(self) -> float:
        """wmic cpu get LoadPercentage"""
        output = run_cmd("wmic cpu get LoadPercentage /value", timeout=10)
        for line in output.splitlines():
            if "LoadPercentage" in line:
                try:
                    return float(line.split("=")[1].strip())
                except (ValueError, IndexError):
                    pass
        return 0.0

    # ----- Memory -----
    def get_memory_usage(self) -> float:
        if HAS_PSUTIL:
            try:
                return round(psutil.virtual_memory().percent, 1)
            except Exception:
                pass
        return self._memory_via_wmic()

    def _memory_via_wmic(self) -> float:
        """Calculate memory usage from wmic OS get TotalVisibleMemorySize,FreePhysicalMemory"""
        output = run_cmd(
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

    # ----- Disk -----
    def get_disk_usage(self) -> float:
        drive = self.acc_drive.rstrip(":") + ":\\"
        if HAS_PSUTIL:
            try:
                return round(psutil.disk_usage(drive).percent, 1)
            except Exception:
                pass
        return self._disk_via_wmic(drive)

    def _disk_via_wmic(self, drive: str) -> float:
        """wmic logicaldisk get Size,FreeSpace where DeviceID='X:'"""
        device_id = drive.rstrip("\\")
        output = run_cmd(
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


class ProcessCollector:
    """Detect running processes. Uses psutil if available, tasklist fallback."""

    def check_process(self, name: str) -> dict:
        """Check if a process is running. Returns dict with status info."""
        if HAS_PSUTIL:
            result = self._check_psutil(name)
            if result:
                return result

        return self._check_tasklist(name)

    def _check_psutil(self, name: str) -> dict | None:
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
                            cpu = proc.cpu_percent(interval=0.1)
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

    def _check_tasklist(self, name: str) -> dict:
        """Fallback: check process via tasklist command."""
        search = name.replace(".exe", "").lower()
        output = run_cmd("tasklist /FO CSV /NH", timeout=10)
        for line in output.splitlines():
            parts = line.replace('"', '').split(',')
            if len(parts) >= 5:
                proc_name = parts[0].replace(".exe", "").lower()
                if search == proc_name or search in proc_name:
                    try:
                        pid = int(parts[1])
                    except (ValueError, IndexError):
                        pid = 0
                    # tasklist gives memory in K format like "12,345 K"
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


class ServiceCollector:
    """Detect Windows Service status via sc query."""

    def check_service(self, service_name: str, display_name: str = "") -> dict:
        """Query a Windows service by its service_name."""
        output = run_cmd(f'sc query "{service_name}"', timeout=10)

        status = "stopped"
        if output:
            for line in output.splitlines():
                line = line.strip()
                if "STATE" in line:
                    if "RUNNING" in line.upper():
                        status = "running"
                    elif "STOPPED" in line.upper():
                        status = "stopped"
                    elif "PAUSED" in line.upper():
                        status = "paused"
                    elif "START_PENDING" in line.upper():
                        status = "starting"
                    elif "STOP_PENDING" in line.upper():
                        status = "stopping"
                    break
        else:
            # sc query returned nothing -- service might not exist
            status = "not_found"

        return {
            "name": display_name or service_name,
            "service_name": service_name,
            "status": status,
            "pid": 0,
            "cpu": 0.0,
            "memory": 0.0
        }


# ===========================================================================
# Main Agent
# ===========================================================================

class AccMonitorAgent:
    """Lightweight Windows monitoring agent."""

    def __init__(self, config: dict):
        self.config = config
        self.server_id = config["server_id"]
        self.monitor_url = config["monitor_url"].rstrip("/")
        self.report_interval = config.get("report_interval", 30)
        self.logger = setup_logging(config.get("log_level", "INFO"))

        acc_drive = config.get("acc_drive", "C")
        self.resource = ResourceCollector(acc_drive=acc_drive)
        self.process = ProcessCollector()
        self.service = ServiceCollector()

        self.logger.info("=" * 60)
        self.logger.info(f"ACC Monitor Agent v{VERSION} (Windows)")
        self.logger.info(f"  Server ID   : {self.server_id}")
        self.logger.info(f"  Hostname    : {socket.gethostname()}")
        self.logger.info(f"  Monitor URL : {self.monitor_url}")
        self.logger.info(f"  Interval    : {self.report_interval}s")
        self.logger.info(f"  psutil      : {'YES' if HAS_PSUTIL else 'NO (wmic fallback)'}")
        self.logger.info(f"  requests    : {'YES' if HAS_REQUESTS else 'NO (urllib fallback)'}")
        self.logger.info(f"  Processes   : {config.get('processes', [])}")
        self.logger.info(f"  Services    : {[s.get('service_name','') for s in config.get('services', [])]}")
        self.logger.info("=" * 60)

    def collect(self) -> dict:
        """Collect all metrics and build the report payload."""
        hostname = socket.gethostname()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

        # Resources
        cpu = self.resource.get_cpu_usage()
        mem = self.resource.get_memory_usage()
        disk = self.resource.get_disk_usage()

        # Processes (from config: ["Oracle", ...])
        processes = []
        for proc_name in self.config.get("processes", []):
            info = self.process.check_process(proc_name)
            processes.append(info)

        # Windows Services (from config: [{"service_name": "...", "display_name": "..."}, ...])
        for svc_cfg in self.config.get("services", []):
            svc_name = svc_cfg.get("service_name", "")
            disp_name = svc_cfg.get("display_name", svc_name)
            if svc_name:
                info = self.service.check_service(svc_name, disp_name)
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

    def report(self, metrics: dict) -> bool:
        """POST metrics to the monitoring center."""
        url = f"{self.monitor_url}/api/agent/report"
        return http_post(url, metrics, timeout=10)

    def run(self):
        """Main loop: collect -> report -> sleep."""
        consecutive_failures = 0

        while True:
            try:
                metrics = self.collect()
                success = self.report(metrics)

                if success:
                    if consecutive_failures > 0:
                        self.logger.info("Reconnected to monitoring center.")
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1

                # Summary log line
                res = metrics["resources"]
                procs = metrics["processes"]
                running = sum(1 for p in procs if p["status"] == "running")
                stopped = sum(1 for p in procs if p["status"] == "stopped")
                tag = "OK" if stopped == 0 else "ALERT"

                self.logger.info(
                    f"[{tag}] CPU:{res['cpu_usage']}% MEM:{res['memory_usage']}% "
                    f"DISK:{res['disk_usage']}% | "
                    f"Procs: {running} up / {stopped} down"
                    + (f" | report: FAIL ({consecutive_failures})" if not success else "")
                )

                if stopped > 0:
                    for p in procs:
                        if p["status"] == "stopped":
                            self.logger.warning(f"  -> {p['name']} is STOPPED")

                if consecutive_failures >= 10 and consecutive_failures % 10 == 0:
                    self.logger.warning(
                        f"Cannot reach monitoring center after {consecutive_failures} attempts. "
                        "Agent continues collecting locally."
                    )

            except Exception as exc:
                self.logger.error(f"Error in main loop: {exc}")

            time.sleep(self.report_interval)


# ===========================================================================
# Windows Service Support (optional, requires pywin32)
# ===========================================================================

def _try_run_as_service():
    """If pywin32 is available and running as service, use win32serviceutil."""
    try:
        import win32serviceutil
        import win32service
        import win32event
        import servicemanager
    except ImportError:
        return False  # pywin32 not available

    class AccMonitorService(win32serviceutil.ServiceFramework):
        _svc_name_ = "AccMonitorAgent"
        _svc_display_name_ = "ACC Monitor Agent"
        _svc_description_ = "Lightweight monitoring agent for ACC servers"

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.stop_event = win32event.CreateEvent(None, 0, 0, None)
            self.running = True

        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            self.running = False
            win32event.SetEvent(self.stop_event)

        def SvcDoRun(self):
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, "")
            )
            config = load_config()
            agent = AccMonitorAgent(config)

            while self.running:
                try:
                    metrics = agent.collect()
                    agent.report(metrics)
                except Exception:
                    pass
                # Check stop event with timeout = report_interval * 1000 ms
                rc = win32event.WaitForSingleObject(
                    self.stop_event,
                    agent.report_interval * 1000
                )
                if rc == win32event.WAIT_OBJECT_0:
                    break

    # Check if called with service arguments
    if len(sys.argv) > 1 and sys.argv[1] in ("install", "remove", "start", "stop", "restart", "debug"):
        win32serviceutil.HandleCommandLine(AccMonitorService)
        return True

    # If started by SCM (no arguments), run as service
    try:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(AccMonitorService)
        servicemanager.StartServiceCtrlDispatcher()
        return True
    except Exception:
        return False  # Not started by SCM, fall through to console mode


# ===========================================================================
# Entry Point
# ===========================================================================

def main():
    print(f"ACC Monitor Agent v{VERSION} (Windows)")
    print("=" * 50)

    config = load_config()

    if config["server_id"] == "CHANGE_ME":
        print("[ERROR] Please edit agent_config.json and set the correct server_id.")
        print(f"        Config file: {CONFIG_FILE}")
        sys.exit(1)

    agent = AccMonitorAgent(config)

    try:
        agent.run()
    except KeyboardInterrupt:
        agent.logger.info("Agent stopped by user (Ctrl+C).")
    except Exception as exc:
        agent.logger.error(f"Agent fatal error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    # Try running as Windows Service first (if pywin32 available and called by SCM)
    if not _try_run_as_service():
        # Not a service context -- run in console mode
        main()
