# Indexa Production Deployment Guide

This guide covers deploying Indexa to a Proxmox LXC container with Docker.

## Prerequisites

- Proxmox LXC container with Docker installed
- NAS mount point configured on the LXC container
- Network access to Docker Hub
- SSH access to the LXC container

## Deployment Steps

### 1. Build and Push Docker Image

On your development machine (where Docker is available):

```bash
# Run the deployment script
./deploy.sh
```

Or manually:

```bash
# Build the image
docker build -t bpt1901/indexa:latest .

# Login to Docker Hub
docker login

# Push to Docker Hub
docker push bpt1901/indexa:latest
```

### 2. Prepare Your LXC Container

SSH into your LXC container and create the deployment directory:

```bash
# Create deployment directory
mkdir -p /opt/indexa
cd /opt/indexa

# Verify your NAS mount is working
ls -la /mnt/nas/indexa  # Adjust path as needed
```

### 3. Transfer Configuration Files

Copy these files to your LXC container `/opt/indexa/` directory:

- `docker-compose.prod.yml`
- `.env.production` (rename to `.env`)

```bash
# On your LXC container
cd /opt/indexa

# Create .env file from template
cp .env.production .env

# Edit the .env file if needed
nano .env
```

### 4. Update Docker Compose Configuration

Edit `docker-compose.prod.yml` to match your LXC setup:

```yaml
volumes:
  # Update this path to match your NAS mount point
  - /mnt/nas/indexa:/data  # Adjust as needed
```

### 5. Deploy the Application

```bash
# Pull the latest image and start the container
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# Check the logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 6. Verify Deployment

```bash
# Check container status
docker ps

# Test the application
curl http://localhost:8000

# Check health
docker-compose -f docker-compose.prod.yml ps
```

## Configuration Options

### Environment Variables

Edit `/opt/indexa/.env` to customize:

```bash
# Database path (should match your NAS mount)
DATABASE_PATH=/data/indexa.db

# Application settings
APP_NAME=Indexa - Personal IT Knowledge Base
DEBUG=false

# Docker image version
DOCKER_IMAGE=bpt1901/indexa:latest
```

### NAS Mount Points

Common mount point configurations:

```bash
# If your NAS is mounted at /mnt/nas
volumes:
  - /mnt/nas/indexa:/data

# If using a different mount point
volumes:
  - /your/mount/path/indexa:/data
```

### Port Configuration

To change the port, edit `docker-compose.prod.yml`:

```yaml
ports:
  - "8080:8000"  # External port 8080, internal port 8000
```

## Management Commands

### View Logs
```bash
cd /opt/indexa
docker-compose -f docker-compose.prod.yml logs -f
```

### Restart Application
```bash
cd /opt/indexa
docker-compose -f docker-compose.prod.yml restart
```

### Update Application
```bash
cd /opt/indexa
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Stop Application
```bash
cd /opt/indexa
docker-compose -f docker-compose.prod.yml down
```

### Database Backup
```bash
# Backup the database
cp /mnt/nas/indexa/indexa.db /mnt/nas/indexa/backups/indexa_$(date +%Y%m%d_%H%M%S).db
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Check if port is in use
netstat -tulpn | grep 8000

# Check mount points
df -h
```

### Database Issues
```bash
# Check database file permissions
ls -la /mnt/nas/indexa/

# Ensure the directory is writable
touch /mnt/nas/indexa/test.txt && rm /mnt/nas/indexa/test.txt
```

### Network Issues
```bash
# Test container networking
docker exec indexa-prod curl http://localhost:8000

# Check if service is listening
docker exec indexa-prod netstat -tulpn
```

## Security Considerations

1. **Firewall**: Configure firewall rules to restrict access to port 8000
2. **Reverse Proxy**: Consider using nginx or traefik for SSL termination
3. **Backups**: Set up automated database backups
4. **Updates**: Regularly update the Docker image

## Performance Optimization

1. **Resource Limits**: Add resource limits to docker-compose.prod.yml
2. **Log Rotation**: Configure log rotation for Docker containers
3. **Monitoring**: Set up monitoring for the container and database

## Example Complete Setup

```bash
# On your LXC container
mkdir -p /opt/indexa
cd /opt/indexa

# Create docker-compose.prod.yml with your settings
# Create .env with your configuration

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Verify
curl http://localhost:8000
```

Your Indexa application should now be running at `http://your-lxc-ip:8000`!