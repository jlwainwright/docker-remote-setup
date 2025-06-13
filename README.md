# Docker Remote Access Setup

Enable Docker daemon TCP access across multiple hosts with a single command.

## ? Quick Start

### One-liner (from GitHub):
```bash
curl -sSL https://raw.githubusercontent.com/yourusername/docker-remote-setup/main/enable-docker-remote.sh | bash
```

### One-liner (simple version):
```bash
bash -c "$(curl -sSL https://bit.ly/docker-remote-enable)"
```

### Manual execution:
```bash
wget https://raw.githubusercontent.com/yourusername/docker-remote-setup/main/enable-docker-remote.sh
chmod +x enable-docker-remote.sh
sudo ./enable-docker-remote.sh
```

## ? What it does

1. **Detects your init system** (systemd/OpenRC/SysVinit)
2. **Backs up existing Docker configuration**
3. **Configures Docker daemon** to listen on TCP port 2375
4. **Handles systemd overrides** for proper configuration
5. **Restarts Docker daemon** with new settings
6. **Verifies the setup** is working correctly

## ? Supported Systems

- ? **Ubuntu/Debian** (systemd)
- ? **CentOS/RHEL/Fedora** (systemd)  
- ? **Alpine Linux** (OpenRC)
- ? **Amazon Linux** (systemd)
- ? **Raspberry Pi OS** (systemd)

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
  ssh $host "curl -sSL https://raw.githubusercontent.com/yourusername/docker-remote-setup/main/enable-docker-remote.sh | bash"
done

# Using Ansible
ansible all -m shell -a "curl -sSL https://raw.githubusercontent.com/yourusername/docker-remote-setup/main/enable-docker-remote.sh | bash"

# Using parallel SSH
parallel-ssh -h hosts.txt "curl -sSL https://raw.githubusercontent.com/yourusername/docker-remote-setup/main/enable-docker-remote.sh | bash"
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

## ?? Troubleshooting

### Check if Docker is listening on TCP:
```bash
netstat -tlnp | grep :2375
```

### View Docker logs:
```bash
# systemd
sudo journalctl -u docker -f

# OpenRC
sudo tail -f /var/log/docker.log
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
