# Building the Driver Fatigue Detection Application

This guide provides comprehensive instructions for building the Driver Fatigue Detection System into standalone executables using PyInstaller.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Build Methods](#build-methods)
- [Platform-Specific Instructions](#platform-specific-instructions)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

## Overview

The Driver Fatigue Detection System can be packaged into standalone executables for Windows, Linux, and macOS using PyInstaller. This eliminates the need for users to have Python installed on their systems.

### Build Outputs

- **Windows**: `.exe` executable + NSIS installer
- **Linux**: Executable + AppImage + DEB package
- **macOS**: App bundle + DMG installer

### Build Modes

- **One-file**: Single executable containing all dependencies
- **One-directory**: Executable with dependencies in a separate folder

## Prerequisites

### All Platforms

- **Python**: Version 3.8-3.11 (recommended: 3.11)
- **Git**: For cloning the repository
- **Virtual Environment**: Recommended for isolated builds

### Windows

- **PowerShell**: Version 5.1 or later
- **NSIS** (optional): For creating installers
- **Visual Studio Build Tools**: For compiling dependencies

### Linux

- **Build essentials**: `build-essential`, `pkg-config`
- **GUI libraries**: `libgtk-3-dev`, `libwebkit2gtk-4.0-dev`
- **AppImage tools**: `linuxdeploy`, `appimagetool`
- **Package tools**: `dpkg-dev`, `fakeroot`

### macOS

- **Xcode Command Line Tools**
- **Homebrew**: For installing dependencies
- **create-dmg**: For DMG creation (`brew install create-dmg`)

## Build Methods

### Method 1: Using Build Scripts (Recommended)

#### Windows
```powershell
# Clone repository
git clone <repository-url>
cd driver-fatigue-detection

# Run build script
.\build-windows.ps1
```

#### Linux/macOS
```bash
# Clone repository
git clone <repository-url>
cd driver-fatigue-detection

# Make script executable and run
chmod +x build-linux.sh
./build-linux.sh
```

### Method 2: Manual Build Process

1. **Setup Environment**
```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.\.venv\Scripts\activate

# Activate (Linux/macOS)
source .venv/bin/activate

# Install dependencies
pip install -r requirements-build.txt
```

2. **Build with PyInstaller**
```bash
# One-file build
pyinstaller fatigue_app.spec --clean --noconfirm

# One-directory build (modify spec file first)
pyinstaller fatigue_app.spec --clean --noconfirm
```

### Method 3: Using CI/CD (GitHub Actions)

The repository includes GitHub Actions workflows that automatically build the application:

- **Windows**: `.github/workflows/build-windows.yml`
- **Linux**: `.github/workflows/build-linux.yml`
- **macOS**: `.github/workflows/build-macos.yml`

Builds are triggered on:
- Push to `main` or `develop` branches
- Pull requests to `main`
- Manual workflow dispatch
- Tagged releases

## Platform-Specific Instructions

### Windows Build

#### Basic Build
```powershell
# Build one-file executable
.\build-windows.ps1 -BuildMode onefile

# Build one-directory
.\build-windows.ps1 -BuildMode onedir

# Skip tests
.\build-windows.ps1 -SkipTests

# Specify architecture
.\build-windows.ps1 -Architecture x86
```

#### Creating Installer
```powershell
# Install NSIS (if not already installed)
# Download from: https://nsis.sourceforge.io/

# Build with installer
.\build-windows.ps1 -CreateInstaller
```

#### Output Files
- `dist/FatigueDetectionApp.exe` - Main executable
- `FatigueDetectionApp-Setup.exe` - NSIS installer

### Linux Build

#### Basic Build
```bash
# Build one-file executable
./build-linux.sh --onefile

# Build one-directory
./build-linux.sh --onedir

# Skip tests
./build-linux.sh --skip-tests
```

#### Creating Packages
```bash
# Create all packages
./build-linux.sh

# Create only AppImage
./build-linux.sh --package-only
```

#### Output Files
- `dist/FatigueDetectionApp` - Main executable
- `FatigueDetectionApp-*.AppImage` - Portable application
- `driver-fatigue-detection_*.deb` - Debian package

### macOS Build

#### Basic Build
```bash
# Build app bundle
./build-linux.sh --onefile

# Build executable only
./build-linux.sh --onedir
```

#### Creating DMG
```bash
# Install create-dmg
brew install create-dmg

# Build with DMG
./build-linux.sh
```

#### Output Files
- `dist/FatigueDetectionApp.app` - App bundle
- `FatigueDetectionApp-*.dmg` - Disk image installer

## Troubleshooting

### Common Issues

#### 1. Import Errors
**Problem**: Missing modules in built executable
**Solution**: Add hidden imports to `fatigue_app.spec`:
```python
hiddenimports=[
    'your.missing.module',
    'another.module'
]
```

#### 2. File Not Found Errors
**Problem**: Missing data files (assets, configs)
**Solution**: Update `datas` in `fatigue_app.spec`:
```python
datas=[
    ('path/to/file', 'destination/path'),
    ('assets/*', 'assets/')
]
```

#### 3. Large Executable Size
**Problem**: Executable is too large
**Solutions**:
- Use one-directory build mode
- Exclude unnecessary modules in spec file
- Use `--strip` option for Linux builds

#### 4. Slow Startup
**Problem**: Application takes long to start
**Solutions**:
- Use one-directory build mode
- Enable lazy imports
- Optimize Python code

#### 5. Missing DLL/SO Files
**Problem**: Dynamic libraries not found
**Solutions**:
- Install Visual C++ Redistributable (Windows)
- Install required system libraries (Linux)
- Use `--add-binary` in PyInstaller

### Platform-Specific Issues

#### Windows
- **Antivirus False Positives**: Add exclusions for build directory
- **Permission Errors**: Run as Administrator if needed
- **Missing MSVC Runtime**: Install Visual C++ Redistributable

#### Linux
- **Library Dependencies**: Install dev packages for GUI libraries
- **Permission Issues**: Ensure execute permissions on scripts
- **AppImage Issues**: Install FUSE if needed

#### macOS
- **Gatekeeper Issues**: Sign and notarize for distribution
- **Permission Dialogs**: Grant camera/microphone access
- **Architecture Issues**: Build universal binaries for compatibility

## Advanced Configuration

### Customizing the Spec File

The `fatigue_app.spec` file controls PyInstaller behavior:

```python
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('config', 'config'),
        ('data', 'data')
    ],
    hiddenimports=[
        'cv2',
        'mediapipe',
        'numpy',
        'PIL',
        'pygame',
        'tkinter'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FatigueDetectionApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon='assets/icon/app_icon.ico'
)

# macOS app bundle
app = BUNDLE(
    exe,
    name='FatigueDetectionApp.app',
    icon='assets/icon/app_icon.icns',
    bundle_identifier='com.fatiguedetection.app',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'NSCameraUsageDescription': 'This app requires camera access for fatigue detection.',
        'NSMicrophoneUsageDescription': 'This app may use microphone for audio alerts.'
    }
)
```

### Build Environment Variables

Control build behavior with environment variables:

```bash
# Windows
$env:PYINSTALLER_COMPILE_BOOTLOADER = "1"
$env:UPX_DIR = "C:\path\to\upx"

# Linux/macOS
export PYINSTALLER_COMPILE_BOOTLOADER=1
export UPX_DIR="/usr/local/bin"
```

### Optimization Options

#### Reducing Build Time
- Use `--noconfirm` to skip confirmations
- Enable build caching
- Use parallel builds where possible

#### Reducing File Size
- Use UPX compression
- Exclude unnecessary modules
- Strip debug symbols (Linux)

#### Improving Performance
- Use one-directory builds for faster startup
- Implement lazy imports
- Optimize critical code paths

## Best Practices

1. **Version Control**: Tag releases for consistent builds
2. **Testing**: Test built executables on clean systems
3. **Documentation**: Document build requirements and steps
4. **Automation**: Use CI/CD for consistent builds
5. **Distribution**: Sign and notarize for security
6. **User Experience**: Provide clear installation instructions

## Getting Help

- Check the [Troubleshooting](#troubleshooting) section
- Review PyInstaller documentation
- Check platform-specific build logs
- Report issues with detailed error messages
