#!/bin/bash
# ACC Monitor Linux Agent Installation Script

set -e

INSTALL_DIR="/opt/acc-agent"
CONFIG_DIR="/etc/acc-agent"
LOG_DIR="/var/log"

echo "=================================="
echo "ACC Monitor Agent Installation"
echo "=================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install requests

# Create directories
echo "Creating directories..."
mkdir -p $INSTALL_DIR
mkdir -p $CONFIG_DIR

# Copy files
echo "Copying files..."
cp acc_agent.py $INSTALL_DIR/
cp config.json $CONFIG_DIR/
chmod +x $INSTALL_DIR/acc_agent.py

# Install systemd service
echo "Installing systemd service..."
cp acc-agent.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable and start service
echo "Starting service..."
systemctl enable acc-agent
systemctl start acc-agent

# Check status
sleep 2
if systemctl is-active --quiet acc-agent; then
    echo ""
    echo "=================================="
    echo "Installation Complete!"
    echo "=================================="
    echo ""
    echo "Service Status: Running"
    echo "Config File: $CONFIG_DIR/config.json"
    echo "Log File: /var/log/acc_agent.log"
    echo ""
    echo "Commands:"
    echo "  Status:  systemctl status acc-agent"
    echo "  Stop:    systemctl stop acc-agent"
    echo "  Start:   systemctl start acc-agent"
    echo "  Logs:    journalctl -u acc-agent -f"
else
    echo "Warning: Service installed but not running. Check logs."
    journalctl -u acc-agent --no-pager -n 20
fi
