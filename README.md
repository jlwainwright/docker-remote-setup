# Docker Remote Access Setup

Enable Docker daemon TCP access across multiple hosts with a single command.

## ? Quick Start

### One-liner (from GitHub):
```bash
curl -sSL https://raw.githubusercontent.com/jlwainwright/docker-remote-setup/main/enable-docker-remote.sh | bash
```

### One-liner (quick version):
```bash
curl -sSL https://raw.githubusercontent.com/jlwainwright/docker-remote-setup/main/quick-enable.sh | bash
```

### Manual execution:
```bash
wget https://raw.githubusercontent.com/jlwainwright/docker-remote-setup/main/enable-docker-remote.sh
chmod +x enable-docker-remote.sh
# Run as root on Alpine, or with sudo on other systems
./enable-docker-remote.sh
```

## ? What it does

1. **Auto-detects OS and init system** (Alpine Linux/OpenRC, systemd, SysVinit)
2. **Handles sudo availability** (works with or without sudo on Alpine)
3. **Backs up existing Docker configuration**
4. **Configures Docker daemon** to listen on TCP port 2375
5. **Creates appropriate service overrides** (systemd) or uses native restart (OpenRC)
6. **Restarts Docker daemon** with new settings
7. **Verifies the setup** is working correctly

## ? Supported Systems

- ? **Ubuntu/Debian** (systemd)
- ? **CentOS/RHEL/Fedora** (systemd)  
- ? **Alpine Linux** (OpenRC) - ? **Fully Tested & Working**
- ? **Amazon Linux** (systemd)
- ? **Raspberry Pi OS** (systemd)
- ? **Any Linux with Docker** (auto-detects init system)

## ?? Security Warning

This script enables **unencrypted, unauthenticated** access to Docker daemon on port 2375.

**Only use on trusted networks!**

For production environments, consider:
- Setting up TLS certificates
- Using SSH tunneling
- Implementing firewall rules
- Using Docker Machine with proper authentication

## ? Usage After Setup

Once enabled, you can manage Docker remotely:

```bash
# Test the connection
curl http://YOUR_HOST_IP:2375/version

# Use docker client remotely
docker -H tcp://YOUR_HOST_IP:2375 ps

# Create docker context for easy switching
docker context create remote --docker host=tcp://YOUR_HOST_IP:2375
docker context use remote
docker ps  # Now uses remote host
```

## ? Advanced Usage

### Bulk deployment across multiple hosts:
```bash
# Using SSH with key authentication
for host in host1 host2 host3; do
  ssh $host "curl -sSL https://raw.githubusercontent.com/jlwainwright/docker-remote-setup/main/enable-docker-remote.sh | bash"
done

# Using Ansible
ansible all -m shell -a "curl -sSL https://raw.githubusercontent.com/jlwainwright/docker-remote-setup/main/enable-docker-remote.sh | bash"

# Using parallel SSH
parallel-ssh -h hosts.txt "curl -sSL https://raw.githubusercontent.com/jlwainwright/docker-remote-setup/main/enable-docker-remote.sh | bash"
```

## ? Rollback

To disable remote access:
```bash
sudo systemctl stop docker
sudo rm -f /etc/docker/daemon.json
sudo rm -rf /etc/systemd/system/docker.service.d/
sudo systemctl daemon-reload
sudo systemctl start docker
```

## ?? Alpine Linux Notes

### Features:
- ? **Auto-detected** by checking `/etc/alpine-release`
- ? **Works without sudo** when running as root
- ? **Uses OpenRC** service management
- ? **Handles permission issues** gracefully

### Alpine-specific commands:
```bash
# Check Docker service status
rc-service docker status

# Restart Docker manually
rc-service docker restart

# View Docker logs
tail -f /var/log/docker.log
```

## ?? Troubleshooting

### Check if Docker is listening on TCP:
```bash
netstat -tlnp | grep :2375
```

### View Docker logs:
```bash
# systemd (Ubuntu/Debian/CentOS)
sudo journalctl -u docker -f

# OpenRC (Alpine Linux)
tail -f /var/log/docker.log
```

### Test API access:
```bash
curl http://localhost:2375/containers/json
```

## ? Files Modified

- `/etc/docker/daemon.json` - Docker daemon configuration
- `/etc/systemd/system/docker.service.d/override.conf` - systemd service override (systemd only)

## ? Contributing

Feel free to submit issues and pull requests to improve this script!

## ? License

MIT License - feel free to use and modify as needed.
