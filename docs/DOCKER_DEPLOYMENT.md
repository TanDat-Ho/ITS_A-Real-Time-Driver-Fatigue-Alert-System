# 🐳 Docker Deployment Guide

This guide explains how to deploy the Driver Fatigue Alert System using Docker.

## 📋 Prerequisites

- **Docker Desktop** (Windows/macOS) or **Docker Engine** (Linux)
- **Docker Compose** v2.0+
- **Camera access** (USB webcam or built-in camera)
- **X11 forwarding** (Linux/macOS for GUI) or **WSL2** (Windows)

## 🚀 Quick Start

### Option 1: Using Deployment Scripts

#### Windows (PowerShell)
```powershell
# Build and run with GUI
.\deploy-docker.ps1 -Action build

# Run in headless mode (no GUI)
.\deploy-docker.ps1 -Action headless

# Stop services
.\deploy-docker.ps1 -Action stop
```

#### Linux/macOS (Bash)
```bash
# Build and run with GUI
./deploy-docker.sh build

# Run in headless mode
./deploy-docker.sh headless

# Stop services
./deploy-docker.sh stop
```

### Option 2: Manual Docker Commands

#### Build the Image
```bash
docker build -t driver-fatigue-alert:latest .
```

#### Run with GUI (Linux/macOS)
```bash
# Allow X11 forwarding
xhost +local:docker

# Run container
docker run -it --rm \
  --name driver-fatigue-alert \
  --device /dev/video0:/dev/video0 \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/log:/app/log \
  -v $(pwd)/output:/app/output \
  driver-fatigue-alert:latest
```

#### Run Headless Mode
```bash
docker run -it --rm \
  --name driver-fatigue-alert-headless \
  --device /dev/video0:/dev/video0 \
  -e HEADLESS_MODE=true \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/log:/app/log \
  -v $(pwd)/output:/app/output \
  driver-fatigue-alert:latest python run.py --headless
```

### Option 3: Docker Compose

#### With GUI
```bash
docker-compose up -d driver-fatigue-alert
```

#### Headless Mode
```bash
docker-compose --profile headless up -d driver-fatigue-alert-headless
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DISPLAY` | X11 display for GUI | `:0` |
| `QT_X11_NO_MITSHM` | Fix Qt GUI issues | `1` |
| `PYTHONPATH` | Python module path | `/app` |
| `HEADLESS_MODE` | Run without GUI | `false` |

### Volume Mounts

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./config` | `/app/config` | Configuration files |
| `./log` | `/app/log` | Application logs |
| `./output` | `/app/output` | Screenshots and output |

### Device Access

- **Camera:** `/dev/video0:/dev/video0` (Linux)
- **Privileged mode** required for camera access

## 🖥️ Platform-Specific Setup

### Windows (WSL2)

1. **Install Docker Desktop** with WSL2 backend
2. **Enable WSL integration** in Docker Desktop settings
3. **Install VcXsrv** or **X410** for GUI support
4. **Set DISPLAY variable:**
   ```powershell
   $env:DISPLAY = "host.docker.internal:0.0"
   ```

### Linux

1. **Install Docker Engine:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   ```

2. **Add user to docker group:**
   ```bash
   sudo usermod -aG docker $USER
   ```

3. **Enable X11 forwarding:**
   ```bash
   xhost +local:docker
   ```

### macOS

1. **Install Docker Desktop**
2. **Install XQuartz** for X11 support:
   ```bash
   brew install --cask xquartz
   ```

3. **Configure XQuartz:**
   - Open XQuartz
   - Go to Preferences > Security
   - Enable "Allow connections from network clients"
   - Restart XQuartz

## 📊 Monitoring & Logs

### View Logs
```bash
# Docker Compose logs
docker-compose logs -f driver-fatigue-alert

# Direct container logs
docker logs -f driver-fatigue-alert
```

### Health Checks
```bash
# Check container health
docker ps

# Manual health check
docker exec driver-fatigue-alert python -c "import cv2, mediapipe; print('OK')"
```

## 🛠️ Troubleshooting

### Common Issues

#### Camera Not Accessible
```bash
# Check camera devices
ls /dev/video*

# Run with all devices (if specific device unknown)
docker run --privileged -v /dev:/dev ...
```

#### GUI Not Displaying (Linux)
```bash
# Check X11 permissions
xhost
xhost +local:docker

# Verify DISPLAY variable
echo $DISPLAY
```

#### Permission Issues
```bash
# Run with current user
docker run --user $(id -u):$(id -g) ...

# Fix file permissions
sudo chown -R $USER:$USER ./config ./log ./output
```

#### Memory/Performance Issues
```bash
# Increase Docker memory limit (Docker Desktop)
# Settings > Resources > Advanced > Memory

# Monitor container resource usage
docker stats driver-fatigue-alert
```

## 🔄 Updates & Maintenance

### Update Image
```bash
# Pull latest changes
git pull origin main

# Rebuild image
docker build -t driver-fatigue-alert:latest .

# Restart services
docker-compose down && docker-compose up -d
```

### Cleanup
```bash
# Remove unused containers and images
docker system prune -f

# Complete cleanup
./deploy-docker.sh cleanup  # or deploy-docker.ps1 -Action cleanup
```

## 🏗️ Building for Production

### Multi-stage Build (Optional)
```dockerfile
# Add to Dockerfile for smaller production image
FROM python:3.11-slim as runtime
COPY --from=builder /app /app
WORKDIR /app
CMD ["python", "run.py"]
```

### Security Hardening
```dockerfile
# Run as non-root user
RUN useradd -m -u 1000 app
USER app
```

## 📈 CI/CD Integration

The repository includes GitHub Actions workflow (`.github/workflows/docker.yml`) that:

- **Builds** Docker images on every push
- **Tests** dependency installation and imports
- **Publishes** to GitHub Container Registry
- **Scans** for security vulnerabilities
- **Supports** multi-architecture builds (AMD64, ARM64)

### Using Published Images

```bash
# Pull from GitHub Container Registry
docker pull ghcr.io/yourusername/driver-fatigue-alert:latest

# Run published image
docker run -it --rm ghcr.io/yourusername/driver-fatigue-alert:latest
```

## 📝 Development

### Development Mode
```bash
# Mount source code for live development
docker run -it --rm \
  -v $(pwd):/app \
  --device /dev/video0 \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  driver-fatigue-alert:latest bash
```

### Testing Changes
```bash
# Quick test build
docker build -t driver-fatigue-alert:dev .

# Test specific components
docker run --rm driver-fatigue-alert:dev python -c "from src.app.config import get_fatigue_config; print('Config OK')"
```
