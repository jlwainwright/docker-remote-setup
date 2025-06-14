# Docker Remote Setup Script

? **Automatically enable Docker remote access via TCP on Linux systems**

This script configures Docker to accept remote connections on port 2375, enabling remote Docker management across your infrastructure.

## ? Quick Start

```bash
curl -sSL https://raw.githubusercontent.com/jlwainwright/docker-remote-setup/main/enable-docker-remote.sh | bash
```

## ? Supported Systems

- **Alpine Linux** (OpenRC)
- **Ubuntu/Debian** (systemd)
- **CentOS/RHEL** (systemd)
- **Other systemd-based distributions**

## ? Testing Results

The script has been successfully tested on:

| System | OS | Docker Version | Status | Notes |
|--------|----|--------------|---------|---------| 
| alpine-docker | Alpine Linux | 28.2.1 | ? Working | OpenRC init system |
| ubuntu-server | Ubuntu | 28.2.2 | ? Working | Modern systemd |
| debian-server | Debian | 20.10.24 | ? Working | With manual fix |
| homelab | Ubuntu | 28.2.1 | ? Working | 8+ containers |
| media-server | Ubuntu | 28.2.1 | ? Working | Gitea, Deluge, qBittorrent |
| automation | Debian | 20.10.24 | ? Working | n8n, WhatsApp APIs |

## ? What the Script Does

1. **Detects your init system** (OpenRC vs systemd)
2. **Backs up existing configuration**
3. **Configures Docker daemon** to listen on TCP port 2375
4. **Handles systemd overrides** when needed
5. **Restarts Docker service**
6. **Verifies remote access** is working

## ? Usage Examples

### Remote Docker Commands
```bash
# Direct remote commands
docker -H tcp://192.168.1.100:2375 ps
docker -H tcp://192.168.1.100:2375 images

# Create and use contexts
docker context create remote --docker host=tcp://192.168.1.100:2375
docker context use remote
docker ps  # Now runs on remote host
```

### Bulk Management
```bash
# Check all hosts
for host in 192.168.1.100 192.168.1.101 192.168.1.102; do
  echo "=== $host ==="
  docker -H tcp://$host:2375 ps --format "table {{.Names}}\t{{.Status}}"
done
```

## ? Troubleshooting

### Common Issue: systemd ExecStart Conflict

**Symptoms:**
- Script runs but Docker fails to start
- Error: `Job for docker.service failed because the control process exited with error code`
- Status shows: `code=exited, status=203/EXEC`

**Cause:**
Some systems have `-H fd://` in their original Docker service configuration, which conflicts with the `hosts` setting in `daemon.json`.

### ?? Universal Fix Command

If the script fails with systemd errors, run this one-liner fix:

```bash
sudo rm -rf /etc/systemd/system/docker.service.d/ && echo '{}' | sudo tee /etc/docker/daemon.json > /dev/null && sudo systemctl daemon-reload && sudo systemctl start docker && sleep 3 && sudo systemctl stop docker && echo '{"hosts": ["unix:///var/run/docker.sock", "tcp://0.0.0.0:2375"]}' | sudo tee /etc/docker/daemon.json > /dev/null && ORIGINAL_EXEC=$(systemctl cat docker.service | grep "ExecStart=" | grep -v "ExecStart=$" | head -1 | sed 's/ExecStart=//') && sudo mkdir -p /etc/systemd/system/docker.service.d && echo -e "[Service]\nExecStart=\nExecStart=$ORIGINAL_EXEC" | sed 's/-H fd:\/\///' | sudo tee /etc/systemd/system/docker.service.d/override.conf > /dev/null && sudo systemctl daemon-reload && sudo systemctl start docker && sleep 3 && echo "Testing..." && netstat -tlnp | grep :2375
```

### Step-by-Step Manual Fix

If you prefer to understand each step:

**1. Check original Docker service:**
```bash
systemctl cat docker.service | grep ExecStart
```

**2. Remove broken override:**
```bash
sudo rm -rf /etc/systemd/system/docker.service.d/
sudo systemctl daemon-reload
```

**3. Start Docker normally:**
```bash
echo '{}' | sudo tee /etc/docker/daemon.json > /dev/null
sudo systemctl start docker
```

**4. Create proper override:**
```bash
sudo systemctl stop docker
echo '{"hosts": ["unix:///var/run/docker.sock", "tcp://0.0.0.0:2375"]}' | sudo tee /etc/docker/daemon.json > /dev/null

# Create correct systemd override
sudo mkdir -p /etc/systemd/system/docker.service.d
sudo tee /etc/systemd/system/docker.service.d/override.conf > /dev/null << 'EOF'
[Service]
ExecStart=
ExecStart=/usr/sbin/dockerd --containerd=/run/containerd/containerd.sock $DOCKER_OPTS
EOF

sudo systemctl daemon-reload
sudo systemctl start docker
```

**5. Verify it's working:**
```bash
# Check status
sudo systemctl status docker

# Check TCP port
netstat -tlnp | grep :2375

# Test API
curl http://localhost:2375/version
```

