#!/bin/bash
# Docker Remote Access Enabler
# Usage: curl -sSL https://raw.githubusercontent.com/yourusername/docker-remote-setup/main/enable-docker-remote.sh | bash

set -e

echo "? Enabling Docker Remote Access..."

# Detect init system and OS
if [ -f /etc/alpine-release ]; then
    INIT_SYSTEM="openrc"
    OS="alpine"
elif command -v rc-service >/dev/null 2>&1 && [ -d /etc/runlevels ]; then
    INIT_SYSTEM="openrc"
    OS="alpine"
elif command -v systemctl >/dev/null 2>&1 && systemctl --version >/dev/null 2>&1; then
    INIT_SYSTEM="systemd"
    OS="systemd-based"
elif command -v service >/dev/null 2>&1; then
    INIT_SYSTEM="sysvinit"
    OS="sysvinit-based"
else
    echo "? Unsupported init system"
    exit 1
fi

echo "? Detected OS: $OS, Init system: $INIT_SYSTEM"

# Create docker directory if it doesn't exist
# Handle Alpine Linux which may not have sudo
if command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
else
    SUDO=""
    if [ "$(id -u)" != "0" ]; then
        echo "? This script requires root privileges"
        echo "Please run as root or install sudo"
        exit 1
    fi
fi

$SUDO mkdir -p /etc/docker

# Backup existing daemon.json if it exists
if [ -f /etc/docker/daemon.json ]; then
    echo "? Backing up existing daemon.json..."
    $SUDO cp /etc/docker/daemon.json /etc/docker/daemon.json.backup.$(date +%s)
fi

# Create or update daemon.json
echo "??  Configuring Docker daemon..."
if [ -f /etc/docker/daemon.json ] && [ -s /etc/docker/daemon.json ]; then
    # Merge with existing configuration
    $SUDO python3 -c "
import json
import sys

try:
    with open('/etc/docker/daemon.json', 'r') as f:
        config = json.load(f)
except:
    config = {}

# Add TCP host if not present
hosts = config.get('hosts', [])
tcp_host = 'tcp://0.0.0.0:2375'
unix_host = 'unix:///var/run/docker.sock'

if unix_host not in hosts:
    hosts.insert(0, unix_host)
if tcp_host not in hosts:
    hosts.append(tcp_host)

config['hosts'] = hosts

with open('/etc/docker/daemon.json', 'w') as f:
    json.dump(config, f, indent=2)
" 2>/dev/null || {
    # Fallback if python3 not available
    echo '{"hosts": ["unix:///var/run/docker.sock", "tcp://0.0.0.0:2375"]}' | $SUDO tee /etc/docker/daemon.json > /dev/null
}
else
    # Create new configuration
    echo '{"hosts": ["unix:///var/run/docker.sock", "tcp://0.0.0.0:2375"]}' | $SUDO tee /etc/docker/daemon.json > /dev/null
fi

echo "? Docker daemon configuration:"
$SUDO cat /etc/docker/daemon.json

# Handle systemd override for hosts parameter
if [ "$INIT_SYSTEM" = "systemd" ]; then
    echo "? Creating systemd override..."
    $SUDO mkdir -p /etc/systemd/system/docker.service.d
    $SUDO tee /etc/systemd/system/docker.service.d/override.conf > /dev/null << 'EOF'
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd
EOF
    $SUDO systemctl daemon-reload
fi

# Restart Docker daemon
echo "? Restarting Docker daemon..."
case $INIT_SYSTEM in
    systemd)
        $SUDO systemctl restart docker
        $SUDO systemctl enable docker
        ;;
    openrc)
        $SUDO rc-service docker restart 2>/dev/null || rc-service docker restart
        $SUDO rc-update add docker default 2>/dev/null || rc-update add docker default
        ;;
    sysvinit)
        $SUDO service docker restart
        ;;
esac

# Wait a moment for daemon to start
sleep 3

# Verify Docker is running
if docker version >/dev/null 2>&1; then
    echo "? Docker is running locally"
else
    echo "? Docker is not responding locally"
    exit 1
fi

# Check if TCP port is listening
if netstat -tlnp 2>/dev/null | grep -q ":2375"; then
    echo "? Docker TCP port 2375 is listening"
    
    # Get local IP address
    LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || ip route get 1.1.1.1 | awk '{print $7}' 2>/dev/null || echo "localhost")
    
    echo "? Docker API accessible at:"
    echo "   http://$LOCAL_IP:2375"
    echo "   Test with: curl http://$LOCAL_IP:2375/version"
    echo "   Or: docker -H tcp://$LOCAL_IP:2375 version"
else
    echo "? Docker TCP port 2375 is not listening"
    echo "? Checking logs..."
    case $INIT_SYSTEM in
        systemd)
            $SUDO journalctl -u docker --no-pager -n 10
            ;;
        openrc)
            echo "Checking Alpine/OpenRC Docker logs..."
            $SUDO tail -10 /var/log/docker.log 2>/dev/null || echo "No Docker logs found"
            ;;
        *)
            $SUDO tail -10 /var/log/docker.log 2>/dev/null || echo "No Docker logs found"
            ;;
    esac
    exit 1
fi

echo ""
echo "? Docker remote access enabled successfully!"
echo ""
echo "??  SECURITY WARNING:"
echo "   Docker API is now accessible without authentication"
echo "   Only use this on trusted networks"
echo "   Consider using TLS certificates for production"
echo ""
echo "? Usage examples:"
echo "   docker -H tcp://$LOCAL_IP:2375 ps"
echo "   docker context create remote --docker host=tcp://$LOCAL_IP:2375"
echo ""
