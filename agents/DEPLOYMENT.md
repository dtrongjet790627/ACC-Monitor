# ACC Monitor Agent Deployment Guide

## Overview

The ACC Monitor Agent runs on each Windows server to collect and report:
- Process status (running/stopped)
- Resource usage (CPU, Memory, Disk)
- Log errors and alerts

## Requirements

- Python 3.7+
- psutil
- requests

## Quick Start

### 1. Copy Files to Server

Copy the following files to the target server (e.g., `C:\ACC-Monitor\`):

```
windows/
  acc_agent.py
  config.example.json
```

### 2. Install Dependencies

```cmd
pip install psutil requests
```

Optional (for Oracle service detection via WMI):
```cmd
pip install wmi
```

### 3. Configure Agent

Create `config.json` based on `config.example.json`:

```json
{
  "server_url": "http://MONITOR_SERVER_IP:5000",
  "server_id": "164",
  "report_interval": 10,
  "processes": [
    "Pack.Server",
    "ACC.Server",
    "ACC.MQ",
    "ACC.LogReader",
    "ACC.Packing"
  ],
  "log_path": "E:\\ACC\\ACC\\Log",
  "auto_restart": false
}
```

**Configuration Options:**

| Option | Description | Default |
|--------|-------------|---------|
| server_url | Monitoring center URL | http://localhost:5000 |
| server_id | Unique identifier for this server | local |
| report_interval | Seconds between reports | 10 |
| processes | List of process names to monitor | [] |
| oracle_service | Windows service name for Oracle | OracleServiceXE |
| log_path | Path to scan for error logs | - |
| auto_restart | Auto-restart stopped processes | false |
| restart_cooldown | Seconds between restart attempts | 300 |
| log_level | Logging level (DEBUG/INFO/WARNING/ERROR) | INFO |

### 4. Test Run

```cmd
cd C:\ACC-Monitor
python acc_agent.py
```

You should see output like:
```
ACC Monitor Agent - Windows Edition
========================================
Loaded configuration from C:\ACC-Monitor\config.json
2026-01-29 16:00:00 - INFO - ACC Agent starting...
2026-01-29 16:00:00 - INFO - Server ID: 164
2026-01-29 16:00:01 - INFO - [✓] CPU: 25.5% | Memory: 45.2% | Disk: 60.1% | Processes: 5 up, 0 down
```

### 5. Install as Windows Service

For production, install as a Windows service using NSSM:

1. Download NSSM from https://nssm.cc/download
2. Install service:

```cmd
nssm install ACC-Monitor-Agent "C:\Python39\python.exe" "C:\ACC-Monitor\acc_agent.py"
nssm set ACC-Monitor-Agent AppDirectory "C:\ACC-Monitor"
nssm set ACC-Monitor-Agent DisplayName "ACC Monitor Agent"
nssm set ACC-Monitor-Agent Description "Reports server status to ACC monitoring center"
nssm set ACC-Monitor-Agent Start SERVICE_AUTO_START
nssm start ACC-Monitor-Agent
```

## Server Configuration Reference

| Server ID | Server Name | IP | Processes |
|-----------|-------------|-----|-----------|
| 164 | DKYX | 172.17.10.164 | Pack.Server, ACC.Server, ACC.MQ, ACC.Packing, Oracle |
| 168 | DKEX | 172.17.10.168 | Pack.Server, ACC.Server, ACC.MQ, ACC.LogReader, Oracle |
| 153 | DP_EPS | 172.17.10.153 | Pack.Server, ACC.Server, ACC.MQ, ACC.LogReader, Oracle |
| 193 | C_EPS | 172.17.10.193 | ACC.Server, ACC.MQ, ACC.LogReader, Oracle |
| 194 | L_EPP | 172.17.10.194 | ACC.Server, ACC.MQ, ACC.LogReader, Oracle |
| 165 | SHARED | 172.17.10.165 | Oracle |

## Troubleshooting

### Cannot connect to monitoring center

1. Check if monitoring center is running: `curl http://MONITOR_IP:5000/api/health`
2. Check firewall rules allow port 5000
3. Verify server_url in config.json

### Process not detected

1. Process name must match exactly (case-insensitive)
2. Check if process is running: `tasklist | findstr ProcessName`
3. Try adding .exe suffix to process name

### High CPU usage

Increase report_interval to reduce frequency:
```json
{
  "report_interval": 30
}
```

### Agent logs

Check `acc_agent.log` in the same directory as the script.

## Local Testing

For testing without real servers, use the test agent:

```cmd
cd D:\TechTeam\Projects\ACC-Monitor\agents
python test_agent.py --server-id=164 --scenario=normal
```

Scenarios:
- `normal` - All processes running
- `warning` - High resource usage
- `error` - Some processes stopped
- `mixed` - Random states
