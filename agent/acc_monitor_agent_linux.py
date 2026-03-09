#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ACC Monitor - Lightweight Linux Agent
Collects server metrics and Docker container status, pushes to monitoring center.

Features:
  - CPU from /proc/stat (no external tools)
  - Memory from /proc/meminfo (no external tools)
  - Disk via df command
  - Docker container status and metrics via docker CLI
  - Zero external dependencies (stdlib only)
  - Robust: network failures do not crash the agent

Dependencies: Python 3.6+ (standard library only)

Usage:
  1. Edit agent_config.json with correct server_id and monitor_url
  2. Run:  python3 acc_monitor_agent_linux.py
  3. Or install as systemd service: sudo bash install_linux_service.sh
"""

import os
import sys
import time
import json
import socket
import logging
import subprocess
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from logging.handlers import RotatingFileHandler

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
    "containers": []
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

def run_cmd(cmd, timeout=15):
    """Run a shell command and return stdout. Returns empty string on failure.
    Uses Popen for reliable timeout handling on Python 3.6+."""
    try:
        proc = subprocess.Popen(
            cmd, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        try:
            stdout, _ = proc.communicate(timeout=timeout)
            return stdout.decode("utf-8", errors="replace").strip()
        except subprocess.TimeoutExpired:
            # Kill the entire process group to avoid zombie processes
            import signal
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:
                proc.kill()
            proc.wait()
            return ""
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Helper: HTTP POST (stdlib only)
# ---------------------------------------------------------------------------

def http_post(url: str, data: dict, timeout: int = 10) -> bool:
    """POST JSON data to url using urllib. Returns True on success."""
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
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

class CpuCollector:
    """Read CPU usage from /proc/stat (measures between two snapshots)."""

    def __init__(self):
        self._prev = None

    def _read_stat(self) -> tuple:
        """Read aggregate CPU line from /proc/stat. Returns (idle, total)."""
        try:
            with open("/proc/stat", "r") as f:
                line = f.readline()  # first line: cpu  user nice system idle iowait irq softirq ...
            parts = line.split()
            # parts[0] == 'cpu', parts[1..] are user nice system idle iowait irq softirq steal guest guest_nice
            values = [int(v) for v in parts[1:]]
            idle = values[3] + values[4]  # idle + iowait
            total = sum(values)
            return idle, total
        except Exception:
            return 0, 0

    def get_usage(self) -> float:
        """Get CPU usage percentage between two reads (0.5s apart)."""
        idle1, total1 = self._read_stat()
        time.sleep(0.5)
        idle2, total2 = self._read_stat()

        total_diff = total2 - total1
        idle_diff = idle2 - idle1

        if total_diff == 0:
            return 0.0
        return round((1.0 - idle_diff / total_diff) * 100, 1)


class MemoryCollector:
    """Read memory usage from /proc/meminfo."""

    def get_usage(self) -> float:
        """Return memory usage percentage."""
        try:
            info = {}
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        key = parts[0].rstrip(":")
                        info[key] = int(parts[1])  # value in kB

            total = info.get("MemTotal", 0)
            available = info.get("MemAvailable", 0)
            if total == 0:
                return 0.0
            used = total - available
            return round(used / total * 100, 1)
        except Exception:
            return 0.0


class DiskCollector:
    """Read disk usage via df command."""

    def get_usage(self, path: str = "/") -> float:
        """Return disk usage percentage for given mount point."""
        output = run_cmd(f"df {path} 2>/dev/null | tail -1")
        if not output:
            return 0.0
        parts = output.split()
        # df output: Filesystem 1K-blocks Used Available Use% Mounted
        for part in parts:
            if part.endswith("%"):
                try:
                    return float(part.rstrip("%"))
                except ValueError:
                    pass
        return 0.0


class DockerCollector:
    """Collect Docker container status and metrics."""

    def check_container(self, container_name: str) -> dict:
        """Get status and metrics for a single container."""
        result = {
            "name": container_name,
            "status": "unknown",
            "container_id": "",
            "metrics": {
                "cpu": "0%",
                "memory": "0MB/0MB",
                "network": "0B/0B"
            }
        }

        # Check container state via docker inspect
        inspect_out = run_cmd(
            f"docker inspect --format '{{{{.Id}}}}|{{{{.State.Running}}}}|{{{{.State.Status}}}}' "
            f"{container_name} 2>/dev/null",
            timeout=20
        )

        if not inspect_out:
            result["status"] = "not_found"
            return result

        parts = inspect_out.split("|")
        if len(parts) >= 3:
            result["container_id"] = parts[0][:12]
            is_running = parts[1].strip().lower() == "true"
            result["status"] = "running" if is_running else "stopped"

        # If running, get resource metrics
        if result["status"] == "running":
            stats_out = run_cmd(
                f"docker stats {container_name} --no-stream "
                f"--format '{{{{.CPUPerc}}}}|{{{{.MemUsage}}}}|{{{{.NetIO}}}}' 2>/dev/null",
                timeout=30
            )
            if stats_out:
                stat_parts = stats_out.split("|")
                if len(stat_parts) >= 3:
                    result["metrics"]["cpu"] = stat_parts[0].strip()
                    result["metrics"]["memory"] = stat_parts[1].strip()
                    result["metrics"]["network"] = stat_parts[2].strip()

        return result


# ===========================================================================
# Main Agent
# ===========================================================================

class AccMonitorAgent:
    """Lightweight Linux monitoring agent."""

    def __init__(self, config: dict):
        self.config = config
        self.server_id = config["server_id"]
        self.monitor_url = config["monitor_url"].rstrip("/")
        self.report_interval = config.get("report_interval", 30)
        self.logger = setup_logging(config.get("log_level", "INFO"))

        self.cpu = CpuCollector()
        self.memory = MemoryCollector()
        self.disk = DiskCollector()
        self.docker = DockerCollector()

        self.logger.info("=" * 60)
        self.logger.info(f"ACC Monitor Agent v{VERSION} (Linux)")
        self.logger.info(f"  Server ID   : {self.server_id}")
        self.logger.info(f"  Hostname    : {socket.gethostname()}")
        self.logger.info(f"  Monitor URL : {self.monitor_url}")
        self.logger.info(f"  Interval    : {self.report_interval}s")
        self.logger.info(f"  Containers  : {config.get('containers', [])}")
        self.logger.info("=" * 60)

    def collect(self) -> dict:
        """Collect all metrics and build the report payload."""
        hostname = socket.gethostname()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

        # Resources
        cpu_usage = self.cpu.get_usage()
        mem_usage = self.memory.get_usage()
        disk_usage = self.disk.get_usage("/")

        # Docker containers
        containers = []
        for cname in self.config.get("containers", []):
            info = self.docker.check_container(cname)
            containers.append(info)

        # Build alerts for stopped containers
        alerts = []
        for c in containers:
            if c["status"] == "stopped":
                alerts.append({
                    "message": f"Container {c['name']} is STOPPED on {hostname}",
                    "level": "error",
                    "timestamp": now
                })

        return {
            "server_id": self.server_id,
            "hostname": hostname,
            "timestamp": now,
            "resources": {
                "cpu_usage": cpu_usage,
                "memory_usage": mem_usage,
                "disk_usage": disk_usage
            },
            "processes": [],
            "containers": containers,
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
                conts = metrics["containers"]
                running = sum(1 for c in conts if c["status"] == "running")
                stopped = sum(1 for c in conts if c["status"] == "stopped")
                tag = "OK" if stopped == 0 else "ALERT"

                self.logger.info(
                    f"[{tag}] CPU:{res['cpu_usage']}% MEM:{res['memory_usage']}% "
                    f"DISK:{res['disk_usage']}% | "
                    f"Containers: {running} up / {stopped} down"
                    + (f" | report: FAIL ({consecutive_failures})" if not success else "")
                )

                if stopped > 0:
                    for c in conts:
                        if c["status"] == "stopped":
                            self.logger.warning(f"  -> Container {c['name']} is STOPPED")

                if consecutive_failures >= 10 and consecutive_failures % 10 == 0:
                    self.logger.warning(
                        f"Cannot reach monitoring center after {consecutive_failures} attempts. "
                        "Agent continues collecting locally."
                    )

            except Exception as exc:
                self.logger.error(f"Error in main loop: {exc}")

            time.sleep(self.report_interval)


# ===========================================================================
# Entry Point
# ===========================================================================

def main():
    print(f"ACC Monitor Agent v{VERSION} (Linux)")
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
    main()
