# Windows Installer Guide

This document provides comprehensive instructions for creating and using the Windows installer for the Driver Fatigue Detection System.

## Table of Contents

- [Overview](#overview)
- [Installer Features](#installer-features)
- [Building the Installer](#building-the-installer)
- [Installation Process](#installation-process)
- [Uninstallation](#uninstallation)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)

## Overview

The Windows installer is created using NSIS (Nullsoft Scriptable Install System) and provides a professional installation experience for end users. The installer packages the PyInstaller-built executable along with all necessary dependencies, assets, and configuration files.

## Installer Features

### Core Features
- **Modern UI**: Professional installation interface
- **Component Selection**: Choose what to install
- **Desktop Shortcut**: Optional desktop shortcut creation
- **Start Menu Integration**: Program group and shortcuts
- **File Associations**: Associate .fatigue files with the application
- **Uninstaller**: Complete removal with registry cleanup
- **Dependencies**: Automatic VC++ Redistributable installation

### Installation Components
1. **Core Application** (Required)
   - Main executable
   - Required libraries and assets
   - Configuration files

2. **Desktop Shortcut** (Optional)
   - Desktop icon for quick access

3. **Start Menu Shortcuts** (Optional)
   - Program group in Start Menu
   - Uninstaller shortcut

4. **Visual C++ Redistributable** (Optional)
   - Microsoft VC++ Runtime libraries
   - Required for optimal performance

5. **File Associations** (Optional)
   - Associate .fatigue files with the application
   - Enable double-click to open data files

## Building the Installer

### Prerequisites

1. **NSIS Installation**
```powershell
# Download NSIS from https://nsis.sourceforge.io/
# Install to default location (C:\Program Files (x86)\NSIS\)

# Verify installation
makensis.exe /VERSION
```

2. **Build the Application**
```powershell
# Build the main application first
.\build-windows.ps1 -BuildMode onefile
```

3. **Required Files**
- `dist/FatigueDetectionApp.exe` - Main executable
- `assets/` - Application assets
- `config/` - Configuration files
- `installer/setup.nsi` - NSIS script

### Building Process

#### Method 1: Using Build Script (Recommended)
```powershell
# Build application and installer
.\build-windows.ps1 -CreateInstaller
```

#### Method 2: Manual Build
```powershell
# Navigate to project root
cd "C:\path\to\driver-fatigue-detection"

# Build installer
makensis.exe installer\setup.nsi
```

#### Method 3: Visual Build
```powershell
# Open NSIS GUI
& "C:\Program Files (x86)\NSIS\makensisw.exe"
# Drag setup.nsi to the window or use File > Load Script
```

### Build Output

The installer will be created as:
- `FatigueDetectionApp-Setup.exe` - Complete installer package
- Size: Approximately 50-100 MB (depending on build mode)

## Installation Process

### System Requirements
- **Operating System**: Windows 10 or later (64-bit recommended)
- **Processor**: Intel Core i3 or equivalent
- **Memory**: 4 GB RAM minimum, 8 GB recommended
- **Storage**: 500 MB free disk space
- **Camera**: USB webcam or built-in camera
- **Permissions**: Administrator rights for installation

### Installation Steps

1. **Download Installer**
   - Download `FatigueDetectionApp-Setup.exe`
   - Verify file integrity if hash provided

2. **Run Installer**
   ```cmd
   # Run as administrator (recommended)
   FatigueDetectionApp-Setup.exe
   
   # Silent installation
   FatigueDetectionApp-Setup.exe /S
   
   # Install to custom directory
   FatigueDetectionApp-Setup.exe /D=C:\CustomPath\FatigueDetection
   ```

3. **Installation Wizard**
   - **Welcome Screen**: Introduction and requirements
   - **License Agreement**: Accept terms and conditions
   - **Component Selection**: Choose installation components
   - **Installation Directory**: Select destination folder
   - **Start Menu Folder**: Choose program group name
   - **Installation Progress**: Wait for files to be copied
   - **Completion**: Launch application option

4. **Post-Installation**
   - Camera permissions may be requested on first run
   - Configuration wizard may appear for first-time setup

### Installation Options

#### Silent Installation
```cmd
# Completely silent installation
FatigueDetectionApp-Setup.exe /S

# Silent with custom directory
FatigueDetectionApp-Setup.exe /S /D=C:\MyApps\FatigueDetection

# Silent with specific components
FatigueDetectionApp-Setup.exe /S /COMPONENTS="main,desktop,startmenu"
```

#### Component Selection
- `main` - Core application (required)
- `desktop` - Desktop shortcut
- `startmenu` - Start Menu shortcuts
- `vcredist` - Visual C++ Redistributable
- `fileassoc` - File associations

#### Registry Settings
The installer creates registry entries for:
- Uninstall information
- Application settings
- File associations
- Installation path tracking

## Uninstallation

### Using Windows Settings
1. Open Windows Settings (`Win + I`)
2. Navigate to Apps > Apps & features
3. Search for "Driver Fatigue Detection"
4. Click "Uninstall"

### Using Control Panel
1. Open Control Panel
2. Navigate to Programs > Programs and Features
3. Find "Driver Fatigue Detection System"
4. Click "Uninstall"

### Using Start Menu
1. Open Start Menu
2. Find "Driver Fatigue Detection" program group
3. Click "Uninstall Driver Fatigue Detection"

### Silent Uninstallation
```cmd
# Find uninstaller path in registry or use
"C:\Program Files\Driver Fatigue Detection\Uninstall.exe" /S
```

### What Gets Removed
- Application executable and libraries
- Desktop shortcuts (if created)
- Start Menu entries
- File associations
- Registry entries
- Application data (optional, user choice)

### What's Preserved
- User data in `%APPDATA%\FatigueDetection\` (optional)
- Log files (if user chooses to keep)
- Configuration customizations (optional)

## Customization

### Modifying the Installer

The installer script (`installer/setup.nsi`) can be customized:

#### Basic Settings
```nsis
# Application information
!define APP_NAME "Driver Fatigue Detection System"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "Your Company"
!define APP_URL "https://yourwebsite.com"

# File information
!define APP_EXE "FatigueDetectionApp.exe"
!define APP_ICON "assets\icon\app_icon.ico"
```

#### Installation Directory
```nsis
# Default installation directory
InstallDir "$PROGRAMFILES64\Driver Fatigue Detection"

# Allow user to change directory
DirText "Choose the directory to install $(^NameDA):"
```

#### Components
```nsis
# Add new component
Section "Additional Tools" SecTools
  ; Installation code here
SectionEnd
```

#### Custom Pages
```nsis
# Add custom page
Page custom CustomPage
Function CustomPage
  ; Custom page implementation
FunctionEnd
```

### Branding

#### Visual Customization
- **Installer Icon**: Replace `app_icon.ico`
- **Header Image**: Add custom header bitmap
- **Side Image**: Add custom wizard image
- **Colors**: Customize UI colors

#### Text Customization
- **Welcome Text**: Modify welcome message
- **License Text**: Update license agreement
- **Component Descriptions**: Change component descriptions
- **Completion Message**: Customize finish page

### Advanced Features

#### Digital Signing
```cmd
# Sign the installer (requires code signing certificate)
signtool sign /f certificate.p12 /p password /t http://timestamp.digicert.com FatigueDetectionApp-Setup.exe
```

#### Update Detection
```nsis
# Check for existing installation
ReadRegStr $R0 HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString"
StrCmp $R0 "" done

# Prompt for upgrade
MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
  "${APP_NAME} is already installed. $\n$\nClick OK to remove the previous version or Cancel to cancel this upgrade." \
  IDOK uninst
Abort
```

#### Custom Installation Options
```nsis
# Create custom installation types
InstType "Minimal"
InstType "Standard"
InstType "Complete"
InstType /NOCUSTOM

# Assign components to installation types
Section "Core Application" SecCore
  SectionIn RO 1 2 3  ; Required, in all install types
SectionEnd

Section "Desktop Shortcut" SecDesktop
  SectionIn 2 3      ; In Standard and Complete
SectionEnd
```

## Troubleshooting

### Common Installation Issues

#### 1. Insufficient Permissions
**Problem**: "Access denied" or permission errors
**Solutions**:
- Run installer as Administrator
- Check user account permissions
- Temporarily disable antivirus software

#### 2. Missing Dependencies
**Problem**: Application fails to start after installation
**Solutions**:
- Install Visual C++ Redistributable manually
- Check for missing system libraries
- Run dependency checker tool

#### 3. Installation Corruption
**Problem**: Files missing or corrupted during installation
**Solutions**:
- Re-download installer
- Check disk space availability
- Run disk cleanup and retry

#### 4. Registry Issues
**Problem**: Uninstaller not appearing in Programs list
**Solutions**:
- Run installer repair mode
- Manually clean registry entries
- Reinstall application

### Installer Build Issues

#### 1. NSIS Not Found
**Problem**: `makensis.exe` command not recognized
**Solutions**:
```powershell
# Add NSIS to PATH
$env:PATH += ";C:\Program Files (x86)\NSIS"

# Or use full path
& "C:\Program Files (x86)\NSIS\makensis.exe" installer\setup.nsi
```

#### 2. File Not Found Errors
**Problem**: Referenced files missing during build
**Solutions**:
- Verify all file paths in setup.nsi
- Ensure application was built successfully
- Check relative path references

#### 3. Icon/Resource Issues
**Problem**: Icons not displaying correctly
**Solutions**:
- Verify icon file format (.ico for Windows)
- Check icon file path in script
- Ensure icon dimensions are correct

### Runtime Issues

#### 1. Antivirus False Positives
**Problem**: Installer flagged as malware
**Solutions**:
- Submit installer for whitelist review
- Sign installer with code signing certificate
- Add build environment details to documentation

#### 2. Compatibility Issues
**Problem**: Application doesn't work on specific Windows versions
**Solutions**:
- Test on target Windows versions
- Update system requirements
- Add compatibility shims if needed

#### 3. Performance Issues
**Problem**: Slow installation or large installer size
**Solutions**:
- Use compression options in NSIS
- Optimize included files
- Consider separate dependency installers

### Getting Help

1. **Check Logs**: Windows Event Viewer for installation errors
2. **NSIS Documentation**: Official NSIS documentation and forums
3. **Application Logs**: Check application-specific log files
4. **Community Support**: Post issues with detailed error messages

### Useful Commands

```cmd
# Check installer details
FatigueDetectionApp-Setup.exe /?

# Extract installer contents (debugging)
FatigueDetectionApp-Setup.exe /EXTRACTONLY

# Install with logging
FatigueDetectionApp-Setup.exe /S /LOG=install.log

# Verify installation
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Driver Fatigue Detection System"
```
