# Linux Installer Guide

This document provides comprehensive instructions for creating and distributing Linux packages for the Driver Fatigue Detection System.

## Table of Contents

- [Overview](#overview)
- [Package Formats](#package-formats)
- [Building Packages](#building-packages)
- [Installation Methods](#installation-methods)
- [Distribution](#distribution)
- [Desktop Integration](#desktop-integration)
- [Troubleshooting](#troubleshooting)

## Overview

The Linux distribution provides multiple package formats to support different Linux distributions and user preferences:

- **AppImage**: Portable application that runs on most Linux distributions
- **DEB**: Package for Debian-based distributions (Ubuntu, Mint, etc.)
- **RPM**: Package for Red Hat-based distributions (Fedora, CentOS, etc.)
- **Snap**: Universal package for modern Linux distributions
- **Flatpak**: Sandboxed application format
- **Tarball**: Generic archive for manual installation

## Package Formats

### AppImage
- **Portable**: Runs without installation
- **Self-contained**: All dependencies included
- **Distribution-agnostic**: Works on most Linux distributions
- **Size**: ~80-150 MB

### DEB Package
- **Native**: Integrates with APT package manager
- **Dependencies**: Automatic dependency resolution
- **System integration**: Desktop files, menu entries
- **Target**: Debian, Ubuntu, Linux Mint, Elementary OS

### RPM Package
- **Native**: Integrates with YUM/DNF package managers
- **Dependencies**: Automatic dependency resolution
- **System integration**: Desktop files, menu entries
- **Target**: Fedora, CentOS, RHEL, openSUSE

### Snap Package
- **Universal**: Works across different distributions
- **Sandboxed**: Enhanced security isolation
- **Auto-updates**: Built-in update mechanism
- **Store distribution**: Ubuntu Snap Store

### Flatpak
- **Universal**: Works across different distributions
- **Sandboxed**: Runtime isolation
- **Permission-based**: Granular access control
- **Store distribution**: Flathub

## Building Packages

### Prerequisites

#### System Dependencies
```bash
# Debian/Ubuntu
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    pkg-config \
    libgtk-3-dev \
    libwebkit2gtk-4.0-dev \
    libappindicator3-dev \
    librsvg2-dev \
    patchelf \
    desktop-file-utils \
    libgdk-pixbuf2.0-dev \
    fakeroot \
    dpkg-dev \
    rpm \
    alien

# Fedora/CentOS
sudo dnf install -y \
    gcc gcc-c++ \
    pkg-config \
    gtk3-devel \
    webkit2gtk3-devel \
    libappindicator-gtk3-devel \
    librsvg2-devel \
    patchelf \
    desktop-file-utils \
    gdk-pixbuf2-devel \
    rpm-build \
    rpm-devel

# Arch Linux
sudo pacman -S \
    base-devel \
    pkg-config \
    gtk3 \
    webkit2gtk \
    libappindicator-gtk3 \
    librsvg \
    patchelf \
    desktop-file-utils \
    gdk-pixbuf2
```

#### AppImage Tools
```bash
# Download linuxdeploy
wget https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
chmod +x linuxdeploy-x86_64.AppImage
sudo mv linuxdeploy-x86_64.AppImage /usr/local/bin/linuxdeploy

# Download appimagetool (alternative)
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool
```

### Building Process

#### Method 1: Using Build Script (Recommended)
```bash
# Build all packages
chmod +x build-linux.sh
./build-linux.sh --onefile

# Build specific package types
./build-linux.sh --appimage-only
./build-linux.sh --deb-only
./build-linux.sh --rpm-only
```

#### Method 2: Manual Build Process

##### 1. Build Application Executable
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements-build.txt

# Build with PyInstaller
python -m PyInstaller fatigue_app.spec --clean --noconfirm
```

##### 2. Create AppImage
```bash
# Create AppDir structure
mkdir -p FatigueDetectionApp.AppDir/usr/{bin,share/applications,share/icons/hicolor/256x256/apps}

# Copy executable
cp dist/FatigueDetectionApp FatigueDetectionApp.AppDir/usr/bin/

# Create desktop file
cat > FatigueDetectionApp.AppDir/usr/share/applications/fatigue-detection.desktop << EOF
[Desktop Entry]
Type=Application
Name=Driver Fatigue Detection
Comment=Real-time driver fatigue detection system
Exec=FatigueDetectionApp
Icon=fatigue-detection
Categories=Utility;Science;
Terminal=false
StartupNotify=true
EOF

# Copy icon
cp assets/icon/app_icon.png FatigueDetectionApp.AppDir/usr/share/icons/hicolor/256x256/apps/fatigue-detection.png

# Create AppRun script
cat > FatigueDetectionApp.AppDir/AppRun << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
exec ./usr/bin/FatigueDetectionApp "$@"
EOF
chmod +x FatigueDetectionApp.AppDir/AppRun

# Create AppImage
linuxdeploy --appdir FatigueDetectionApp.AppDir --output appimage
```

##### 3. Create DEB Package
```bash
# Create package structure
PACKAGE_NAME="driver-fatigue-detection"
VERSION="1.0.0"
ARCHITECTURE="amd64"
PACKAGE_DIR="${PACKAGE_NAME}_${VERSION}_${ARCHITECTURE}"

mkdir -p $PACKAGE_DIR/{DEBIAN,usr/bin,usr/share/{applications,icons/hicolor/256x256/apps,doc/$PACKAGE_NAME}}

# Create control file
cat > $PACKAGE_DIR/DEBIAN/control << EOF
Package: $PACKAGE_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCHITECTURE
Depends: python3 (>= 3.8), python3-tk, libgtk-3-0, libgstreamer1.0-0
Maintainer: Driver Fatigue Detection Team <team@example.com>
Homepage: https://github.com/yourorg/driver-fatigue-detection
Description: Real-time driver fatigue detection system
 A comprehensive system for detecting driver fatigue using computer vision
 and machine learning techniques. The application monitors eye movements,
 head pose, and other fatigue indicators to alert drivers in real-time.
EOF

# Create postinst script
cat > $PACKAGE_DIR/DEBIAN/postinst << 'EOF'
#!/bin/bash
set -e
# Update desktop database
if command -v update-desktop-database >/dev/null; then
    update-desktop-database /usr/share/applications
fi
# Update icon cache
if command -v gtk-update-icon-cache >/dev/null; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor
fi
EOF
chmod +x $PACKAGE_DIR/DEBIAN/postinst

# Create prerm script
cat > $PACKAGE_DIR/DEBIAN/prerm << 'EOF'
#!/bin/bash
set -e
# Stop any running instances
pkill -f FatigueDetectionApp || true
EOF
chmod +x $PACKAGE_DIR/DEBIAN/prerm

# Copy files
cp dist/FatigueDetectionApp $PACKAGE_DIR/usr/bin/
cp assets/icon/app_icon.png $PACKAGE_DIR/usr/share/icons/hicolor/256x256/apps/fatigue-detection.png
cp README.md $PACKAGE_DIR/usr/share/doc/$PACKAGE_NAME/

# Create desktop file
cat > $PACKAGE_DIR/usr/share/applications/fatigue-detection.desktop << EOF
[Desktop Entry]
Type=Application
Name=Driver Fatigue Detection
GenericName=Fatigue Detection System
Comment=Real-time driver fatigue detection system
Exec=/usr/bin/FatigueDetectionApp
Icon=fatigue-detection
Categories=Utility;Science;AudioVideo;
Keywords=fatigue;driver;detection;safety;monitoring;
Terminal=false
StartupNotify=true
MimeType=application/x-fatigue-data;
EOF

# Build DEB package
dpkg-deb --build $PACKAGE_DIR
```

##### 4. Create RPM Package
```bash
# Create RPM build environment
mkdir -p ~/rpmbuild/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}

# Create spec file
cat > ~/rpmbuild/SPECS/driver-fatigue-detection.spec << 'EOF'
Name:           driver-fatigue-detection
Version:        1.0.0
Release:        1%{?dist}
Summary:        Real-time driver fatigue detection system
License:        MIT
URL:            https://github.com/yourorg/driver-fatigue-detection
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  python3-devel
Requires:       python3 >= 3.8, python3-tkinter, gtk3, gstreamer1

%description
A comprehensive system for detecting driver fatigue using computer vision
and machine learning techniques. The application monitors eye movements,
head pose, and other fatigue indicators to alert drivers in real-time.

%prep
%setup -q

%build
# Nothing to build - pre-compiled binary

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/usr/bin
mkdir -p %{buildroot}/usr/share/applications
mkdir -p %{buildroot}/usr/share/icons/hicolor/256x256/apps
mkdir -p %{buildroot}/usr/share/doc/%{name}

install -m 755 FatigueDetectionApp %{buildroot}/usr/bin/
install -m 644 fatigue-detection.desktop %{buildroot}/usr/share/applications/
install -m 644 app_icon.png %{buildroot}/usr/share/icons/hicolor/256x256/apps/fatigue-detection.png
install -m 644 README.md %{buildroot}/usr/share/doc/%{name}/

%files
/usr/bin/FatigueDetectionApp
/usr/share/applications/fatigue-detection.desktop
/usr/share/icons/hicolor/256x256/apps/fatigue-detection.png
/usr/share/doc/%{name}/README.md

%post
update-desktop-database /usr/share/applications
gtk-update-icon-cache -f -t /usr/share/icons/hicolor

%postun
update-desktop-database /usr/share/applications
gtk-update-icon-cache -f -t /usr/share/icons/hicolor

%changelog
* Fri Nov 29 2025 Your Name <email@example.com> - 1.0.0-1
- Initial RPM release
EOF

# Create source tarball
tar -czf ~/rpmbuild/SOURCES/driver-fatigue-detection-1.0.0.tar.gz \
    --transform 's,^,driver-fatigue-detection-1.0.0/,' \
    dist/FatigueDetectionApp \
    assets/icon/app_icon.png \
    README.md \
    fatigue-detection.desktop

# Build RPM
rpmbuild -ba ~/rpmbuild/SPECS/driver-fatigue-detection.spec
```

##### 5. Create Snap Package
```bash
# Install snapcraft
sudo apt install snapcraft

# Create snapcraft.yaml
mkdir snap
cat > snap/snapcraft.yaml << 'EOF'
name: driver-fatigue-detection
version: '1.0.0'
summary: Real-time driver fatigue detection system
description: |
  A comprehensive system for detecting driver fatigue using computer vision
  and machine learning techniques. The application monitors eye movements,
  head pose, and other fatigue indicators to alert drivers in real-time.

base: core20
grade: stable
confinement: strict

apps:
  driver-fatigue-detection:
    command: usr/bin/FatigueDetectionApp
    desktop: usr/share/applications/fatigue-detection.desktop
    plugs:
      - camera
      - audio-playback
      - desktop
      - desktop-legacy
      - wayland
      - x11
      - home
      - network

parts:
  driver-fatigue-detection:
    plugin: dump
    source: .
    organize:
      dist/FatigueDetectionApp: usr/bin/FatigueDetectionApp
      assets/icon/app_icon.png: usr/share/icons/hicolor/256x256/apps/fatigue-detection.png
    stage-packages:
      - python3
      - python3-tk
      - libgtk-3-0
      - libgstreamer1.0-0
EOF

# Build snap
snapcraft
```

##### 6. Create Flatpak Package
```bash
# Install flatpak-builder
sudo apt install flatpak-builder

# Create manifest
cat > com.fatiguedetection.App.json << 'EOF'
{
    "app-id": "com.fatiguedetection.App",
    "runtime": "org.freedesktop.Platform",
    "runtime-version": "22.08",
    "sdk": "org.freedesktop.Sdk",
    "command": "FatigueDetectionApp",
    "finish-args": [
        "--share=ipc",
        "--socket=x11",
        "--socket=wayland",
        "--device=all",
        "--share=network",
        "--filesystem=home"
    ],
    "modules": [
        {
            "name": "driver-fatigue-detection",
            "buildsystem": "simple",
            "build-commands": [
                "install -Dm755 FatigueDetectionApp /app/bin/FatigueDetectionApp",
                "install -Dm644 com.fatiguedetection.App.desktop /app/share/applications/com.fatiguedetection.App.desktop",
                "install -Dm644 app_icon.png /app/share/icons/hicolor/256x256/apps/com.fatiguedetection.App.png"
            ],
            "sources": [
                {
                    "type": "file",
                    "path": "dist/FatigueDetectionApp"
                },
                {
                    "type": "file",
                    "path": "assets/icon/app_icon.png"
                },
                {
                    "type": "file",
                    "path": "com.fatiguedetection.App.desktop"
                }
            ]
        }
    ]
}
EOF

# Create desktop file for Flatpak
cat > com.fatiguedetection.App.desktop << EOF
[Desktop Entry]
Type=Application
Name=Driver Fatigue Detection
Comment=Real-time driver fatigue detection system
Exec=FatigueDetectionApp
Icon=com.fatiguedetection.App
Categories=Utility;Science;
Terminal=false
StartupNotify=true
EOF

# Build Flatpak
flatpak-builder build com.fatiguedetection.App.json
```

## Installation Methods

### AppImage Installation

#### Download and Run
```bash
# Download AppImage
wget https://github.com/yourorg/driver-fatigue-detection/releases/download/v1.0.0/FatigueDetectionApp-1.0.0-x86_64.AppImage

# Make executable
chmod +x FatigueDetectionApp-1.0.0-x86_64.AppImage

# Run directly
./FatigueDetectionApp-1.0.0-x86_64.AppImage
```

#### Desktop Integration
```bash
# Install AppImageLauncher for system integration
sudo apt install appimagelauncher  # Ubuntu/Debian
sudo dnf install appimagelauncher  # Fedora

# Or manual integration
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/fatigue-detection.desktop << EOF
[Desktop Entry]
Type=Application
Name=Driver Fatigue Detection
Exec=/path/to/FatigueDetectionApp-1.0.0-x86_64.AppImage
Icon=/path/to/app_icon.png
Categories=Utility;Science;
EOF
```

### DEB Package Installation

#### Using APT (if repository available)
```bash
# Add repository (if available)
curl -fsSL https://yourorg.com/apt/gpg | sudo gpg --dearmor -o /usr/share/keyrings/fatigue-detection.gpg
echo "deb [signed-by=/usr/share/keyrings/fatigue-detection.gpg] https://yourorg.com/apt stable main" | sudo tee /etc/apt/sources.list.d/fatigue-detection.list

# Update and install
sudo apt update
sudo apt install driver-fatigue-detection
```

#### Direct Installation
```bash
# Download DEB package
wget https://github.com/yourorg/driver-fatigue-detection/releases/download/v1.0.0/driver-fatigue-detection_1.0.0_amd64.deb

# Install with dpkg
sudo dpkg -i driver-fatigue-detection_1.0.0_amd64.deb

# Fix dependencies if needed
sudo apt install -f
```

#### Using GDebi (GUI)
```bash
# Install GDebi
sudo apt install gdebi

# Install package
sudo gdebi driver-fatigue-detection_1.0.0_amd64.deb
```

### RPM Package Installation

#### Using DNF/YUM
```bash
# Install directly
sudo dnf install https://github.com/yourorg/driver-fatigue-detection/releases/download/v1.0.0/driver-fatigue-detection-1.0.0-1.x86_64.rpm

# Or download and install
wget https://github.com/yourorg/driver-fatigue-detection/releases/download/v1.0.0/driver-fatigue-detection-1.0.0-1.x86_64.rpm
sudo dnf install driver-fatigue-detection-1.0.0-1.x86_64.rpm
```

#### Using RPM directly
```bash
sudo rpm -ivh driver-fatigue-detection-1.0.0-1.x86_64.rpm
```

### Snap Installation

#### From Snap Store
```bash
sudo snap install driver-fatigue-detection
```

#### From Local File
```bash
sudo snap install driver-fatigue-detection_1.0.0_amd64.snap --dangerous
```

### Flatpak Installation

#### From Flathub
```bash
flatpak install flathub com.fatiguedetection.App
```

#### From Local File
```bash
flatpak install driver-fatigue-detection.flatpak
```

## Desktop Integration

### Desktop Entry
Standard `.desktop` file for all package formats:
```ini
[Desktop Entry]
Type=Application
Version=1.0
Name=Driver Fatigue Detection
GenericName=Fatigue Detection System
Comment=Real-time driver fatigue detection system
Exec=FatigueDetectionApp
Icon=fatigue-detection
Terminal=false
Categories=Utility;Science;AudioVideo;Security;
Keywords=fatigue;driver;detection;safety;monitoring;camera;
StartupNotify=true
StartupWMClass=FatigueDetectionApp
MimeType=application/x-fatigue-data;
Actions=Configure;

[Desktop Action Configure]
Name=Configure Settings
Exec=FatigueDetectionApp --configure
```

### MIME Type Registration
Create `fatigue-detection.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="application/x-fatigue-data">
    <comment>Fatigue Detection Data</comment>
    <icon name="fatigue-detection"/>
    <glob pattern="*.fatigue"/>
    <glob pattern="*.fdata"/>
  </mime-type>
</mime-info>
```

### Icon Themes
Provide icons in multiple sizes:
```
usr/share/icons/hicolor/
├── 16x16/apps/fatigue-detection.png
├── 24x24/apps/fatigue-detection.png
├── 32x32/apps/fatigue-detection.png
├── 48x48/apps/fatigue-detection.png
├── 64x64/apps/fatigue-detection.png
├── 128x128/apps/fatigue-detection.png
├── 256x256/apps/fatigue-detection.png
└── scalable/apps/fatigue-detection.svg
```

## Distribution

### GitHub Releases
```bash
# Create release with all packages
gh release create v1.0.0 \
    FatigueDetectionApp-1.0.0-x86_64.AppImage \
    driver-fatigue-detection_1.0.0_amd64.deb \
    driver-fatigue-detection-1.0.0-1.x86_64.rpm \
    driver-fatigue-detection_1.0.0_amd64.snap \
    --title "Driver Fatigue Detection v1.0.0" \
    --notes "Initial release with multi-platform support"
```

### Package Repositories

#### Creating APT Repository
```bash
# Setup repository structure
mkdir -p apt-repo/{conf,dists/stable/main/binary-amd64}

# Create repository configuration
cat > apt-repo/conf/distributions << EOF
Codename: stable
Suite: stable
Components: main
Architectures: amd64
Description: Driver Fatigue Detection Repository
SignWith: YOUR_GPG_KEY_ID
EOF

# Add packages
reprepro -b apt-repo includedeb stable driver-fatigue-detection_1.0.0_amd64.deb
```

#### Snap Store Submission
```bash
# Login to Snap Store
snapcraft login

# Register name
snapcraft register driver-fatigue-detection

# Upload snap
snapcraft upload driver-fatigue-detection_1.0.0_amd64.snap

# Release to channels
snapcraft release driver-fatigue-detection 1 stable
```

#### Flathub Submission
1. Fork the Flathub repository
2. Create app manifest in `com.fatiguedetection.App` directory
3. Submit pull request
4. Follow review process

### Third-Party Repositories

#### AUR (Arch User Repository)
Create `PKGBUILD`:
```bash
pkgname=driver-fatigue-detection
pkgver=1.0.0
pkgrel=1
pkgdesc="Real-time driver fatigue detection system"
arch=('x86_64')
url="https://github.com/yourorg/driver-fatigue-detection"
license=('MIT')
depends=('python' 'python-opencv' 'gtk3')
source=("https://github.com/yourorg/driver-fatigue-detection/releases/download/v$pkgver/FatigueDetectionApp-$pkgver-linux-x86_64.tar.gz")
sha256sums=('SKIP')

package() {
    install -Dm755 "$srcdir/FatigueDetectionApp" "$pkgdir/usr/bin/FatigueDetectionApp"
    install -Dm644 "$srcdir/fatigue-detection.desktop" "$pkgdir/usr/share/applications/fatigue-detection.desktop"
    install -Dm644 "$srcdir/app_icon.png" "$pkgdir/usr/share/icons/hicolor/256x256/apps/fatigue-detection.png"
}
```

## Troubleshooting

### Build Issues

#### 1. Missing System Dependencies
**Problem**: Build fails due to missing libraries
**Solution**: Install development packages:
```bash
# Debian/Ubuntu
sudo apt install build-essential pkg-config libgtk-3-dev

# Fedora
sudo dnf groupinstall "Development Tools"
sudo dnf install gtk3-devel
```

#### 2. PyInstaller Import Errors
**Problem**: Hidden imports not found
**Solution**: Add to spec file:
```python
hiddenimports=[
    'PIL._imaging',
    'cv2',
    'numpy.core._methods'
]
```

#### 3. Large Package Size
**Problem**: Packages are too large
**Solutions**:
- Exclude unnecessary modules
- Use external dependencies
- Optimize asset compression

### Installation Issues

#### 1. Dependency Conflicts
**Problem**: Package dependencies conflict
**Solutions**:
```bash
# Force installation
sudo dpkg -i --force-depends package.deb

# Use different package format
# Try AppImage instead
```

#### 2. Permission Denied
**Problem**: Cannot access camera/microphone
**Solutions**:
```bash
# Add user to video group
sudo usermod -a -G video $USER

# Check device permissions
ls -l /dev/video0

# For Flatpak/Snap, check permissions
flatpak permissions com.fatiguedetection.App
snap connections driver-fatigue-detection
```

#### 3. Desktop Integration Issues
**Problem**: Application not showing in menu
**Solutions**:
```bash
# Update desktop database
sudo update-desktop-database

# Update icon cache
sudo gtk-update-icon-cache /usr/share/icons/hicolor

# Check desktop file
desktop-file-validate /usr/share/applications/fatigue-detection.desktop
```

### Runtime Issues

#### 1. Library Loading Errors
**Problem**: Shared libraries not found
**Solutions**:
```bash
# Check missing libraries
ldd FatigueDetectionApp

# Install missing packages
sudo apt install libgtk-3-0 libgstreamer1.0-0

# Use AppImage for self-contained solution
```

#### 2. Graphics Issues
**Problem**: GUI not displaying correctly
**Solutions**:
```bash
# Force X11 backend
export GDK_BACKEND=x11

# Check Wayland compatibility
echo $XDG_SESSION_TYPE

# Install additional GUI libraries
sudo apt install libqt5gui5
```

#### 3. Performance Issues
**Problem**: Application runs slowly
**Solutions**:
- Check system resources
- Verify GPU acceleration
- Use hardware-optimized builds
- Check for memory leaks

### Package-Specific Issues

#### AppImage
```bash
# Extract AppImage for debugging
./app.AppImage --appimage-extract

# Run with verbose output
./app.AppImage --appimage-verbose

# Check FUSE availability
fusermount --version
```

#### Snap
```bash
# Debug snap issues
snap logs driver-fatigue-detection

# Check snap confinement
snap info driver-fatigue-detection

# Grant additional permissions
snap connect driver-fatigue-detection:camera
```

#### Flatpak
```bash
# Debug Flatpak issues
flatpak run --devel com.fatiguedetection.App

# Check permissions
flatpak info --show-permissions com.fatiguedetection.App

# Grant permissions
flatpak permission-set devices camera com.fatiguedetection.App yes
```

### Getting Help

#### Useful Commands
```bash
# System information
uname -a
cat /etc/os-release
lscpu
free -h

# Graphics information
lspci | grep VGA
glxinfo | grep "OpenGL version"

# Camera information
lsusb | grep -i camera
v4l2-ctl --list-devices

# Check logs
journalctl -f
dmesg | tail
```

#### Support Channels
1. **GitHub Issues**: Report bugs and feature requests
2. **Distribution Forums**: Distro-specific installation help
3. **Community Chat**: Real-time support and discussion
4. **Documentation**: Check online documentation

Remember to include detailed system information when reporting issues.