### Other Common Issues

**Docker not starting after script:**
```bash
# Check logs
sudo journalctl -u docker --no-pager -n 20

# Reset to original state
sudo rm -f /etc/docker/daemon.json.backup
sudo mv /etc/docker/daemon.json.backup /etc/docker/daemon.json
sudo systemctl restart docker
```

**Port 2375 not listening:**
```bash
# Check daemon.json
cat /etc/docker/daemon.json

# Verify Docker is reading the config
docker system info | grep -A 5 "Server"
```

**Permission denied:**
```bash
# Ensure script runs as root
sudo curl -sSL https://raw.githubusercontent.com/jlwainwright/docker-remote-setup/main/enable-docker-remote.sh | sudo bash
```

## ? Verification Commands

After running the script (or fix), verify everything works:

```bash
# Local verification
docker ps
curl http://localhost:2375/version

# Remote verification (from another machine)
docker -H tcp://YOUR_SERVER_IP:2375 version
docker -H tcp://YOUR_SERVER_IP:2375 ps

# Check if port is listening
netstat -tlnp | grep :2375
# Should show: tcp6 0 0 :::2375 :::* LISTEN
```

## ?? Security Warning

**This configuration exposes Docker API without authentication!**

- ? **Safe for**: Home labs, development environments, trusted networks
- ? **NOT safe for**: Production servers, public networks, cloud instances

### Production Security

For production use, consider:
- TLS certificates with client authentication
- VPN or private networks only
- Firewall rules restricting access
- Docker API proxy with authentication

## ?? Multi-Host Management

Once you have multiple Docker hosts configured:

### Create Contexts
```bash
docker context create homelab --docker host=tcp://192.168.1.100:2375
docker context create media --docker host=tcp://192.168.1.101:2375
docker context create automation --docker host=tcp://192.168.1.102:2375
```

### Switch Between Hosts
```bash
docker context use homelab
docker ps  # Shows containers on homelab

docker context use media  
docker ps  # Shows containers on media server
```

### Bulk Operations Script
```bash
#!/bin/bash
HOSTS="192.168.1.100 192.168.1.101 192.168.1.102"

echo "=== Docker Host Status ==="
for host in $HOSTS; do
    echo "--- $host ---"
    docker -H tcp://$host:2375 ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" 2>/dev/null || echo "Failed to connect"
    echo
done
```

## ? Tested Configurations

### Successful Deployments
- **Home automation stack**: 8 containers across multiple hosts
- **Media server**: Deluge, qBittorrent, Gitea
- **Development environment**: OpenHands, Portainer, various tools
- **Automation platform**: n8n, WhatsApp APIs, PostgreSQL
- **Security tools**: CyberZap stack

### Architecture Examples
```
???????????????????    ???????????????????    ???????????????????
?   Homelab       ?    ?   Media Server  ?    ?   Dev Machine   ?
? 192.168.1.100   ?    ? 192.168.1.101   ?    ? 192.168.1.102   ?
?                 ?    ?                 ?    ?                 ?
? ? Home Assistant?    ? ? Deluge        ?    ? ? OpenHands     ?
? ? Node-RED      ?    ? ? qBittorrent   ?    ? ? Portainer     ?
? ? InfluxDB      ?    ? ? Gitea         ?    ? ? Development   ?
? ? Grafana       ?    ? ? Plex          ?    ?   Containers    ?
???????????????????    ???????????????????    ???????????????????
         ?                       ?                       ?
         ?????????????????????????????????????????????????
                                 ?
                    ???????????????????
                    ?   Management    ?
                    ?    Machine      ?
                    ?                 ?
                    ? docker context  ?
                    ?   switching     ?
                    ???????????????????
```

## ? Script Details

### Configuration Files Modified
- `/etc/docker/daemon.json` - Docker daemon configuration
- `/etc/systemd/system/docker.service.d/override.conf` - systemd override (if needed)
- Backup created at `/etc/docker/daemon.json.backup`

### Detection Logic
```bash
# Init system detection
if command -v systemctl >/dev/null 2>&1; then
    INIT_SYSTEM="systemd"
elif command -v rc-service >/dev/null 2>&1; then
    INIT_SYSTEM="openrc"
else
    echo "Unsupported init system"
    exit 1
fi
```

### Network Configuration
The script configures Docker to listen on:
- `unix:///var/run/docker.sock` - Local Unix socket (default)
- `tcp://0.0.0.0:2375` - TCP on all interfaces, port 2375

## ? Contributing

Found an issue or have an improvement? Please:

1. Open an issue describing the problem
2. Include your OS, Docker version, and error logs
3. Test the universal fix command if applicable
4. Submit pull requests with improvements

## ? License

MIT License - feel free to use and modify as needed.

## ? Related Tools

- [Docker Contexts Documentation](https://docs.docker.com/engine/context/working-with-contexts/)
- [Docker API Documentation](https://docs.docker.com/engine/api/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)

---

**Made with ?? for Docker infrastructure management**