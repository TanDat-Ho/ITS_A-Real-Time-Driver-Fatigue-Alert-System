# macOS Code Signing Guide

This guide covers code signing and notarization for macOS distribution of the Driver Fatigue Detection System.

## Prerequisites

### Apple Developer Account
- **Required**: Apple Developer Program membership ($99/year)
- **Account Type**: Individual or Organization
- **Access**: Apple Developer Portal access

### Development Environment
- **macOS**: 10.15 (Catalina) or later
- **Xcode**: Latest version with Command Line Tools
- **Certificates**: Developer ID Application certificate

## Setting Up Code Signing

### 1. Certificates and Identities

#### Request Developer ID Certificate
1. Open **Keychain Access**
2. Go to **Certificate Assistant** → **Request a Certificate from a Certificate Authority**
3. Fill in your email and name, select **Saved to disk**
4. Upload `.certSigningRequest` file to Apple Developer Portal
5. Download the certificate and install in Keychain

#### Verify Certificate Installation
```bash
# List available code signing certificates
security find-identity -v -p codesigning

# Expected output should include:
# 1) ABC123... "Developer ID Application: Your Name (TEAM_ID)"
```

### 2. Environment Configuration

#### Set Environment Variables
```bash
# Add to ~/.zshrc or ~/.bash_profile
export DEVELOPER_ID="Developer ID Application: Your Name (TEAM_ID)"
export TEAM_ID="YOUR_APPLE_TEAM_ID"
export APPLE_ID="your-apple-id@example.com"

# Reload shell configuration
source ~/.zshrc
```

