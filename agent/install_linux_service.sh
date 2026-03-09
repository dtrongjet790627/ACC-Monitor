#!/bin/bash
# =====================================================================
# ACC Monitor Agent - Linux (systemd) Service Installation
#
# This script:
#   1. Copies agent files to /opt/acc-monitor-agent/
#   2. Creates a systemd service unit
#   3. Enables and starts the service
#
# Run as root:  sudo bash install_linux_service.sh
# =====================================================================

set -e

# --- Configuration ---
INSTALL_DIR="/opt/acc-monitor-agent"
SERVICE_NAME="acc-monitor-agent"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENT_SCRIPT="acc_monitor_agent_linux.py"
CONFIG_FILE="agent_config.json"

echo "======================================================"
echo "  ACC Monitor Agent - Linux Service Installer"
echo "======================================================"
echo ""

# --- Check root ---
if [ "$(id -u)" -ne 0 ]; then
    echo "[ERROR] This script must be run as root."
    echo "        Usage: sudo bash $0"
    exit 1
fi

# --- Check Python 3 ---
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] Python 3 not found. Please install python3."
    exit 1
fi
echo "[INFO] Python3 found: $(python3 --version)"

# --- Check source files ---
if [ ! -f "${SCRIPT_DIR}/${AGENT_SCRIPT}" ]; then
    echo "[ERROR] Agent script not found: ${SCRIPT_DIR}/${AGENT_SCRIPT}"
    exit 1
fi

if [ ! -f "${SCRIPT_DIR}/${CONFIG_FILE}" ]; then
    echo "[WARN] Config file not found: ${SCRIPT_DIR}/${CONFIG_FILE}"
    echo "       A default config will be created. Edit it before starting."
fi

# --- Stop existing service if running ---
if systemctl is-active --quiet "${SERVICE_NAME}" 2>/dev/null; then
    echo "[INFO] Stopping existing ${SERVICE_NAME} service..."
    systemctl stop "${SERVICE_NAME}"
fi

# --- Create install directory ---
echo "[INFO] Creating ${INSTALL_DIR}..."
mkdir -p "${INSTALL_DIR}"

# --- Copy files ---
echo "[INFO] Copying agent files..."
cp "${SCRIPT_DIR}/${AGENT_SCRIPT}" "${INSTALL_DIR}/"
chmod +x "${INSTALL_DIR}/${AGENT_SCRIPT}"

if [ -f "${SCRIPT_DIR}/${CONFIG_FILE}" ]; then
    # Only copy config if it does not already exist at destination (avoid overwrite)
    if [ ! -f "${INSTALL_DIR}/${CONFIG_FILE}" ]; then
        cp "${SCRIPT_DIR}/${CONFIG_FILE}" "${INSTALL_DIR}/"
        echo "[INFO] Config copied. Please edit: ${INSTALL_DIR}/${CONFIG_FILE}"
    else
        echo "[INFO] Config already exists at ${INSTALL_DIR}/${CONFIG_FILE}, not overwriting."
    fi
fi

# --- Create systemd service file ---
echo "[INFO] Creating systemd service: ${SERVICE_FILE}"
cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=ACC Monitor Agent
Documentation=https://github.com/TechTeam/ACC-Monitor
After=network-online.target docker.service
Wants=network-online.target docker.service

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
ExecStart=/usr/bin/python3 ${INSTALL_DIR}/${AGENT_SCRIPT}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}

# Hardening
NoNewPrivileges=false
ProtectSystem=false

[Install]
WantedBy=multi-user.target
EOF

# --- Reload systemd ---
echo "[INFO] Reloading systemd daemon..."
systemctl daemon-reload

# --- Enable service ---
echo "[INFO] Enabling ${SERVICE_NAME} to start on boot..."
systemctl enable "${SERVICE_NAME}"

# --- Start service ---
echo "[INFO] Starting ${SERVICE_NAME}..."
systemctl start "${SERVICE_NAME}"

# --- Verify ---
sleep 2
if systemctl is-active --quiet "${SERVICE_NAME}"; then
    echo ""
    echo "======================================================"
    echo "  Installation Complete - Service is RUNNING"
    echo "======================================================"
    echo ""
    echo "  Install dir : ${INSTALL_DIR}"
    echo "  Config file : ${INSTALL_DIR}/${CONFIG_FILE}"
    echo "  Log file    : ${INSTALL_DIR}/acc_monitor_agent.log"
    echo ""
    echo "  Management commands:"
    echo "    Status  : systemctl status ${SERVICE_NAME}"
    echo "    Logs    : journalctl -u ${SERVICE_NAME} -f"
    echo "    Stop    : systemctl stop ${SERVICE_NAME}"
    echo "    Start   : systemctl start ${SERVICE_NAME}"
    echo "    Restart : systemctl restart ${SERVICE_NAME}"
    echo "    Disable : systemctl disable ${SERVICE_NAME}"
    echo ""
else
    echo ""
    echo "[WARN] Service installed but NOT running."
    echo "       Check logs: journalctl -u ${SERVICE_NAME} --no-pager -n 30"
    echo ""
    echo "       Common issues:"
    echo "       1. agent_config.json has server_id set to CHANGE_ME"
    echo "       2. Python dependencies missing"
    echo ""
fi
