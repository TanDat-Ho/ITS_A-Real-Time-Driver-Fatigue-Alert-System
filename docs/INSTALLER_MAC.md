# macOS Installer Guide

This document provides comprehensive instructions for creating and distributing the macOS installer for the Driver Fatigue Detection System.

## Table of Contents

- [Overview](#overview)
- [Installer Features](#installer-features)
- [Building the Installer](#building-the-installer)
- [Code Signing & Notarization](#code-signing--notarization)
- [Installation Process](#installation-process)
- [Distribution](#distribution)
- [Troubleshooting](#troubleshooting)

## Overview

The macOS installer is distributed as a DMG (Disk Image) file containing the application bundle. This follows Apple's standard distribution practices and provides a familiar installation experience for macOS users.

## Installer Features

### DMG Contents
- **Application Bundle**: `FatigueDetectionApp.app`
- **Applications Folder Shortcut**: Drag-and-drop installation
- **Background Image**: Custom branded background
- **Volume Icon**: Custom DMG icon
- **License Agreement**: Software license display

### Application Bundle Features
- **Universal Binary**: Supports Intel and Apple Silicon Macs
- **Signed and Notarized**: Passes Gatekeeper security checks
- **Privacy Permissions**: Proper camera/microphone access requests
- **System Integration**: Native macOS look and feel
- **Auto-updater**: Built-in update mechanism

## Building the Installer

### Prerequisites

#### Required Tools
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install create-dmg
brew install create-dmg

# Install Python and dependencies
brew install python@3.11
pip3 install -r requirements-build.txt
```

#### Optional Tools
```bash
# For advanced DMG customization
brew install imagemagick  # Image processing
brew install librsvg      # SVG support
```

### Building Process

#### Method 1: Using Build Script (Recommended)
```bash
# Build application and DMG
chmod +x build-linux.sh
./build-linux.sh --onefile
```

#### Method 2: Manual Process

1. **Build Application Bundle**
```bash
# Create app bundle with PyInstaller
python -m PyInstaller fatigue_app.spec --clean --noconfirm

# Verify app bundle
ls -la dist/FatigueDetectionApp.app
```

2. **Create DMG**
```bash
# Basic DMG creation
create-dmg \
  --volname "Driver Fatigue Detection" \
  --volicon "assets/icon/app_icon.icns" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "FatigueDetectionApp.app" 175 120 \
  --hide-extension "FatigueDetectionApp.app" \
  --app-drop-link 425 120 \
  "FatigueDetectionApp-1.0.0-macOS.dmg" \
  "dist/FatigueDetectionApp.app"
```

3. **Advanced DMG Customization**
```bash
# Create DMG with custom background and settings
create-dmg \
  --volname "Driver Fatigue Detection" \
  --volicon "assets/icon/app_icon.icns" \
  --background "assets/dmg-background.png" \
  --window-pos 200 120 \
  --window-size 660 400 \
  --icon-size 80 \
  --icon "FatigueDetectionApp.app" 180 170 \
  --app-drop-link 480 170 \
  --add-file "README.txt" "docs/README_MAC.txt" 340 280 \
  --hide-extension "FatigueDetectionApp.app" \
  --disk-image-size 200 \
  "FatigueDetectionApp-1.0.0-macOS.dmg" \
  "dist/FatigueDetectionApp.app"
```

### Build Configuration

#### PyInstaller Spec File (macOS-specific)
```python
# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

# macOS-specific configuration
if sys.platform == 'darwin':
    icon_file = 'assets/icon/app_icon.icns'
    bundle_identifier = 'com.fatiguedetection.app'
    
    # Info.plist configuration
    info_plist = {
        'CFBundleDisplayName': 'Driver Fatigue Detection',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'CFBundleIdentifier': bundle_identifier,
        'NSCameraUsageDescription': 'This application requires camera access to detect driver fatigue.',
        'NSMicrophoneUsageDescription': 'This application may use the microphone for audio alerts.',
        'NSAppleEventsUsageDescription': 'This application may send Apple Events for system integration.',
        'LSMinimumSystemVersion': '10.14',
        'LSApplicationCategoryType': 'public.app-category.utilities',
        'NSHighResolutionCapable': True,
        'NSSupportsAutomaticGraphicsSwitching': True
    }

# Create app bundle
app = BUNDLE(
    exe,
    name='FatigueDetectionApp.app',
    icon=icon_file,
    bundle_identifier=bundle_identifier,
    info_plist=info_plist,
    version='1.0.0'
)
```

## Code Signing & Notarization

### Prerequisites for Distribution

#### Apple Developer Account
- **Apple ID**: Developer account required
- **Developer Certificate**: Code signing certificate
- **App-Specific Password**: For notarization

#### Certificates Setup
```bash
# List available certificates
security find-identity -v -p codesigning

# Import developer certificate (if not in Keychain)
security import developer_certificate.p12 -k ~/Library/Keychains/login.keychain
```

### Code Signing Process

#### 1. Sign the Application
```bash
# Sign the app bundle
codesign --force --options runtime \
  --sign "Developer ID Application: Your Name (TEAM_ID)" \
  --entitlements entitlements.plist \
  dist/FatigueDetectionApp.app

# Verify signature
codesign --verify --verbose=2 dist/FatigueDetectionApp.app
spctl --assess --verbose dist/FatigueDetectionApp.app
```

#### 2. Create Entitlements File
Create `entitlements.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.camera</key>
    <true/>
    <key>com.apple.security.microphone</key>
    <true/>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
</dict>
</plist>
```

#### 3. Sign the DMG
```bash
# Sign the DMG file
codesign --force --sign "Developer ID Application: Your Name (TEAM_ID)" \
  FatigueDetectionApp-1.0.0-macOS.dmg

# Verify DMG signature
codesign --verify --verbose=2 FatigueDetectionApp-1.0.0-macOS.dmg
```

### Notarization Process

#### 1. Submit for Notarization
```bash
# Store credentials in Keychain
xcrun notarytool store-credentials "notarytool-profile" \
  --apple-id "your-apple-id@example.com" \
  --team-id "TEAM_ID" \
  --password "app-specific-password"

# Submit DMG for notarization
xcrun notarytool submit FatigueDetectionApp-1.0.0-macOS.dmg \
  --keychain-profile "notarytool-profile" \
  --wait

# Alternative: Submit app bundle
xcrun notarytool submit dist/FatigueDetectionApp.app \
  --keychain-profile "notarytool-profile" \
  --wait
```

#### 2. Staple Notarization
```bash
# Staple notarization to DMG
xcrun stapler staple FatigueDetectionApp-1.0.0-macOS.dmg

# Verify notarization
xcrun stapler validate FatigueDetectionApp-1.0.0-macOS.dmg
spctl --assess --verbose FatigueDetectionApp-1.0.0-macOS.dmg
```

### Automated Signing Script
Create `sign-and-notarize.sh`:
```bash
#!/bin/bash

APP_NAME="FatigueDetectionApp"
VERSION="1.0.0"
DEVELOPER_ID="Developer ID Application: Your Name (TEAM_ID)"
PROFILE="notarytool-profile"

# Sign app bundle
echo "Signing app bundle..."
codesign --force --options runtime \
  --sign "$DEVELOPER_ID" \
  --entitlements entitlements.plist \
  dist/$APP_NAME.app

# Create DMG
echo "Creating DMG..."
./build-linux.sh --package-only

# Sign DMG
echo "Signing DMG..."
codesign --force --sign "$DEVELOPER_ID" $APP_NAME-$VERSION-macOS.dmg

# Submit for notarization
echo "Submitting for notarization..."
xcrun notarytool submit $APP_NAME-$VERSION-macOS.dmg \
  --keychain-profile "$PROFILE" \
  --wait

# Staple notarization
echo "Stapling notarization..."
xcrun stapler staple $APP_NAME-$VERSION-macOS.dmg

echo "Code signing and notarization complete!"
```

## Installation Process

### System Requirements
- **Operating System**: macOS 10.14 (Mojave) or later
- **Architecture**: Intel x64 or Apple Silicon (M1/M2)
- **Memory**: 4 GB RAM minimum, 8 GB recommended
- **Storage**: 1 GB free disk space
- **Camera**: Built-in or USB webcam
- **Permissions**: Camera and microphone access

### User Installation Steps

#### 1. Download DMG
- Download `FatigueDetectionApp-1.0.0-macOS.dmg`
- Verify download integrity if hash provided

#### 2. Mount DMG
- Double-click DMG file to mount
- DMG window opens showing installation contents

#### 3. Install Application
- Drag `FatigueDetectionApp.app` to `Applications` folder
- Wait for copy process to complete
- Eject DMG when done

#### 4. First Launch
```bash
# Launch from Finder or Spotlight
open -a "FatigueDetectionApp"

# Or from Terminal
/Applications/FatigueDetectionApp.app/Contents/MacOS/FatigueDetectionApp
```

### Permission Requests
On first launch, macOS will request:
1. **Camera Access**: Required for fatigue detection
2. **Microphone Access**: Optional, for audio alerts
3. **Accessibility**: May be needed for certain features

### Gatekeeper Dialog
If not notarized, users may see:
- "App cannot be opened because it is from an unidentified developer"
- **Solution**: Right-click app → Open → Open (bypass warning)

## Distribution

### Distribution Channels

#### 1. Direct Download
```bash
# Host DMG on your website
curl -L -o FatigueDetectionApp.dmg https://yoursite.com/downloads/FatigueDetectionApp-1.0.0-macOS.dmg
```

#### 2. GitHub Releases
```bash
# Upload to GitHub releases
gh release create v1.0.0 FatigueDetectionApp-1.0.0-macOS.dmg
```

#### 3. Third-Party Platforms
- **Homebrew Cask**: For advanced users
- **MacUpdate**: Software distribution platform
- **Download.com**: Popular download site

### Homebrew Cask (Optional)
Create `Casks/fatigue-detection-app.rb`:
```ruby
cask "fatigue-detection-app" do
  version "1.0.0"
  sha256 "your_dmg_sha256_hash"

  url "https://github.com/yourorg/driver-fatigue-detection/releases/download/v#{version}/FatigueDetectionApp-#{version}-macOS.dmg"
  name "Driver Fatigue Detection"
  desc "Real-time driver fatigue detection system"
  homepage "https://yoursite.com"

  app "FatigueDetectionApp.app"
end
```

### Update Mechanism
Implement auto-updater using Sparkle framework:
```xml
<!-- Info.plist -->
<key>SUFeedURL</key>
<string>https://yoursite.com/updates/appcast.xml</string>
<key>SUPublicEDKey</key>
<string>your-public-key</string>
```

## Troubleshooting

### Build Issues

#### 1. PyInstaller Import Errors
**Problem**: Missing modules in app bundle
**Solution**: Add to hiddenimports in spec file:
```python
hiddenimports=[
    'PIL._imaging',
    'cv2',
    'mediapipe.python._framework_bindings',
    'numpy.core._methods'
]
```

#### 2. Icon Not Displaying
**Problem**: App bundle shows generic icon
**Solutions**:
- Verify `.icns` file format and resolution
- Check icon path in spec file
- Clear icon cache: `sudo find /private/var/folders/ -name com.apple.dock.iconcache -exec rm {} \;`

#### 3. Large App Bundle
**Problem**: App bundle too large (>100MB)
**Solutions**:
- Use `--exclude-module` to remove unused packages
- Optimize included data files
- Consider one-directory build mode

### Code Signing Issues

#### 1. Certificate Not Found
**Problem**: "No signing identity found" error
**Solutions**:
```bash
# Refresh certificates
security find-identity -v -p codesigning

# Re-import certificate
security delete-identity -c "Developer ID Application: Your Name"
# Re-import from .p12 file
```

#### 2. Entitlements Errors
**Problem**: App crashes due to missing entitlements
**Solutions**:
- Verify entitlements.plist syntax
- Check required permissions for app functionality
- Test with minimal entitlements first

#### 3. Notarization Failures
**Problem**: Notarization rejected by Apple
**Solutions**:
```bash
# Get detailed error information
xcrun notarytool log SUBMISSION_ID --keychain-profile "notarytool-profile"

# Common fixes:
# - Ensure all binaries are signed
# - Check entitlements compatibility
# - Verify hardened runtime settings
```

### Runtime Issues

#### 1. Gatekeeper Blocks Execution
**Problem**: "App damaged and cannot be opened"
**Solutions**:
```bash
# Remove quarantine attribute
xattr -rd com.apple.quarantine /Applications/FatigueDetectionApp.app

# Reset Gatekeeper
sudo spctl --master-disable
sudo spctl --master-enable
```

#### 2. Camera Permission Denied
**Problem**: App cannot access camera
**Solutions**:
- Check System Preferences > Security & Privacy > Camera
- Reset privacy permissions:
```bash
sudo tccutil reset Camera com.fatiguedetection.app
```

#### 3. Performance Issues
**Problem**: App runs slowly on Apple Silicon
**Solutions**:
- Build universal binary with `--target-arch=universal2`
- Optimize for ARM64 architecture
- Check Activity Monitor for Rosetta usage

### DMG Issues

#### 1. DMG Won't Mount
**Problem**: "No mountable file systems" error
**Solutions**:
- Verify DMG integrity with `hdiutil verify`
- Re-create DMG with different compression
- Check disk space on target system

#### 2. Custom Background Not Showing
**Problem**: Default folder background appears
**Solutions**:
- Verify background image format (PNG/JPEG)
- Check image dimensions (recommended: 660x400)
- Use absolute path to background image

### Getting Help

#### Useful Commands
```bash
# Check app bundle structure
find FatigueDetectionApp.app -type f | head -20

# Verify all signatures in bundle
codesign --verify --deep --strict FatigueDetectionApp.app

# Check notarization status
spctl --assess --verbose=4 FatigueDetectionApp.app

# View system logs for app
log show --predicate 'process == "FatigueDetectionApp"' --last 1h

# Check entitlements
codesign -d --entitlements - FatigueDetectionApp.app
```

#### Support Resources
1. **Apple Developer Documentation**: Code signing and notarization guides
2. **PyInstaller Documentation**: macOS-specific build instructions
3. **create-dmg Documentation**: DMG customization options
4. **Community Forums**: Stack Overflow, Reddit r/MacOSBeta

#### Contact Information
- **Bug Reports**: Submit with detailed system information
- **Feature Requests**: Include use cases and expected behavior
- **Security Issues**: Contact maintainers directly