#### Create App-Specific Password
1. Go to [appleid.apple.com](https://appleid.apple.com)
2. Sign in with your Apple ID
3. Go to **Security** → **App-Specific Passwords**
4. Generate new password for "notarytool"
5. Save the password securely

### 3. Notarization Setup

#### Store Credentials in Keychain
```bash
# Create notarization profile
xcrun notarytool store-credentials "notarytool-profile" \
  --apple-id "$APPLE_ID" \
  --team-id "$TEAM_ID" \
  --password "app-specific-password"

# Verify profile
xcrun notarytool history --keychain-profile "notarytool-profile"
```

#### Set Notarization Environment
```bash
# Add to shell configuration
export NOTARIZATION_PROFILE="notarytool-profile"
```

## Code Signing Process

### 1. Entitlements Configuration

The build script automatically creates `entitlements.plist` with required permissions:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- Camera access for fatigue detection -->
    <key>com.apple.security.camera</key>
    <true/>
    
    <!-- Microphone access for audio alerts -->
    <key>com.apple.security.microphone</key>
    <true/>
    
    <!-- Device access -->
    <key>com.apple.security.device.audio-input</key>
    <true/>
    <key>com.apple.security.device.camera</key>
    <true/>
    
    <!-- Runtime hardening options -->
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
    
    <!-- System integration -->
    <key>com.apple.security.automation.apple-events</key>
    <true/>
</dict>
</plist>
```

### 2. Building with Code Signing

#### Basic Build with Signing
```bash
# Set environment variables
export DEVELOPER_ID="Developer ID Application: Your Name (TEAM_ID)"

# Build and sign
./build-macos.sh --sign
```

#### Build with Notarization
```bash
# Set environment variables
export DEVELOPER_ID="Developer ID Application: Your Name (TEAM_ID)"
export NOTARIZATION_PROFILE="notarytool-profile"

# Build, sign, and notarize
./build-macos.sh --sign --notarize
```

#### Universal Binary with Signing
```bash
# Create Universal Binary (Intel + Apple Silicon) with signing
./build-macos.sh --universal --sign --notarize
```

### 3. Manual Code Signing

If you need to sign manually:

#### Sign App Bundle
```bash
# Sign all binaries in the bundle
find "dist/FatigueDetectionApp.app" -type f \( -name "*.dylib" -o -name "*.so" \) \
  -exec codesign --force --options runtime --sign "$DEVELOPER_ID" {} \;

# Sign frameworks (if any)
find "dist/FatigueDetectionApp.app/Contents/Frameworks" -type d -name "*.framework" \
  -exec codesign --force --options runtime --sign "$DEVELOPER_ID" {} \; 2>/dev/null || true

# Sign the main app bundle
codesign --force --options runtime \
  --entitlements entitlements.plist \
  --sign "$DEVELOPER_ID" \
  "dist/FatigueDetectionApp.app"
```

#### Verify Signature
```bash
# Verify code signature
codesign --verify --deep --strict "dist/FatigueDetectionApp.app"

# Display signature details
codesign --display --verbose=2 "dist/FatigueDetectionApp.app"

# Check Gatekeeper assessment
spctl --assess --verbose "dist/FatigueDetectionApp.app"
```

#### Sign DMG
```bash
# Sign the DMG file
codesign --force --sign "$DEVELOPER_ID" "FatigueDetectionApp-1.0.0-macOS.dmg"

# Verify DMG signature
codesign --verify --verbose=2 "FatigueDetectionApp-1.0.0-macOS.dmg"
```

## Notarization Process

### 1. Submit for Notarization

#### Submit App Bundle
```bash
# Submit app bundle for notarization
xcrun notarytool submit "dist/FatigueDetectionApp.app" \
  --keychain-profile "notarytool-profile" \
  --wait

# Submit as ZIP for better compatibility
zip -r "FatigueDetectionApp.zip" "dist/FatigueDetectionApp.app"
xcrun notarytool submit "FatigueDetectionApp.zip" \
  --keychain-profile "notarytool-profile" \
  --wait
```

#### Submit DMG
```bash
# Submit DMG for notarization
xcrun notarytool submit "FatigueDetectionApp-1.0.0-macOS.dmg" \
  --keychain-profile "notarytool-profile" \
  --wait
```

### 2. Check Notarization Status

#### Monitor Submission
```bash
# Check submission history
xcrun notarytool history --keychain-profile "notarytool-profile"

# Get detailed log for specific submission
xcrun notarytool log SUBMISSION_ID --keychain-profile "notarytool-profile"
```

### 3. Staple Notarization

#### Staple to App Bundle
```bash
# Staple notarization to app bundle
xcrun stapler staple "dist/FatigueDetectionApp.app"

# Verify stapling
xcrun stapler validate "dist/FatigueDetectionApp.app"
```

#### Staple to DMG
```bash
# Staple notarization to DMG
xcrun stapler staple "FatigueDetectionApp-1.0.0-macOS.dmg"

# Verify stapling
xcrun stapler validate "FatigueDetectionApp-1.0.0-macOS.dmg"
```

## Troubleshooting

### Common Signing Issues

#### 1. Certificate Not Found
**Error**: "No signing identity found"

**Solutions**:
```bash
# Check certificates in Keychain
security find-identity -v -p codesigning

# Refresh certificates
security delete-identity -c "Developer ID Application: Your Name"
# Re-import certificate from .p12 file

# Check certificate validity
security find-certificate -c "Developer ID Application: Your Name" -p | openssl x509 -text
```

#### 2. Entitlements Issues
**Error**: "App-specific entitlement violations"

**Solutions**:
- Review entitlements.plist for required permissions
- Remove unnecessary entitlements
- Ensure entitlements match app functionality

#### 3. Hardened Runtime Issues
**Error**: "Crashed due to hardened runtime restrictions"

**Solutions**:
```xml
<!-- Add to entitlements.plist if needed -->
<key>com.apple.security.cs.allow-jit</key>
<true/>
<key>com.apple.security.cs.allow-unsigned-executable-memory</key>
<true/>
<key>com.apple.security.cs.disable-library-validation</key>
<true/>
```

### Notarization Issues

#### 1. Submission Rejected
**Error**: "The software asset has been rejected"

**Solutions**:
```bash
# Get detailed rejection reason
xcrun notarytool log SUBMISSION_ID --keychain-profile "notarytool-profile"

# Common issues and fixes:
# - Unsigned binaries: Sign all binaries in the bundle
# - Missing entitlements: Add required entitlements
# - Malware detected: Check for false positives
```

#### 2. Notarization Timeout
**Error**: "Request timed out"

**Solutions**:
- Check internet connection
- Try submitting smaller chunks
- Use ZIP format instead of direct app bundle

#### 3. Stapling Failed
**Error**: "Could not staple"

**Solutions**:
```bash
# Ensure notarization completed successfully first
xcrun notarytool history --keychain-profile "notarytool-profile"

# Try stapling again
xcrun stapler staple "path/to/app"

# Check if already stapled
xcrun stapler validate "path/to/app"
```

## Distribution Checklist

### Pre-Distribution Verification

#### Security Verification
```bash
# Verify app signature
codesign --verify --deep --strict "dist/FatigueDetectionApp.app"

# Check Gatekeeper assessment
spctl --assess --verbose "dist/FatigueDetectionApp.app"

# Verify notarization
xcrun stapler validate "dist/FatigueDetectionApp.app"
```

#### Functional Testing
- [ ] App launches without Gatekeeper warnings
- [ ] Camera permissions requested properly
- [ ] All features work as expected
- [ ] No runtime crashes or errors

#### DMG Verification
```bash
# Mount DMG and test
hdiutil mount "FatigueDetectionApp-1.0.0-macOS.dmg"
cp "/Volumes/Driver Fatigue Detection/FatigueDetectionApp.app" "/Applications/"
"/Applications/FatigueDetectionApp.app/Contents/MacOS/FatigueDetectionApp"
```

### Distribution Notes

#### User Instructions
- **For signed and notarized apps**: Direct installation from DMG
- **For unsigned apps**: Right-click → Open → Open (bypass Gatekeeper)

#### Privacy Permissions
Users will see permission dialogs for:
- Camera access (required for fatigue detection)
- Microphone access (optional for audio alerts)

## Automation Scripts

### Complete Build and Sign Script
```bash
#!/bin/bash
# automated-release.sh - Complete build, sign, and notarize

set -e

# Configuration
DEVELOPER_ID="Developer ID Application: Your Name (TEAM_ID)"
NOTARIZATION_PROFILE="notarytool-profile"
VERSION="1.0.0"

# Export environment
export DEVELOPER_ID
export NOTARIZATION_PROFILE

# Clean build
./build-macos.sh --clean-only

# Build universal binary with signing and notarization
./build-macos.sh --universal --sign --notarize

# Verify final products
echo "Verifying final products..."
codesign --verify --deep --strict "dist/FatigueDetectionApp.app"
xcrun stapler validate "FatigueDetectionApp-${VERSION}-macOS.dmg"

echo "✅ Release ready for distribution!"
```

### CI/CD Integration
For GitHub Actions or other CI/CD systems:

```yaml
- name: Import certificates
  run: |
    # Import signing certificate
    echo "${{ secrets.MACOS_CERTIFICATE }}" | base64 --decode > certificate.p12
    security create-keychain -p "${{ secrets.MACOS_CI_KEYCHAIN_PWD }}" build.keychain
    security default-keychain -s build.keychain
    security unlock-keychain -p "${{ secrets.MACOS_CI_KEYCHAIN_PWD }}" build.keychain
    security import certificate.p12 -k build.keychain -P "${{ secrets.MACOS_CERTIFICATE_PWD }}" -T /usr/bin/codesign
    security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "${{ secrets.MACOS_CI_KEYCHAIN_PWD }}" build.keychain

- name: Build and sign
  env:
    DEVELOPER_ID: ${{ secrets.MACOS_CERTIFICATE_NAME }}
    NOTARIZATION_PROFILE: ${{ secrets.NOTARIZATION_PROFILE }}
  run: |
    ./build-macos.sh --sign --notarize
```

This comprehensive guide ensures your macOS builds are properly signed and notarized for distribution through various channels.
