#!/bin/bash
# build-macos.sh - macOS Build Script for Driver Fatigue Detection System
# Supports .app bundle creation, .dmg packaging, code signing, and notarization

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="FatigueDetectionApp"
APP_DISPLAY_NAME="Driver Fatigue Detection"
VERSION="1.0.0"
BUNDLE_ID="com.fatiguedetection.app"
BUILD_DIR="dist"
ASSETS_DIR="assets"
SPEC_FILE="fatigue_app.spec"
DMG_NAME="${APP_NAME}-${VERSION}-macOS.dmg"

# Code signing configuration (optional)
DEVELOPER_ID=""  # Set your Developer ID Application certificate name
TEAM_ID=""       # Set your Apple Developer Team ID
NOTARIZATION_PROFILE=""  # Set your notarytool keychain profile name

echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}    macOS Build Script - Driver Fatigue     ${NC}"
echo -e "${BLUE}    Detection System v${VERSION}            ${NC}"
echo -e "${BLUE}=============================================${NC}"

# Function to print colored status messages
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Function to check if command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "Command '$1' not found. Please install it first."
        exit 1
    fi
}

# Function to check macOS version
check_macos_version() {
    local macos_version=$(sw_vers -productVersion)
    local major_version=$(echo $macos_version | cut -d'.' -f1)
    local minor_version=$(echo $macos_version | cut -d'.' -f2)
    
    print_status "Detected macOS version: $macos_version"
    
    if [[ $major_version -lt 10 ]] || [[ $major_version -eq 10 && $minor_version -lt 14 ]]; then
        print_error "macOS 10.14 (Mojave) or later required. Current: $macos_version"
        exit 1
    fi
}

# Function to setup Python virtual environment
setup_venv() {
    print_step "Setting up Python virtual environment..."
    
    # Check Python version
    if ! python3 --version &> /dev/null; then
        print_error "Python 3 not found. Please install Python 3.8+ first."
        exit 1
    fi
    
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)
    print_status "Python version: $python_version"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv .venv
    fi
    
    # Activate virtual environment
    print_status "Activating virtual environment..."
    source .venv/bin/activate
    
    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip
    
    # Install dependencies
    print_status "Installing dependencies..."
    pip install -r requirements-build.txt
}

# Function to create .icns icon from PNG
create_icns_icon() {
    print_step "Creating .icns icon file..."
    
    local png_icon="assets/icon/app_icon.png"
    local icns_icon="assets/icon/app_icon.icns"
    
    if [ ! -f "$png_icon" ]; then
        print_warning "PNG icon not found: $png_icon"
        print_warning "Using default icon or skipping icon creation"
        return
    fi
    
    if [ -f "$icns_icon" ]; then
        print_status "ICNS icon already exists: $icns_icon"
        return
    fi
    
    # Create iconset directory
    local iconset_dir="assets/icon/app_icon.iconset"
    mkdir -p "$iconset_dir"
    
    # Generate different icon sizes
    print_status "Generating icon sizes..."
    sips -z 16 16 "$png_icon" --out "${iconset_dir}/icon_16x16.png" >/dev/null 2>&1
    sips -z 32 32 "$png_icon" --out "${iconset_dir}/icon_16x16@2x.png" >/dev/null 2>&1
    sips -z 32 32 "$png_icon" --out "${iconset_dir}/icon_32x32.png" >/dev/null 2>&1
    sips -z 64 64 "$png_icon" --out "${iconset_dir}/icon_32x32@2x.png" >/dev/null 2>&1
    sips -z 128 128 "$png_icon" --out "${iconset_dir}/icon_128x128.png" >/dev/null 2>&1
    sips -z 256 256 "$png_icon" --out "${iconset_dir}/icon_128x128@2x.png" >/dev/null 2>&1
    sips -z 256 256 "$png_icon" --out "${iconset_dir}/icon_256x256.png" >/dev/null 2>&1
    sips -z 512 512 "$png_icon" --out "${iconset_dir}/icon_256x256@2x.png" >/dev/null 2>&1
    sips -z 512 512 "$png_icon" --out "${iconset_dir}/icon_512x512.png" >/dev/null 2>&1
    sips -z 1024 1024 "$png_icon" --out "${iconset_dir}/icon_512x512@2x.png" >/dev/null 2>&1
    
    # Create .icns file
    iconutil -c icns "$iconset_dir" -o "$icns_icon"
    
    # Cleanup iconset directory
    rm -rf "$iconset_dir"
    
    print_status "ICNS icon created: $icns_icon"
}

# Function to run tests
run_tests() {
    if [ "$1" = "--skip-tests" ]; then
        print_warning "Skipping tests as requested"
        return
    fi
    
    print_step "Running tests..."
    if [ -f "tests/test_detection_rules.py" ]; then
        python -m pytest tests/ -v || {
            print_warning "Some tests failed, but continuing build..."
        }
    else
        print_warning "No test files found, skipping tests"
    fi
}

# Function to clean previous builds
clean_build() {
    print_step "Cleaning previous builds..."
    rm -rf dist/
    rm -rf build/
    rm -rf *.egg-info/
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    rm -f *.dmg
}

# Function to create entitlements.plist for code signing
create_entitlements() {
    print_step "Creating entitlements.plist..."
    
    cat > entitlements.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.camera</key>
    <true/>
    <key>com.apple.security.microphone</key>
    <true/>
    <key>com.apple.security.device.audio-input</key>
    <true/>
    <key>com.apple.security.device.camera</key>
    <true/>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
    <key>com.apple.security.automation.apple-events</key>
    <true/>
</dict>
</plist>
EOF

    print_status "Created entitlements.plist"
}

# Function to build with PyInstaller
build_app_bundle() {
    local build_mode=${1:-app}
    
    print_step "Building application with PyInstaller (mode: $build_mode)..."
    
    # Ensure spec file exists
    if [ ! -f "$SPEC_FILE" ]; then
        print_error "PyInstaller spec file not found: $SPEC_FILE"
        exit 1
    fi
    
    # Create .icns icon first
    create_icns_icon
    
    # Set macOS-specific environment variables
    export MACOSX_DEPLOYMENT_TARGET=10.14
    export ARCHFLAGS="-arch x86_64 -arch arm64"
    
    # Run PyInstaller
    python -m PyInstaller "$SPEC_FILE" --clean --noconfirm
    
    local app_path="dist/${APP_NAME}.app"
    if [ -d "$app_path" ]; then
        print_status "App bundle created: $app_path"
        
        # Set proper permissions
        find "$app_path" -type f -name "*" -exec chmod 644 {} \;
        find "$app_path" -type d -exec chmod 755 {} \;
        chmod 755 "$app_path/Contents/MacOS/$APP_NAME"
        
        # Display app bundle info
        print_status "App bundle size: $(du -sh "$app_path" | cut -f1)"
        print_status "Bundle identifier: $(defaults read "$PWD/$app_path/Contents/Info.plist" CFBundleIdentifier 2>/dev/null || echo "Not set")"
    else
        print_error "App bundle creation failed"
        exit 1
    fi
}

# Function to sign the app bundle
sign_app_bundle() {
    local app_path="dist/${APP_NAME}.app"
    
    if [ -z "$DEVELOPER_ID" ]; then
        print_warning "No Developer ID specified, skipping code signing"
        return
    fi
    
    print_step "Code signing app bundle..."
    
    # Check if certificate exists
    if ! security find-identity -v -p codesigning | grep -q "$DEVELOPER_ID"; then
        print_error "Developer ID certificate not found: $DEVELOPER_ID"
        print_warning "Available certificates:"
        security find-identity -v -p codesigning
        return
    fi
    
    # Create entitlements file
    create_entitlements
    
    # Sign all binaries in the bundle
    print_status "Signing binaries in app bundle..."
    find "$app_path" -type f \( -name "*.dylib" -o -name "*.so" \) -exec codesign --force --options runtime --sign "$DEVELOPER_ID" {} \;
    
    # Sign frameworks if any
    find "$app_path/Contents/Frameworks" -type d -name "*.framework" -exec codesign --force --options runtime --sign "$DEVELOPER_ID" {} \; 2>/dev/null || true
    
    # Sign the main app bundle
    codesign --force --options runtime --entitlements entitlements.plist --sign "$DEVELOPER_ID" "$app_path"
    
    # Verify signature
    print_status "Verifying code signature..."
    codesign --verify --deep --strict "$app_path"
    codesign --display --verbose=2 "$app_path"
    
    print_status "App bundle signed successfully"
}

# Function to create DMG installer
create_dmg() {
    print_step "Creating DMG installer..."
    
    local app_path="dist/${APP_NAME}.app"
    if [ ! -d "$app_path" ]; then
        print_error "App bundle not found: $app_path"
        exit 1
    fi
    
    # Check if create-dmg is available
    if ! command -v create-dmg &> /dev/null; then
        print_status "Installing create-dmg..."
        if command -v brew &> /dev/null; then
            brew install create-dmg
        else
            print_error "create-dmg not found and Homebrew not available"
            print_error "Please install create-dmg: brew install create-dmg"
            exit 1
        fi
    fi
    
    # Remove existing DMG
    rm -f "$DMG_NAME"
    
    # Create temporary DMG directory
    local dmg_dir="dmg_temp"
    rm -rf "$dmg_dir"
    mkdir "$dmg_dir"
    
    # Copy app to DMG directory
    cp -R "$app_path" "$dmg_dir/"
    
    # Create DMG with custom settings
    print_status "Building DMG with custom layout..."
    
    local dmg_background=""
    if [ -f "assets/dmg-background.png" ]; then
        dmg_background="--background assets/dmg-background.png"
    fi
    
    local dmg_icon=""
    if [ -f "assets/icon/app_icon.icns" ]; then
        dmg_icon="--volicon assets/icon/app_icon.icns"
    fi
    
    create-dmg \
        --volname "$APP_DISPLAY_NAME" \
        $dmg_icon \
        --window-pos 200 120 \
        --window-size 660 400 \
        --icon-size 80 \
        --icon "$APP_NAME.app" 180 170 \
        --app-drop-link 480 170 \
        --hide-extension "$APP_NAME.app" \
        --disk-image-size 500 \
        $dmg_background \
        "$DMG_NAME" \
        "$dmg_dir"
    
    # Cleanup
    rm -rf "$dmg_dir"
    
    if [ -f "$DMG_NAME" ]; then
        print_status "DMG created: $DMG_NAME"
        print_status "DMG size: $(du -sh "$DMG_NAME" | cut -f1)"
    else
        print_error "DMG creation failed"
        exit 1
    fi
}

# Function to sign DMG
sign_dmg() {
    if [ -z "$DEVELOPER_ID" ] || [ ! -f "$DMG_NAME" ]; then
        print_warning "Skipping DMG signing (no Developer ID or DMG not found)"
        return
    fi
    
    print_step "Signing DMG..."
    
    # Sign the DMG
    codesign --force --sign "$DEVELOPER_ID" "$DMG_NAME"
    
    # Verify DMG signature
    codesign --verify --verbose=2 "$DMG_NAME"
    
    print_status "DMG signed successfully"
}

# Function to notarize DMG
notarize_dmg() {
    if [ -z "$NOTARIZATION_PROFILE" ] || [ ! -f "$DMG_NAME" ]; then
        print_warning "Skipping DMG notarization (no notarization profile or DMG not found)"
        return
    fi
    
    print_step "Submitting DMG for notarization..."
    
    # Submit for notarization
    xcrun notarytool submit "$DMG_NAME" --keychain-profile "$NOTARIZATION_PROFILE" --wait
    
    # Staple notarization to DMG
    print_status "Stapling notarization to DMG..."
    xcrun stapler staple "$DMG_NAME"
    
    # Verify notarization
    xcrun stapler validate "$DMG_NAME"
    
    print_status "DMG notarized and stapled successfully"
}

# Function to create universal binary (Intel + Apple Silicon)
create_universal_binary() {
    print_step "Creating Universal Binary..."
    
    local intel_build="dist_x86_64"
    local arm_build="dist_arm64"
    local universal_build="dist_universal"
    
    # Build for Intel
    print_status "Building for Intel (x86_64)..."
    export ARCHFLAGS="-arch x86_64"
    export CMAKE_OSX_ARCHITECTURES=x86_64
    python -m PyInstaller "$SPEC_FILE" --clean --noconfirm --distpath "$intel_build"
    
    # Build for Apple Silicon
    print_status "Building for Apple Silicon (arm64)..."
    export ARCHFLAGS="-arch arm64"
    export CMAKE_OSX_ARCHITECTURES=arm64
    python -m PyInstaller "$SPEC_FILE" --clean --noconfirm --distpath "$arm_build"
    
    # Create universal binary
    print_status "Creating universal binary..."
    mkdir -p "$universal_build"
    cp -R "$intel_build/${APP_NAME}.app" "$universal_build/"
    
    local universal_app="$universal_build/${APP_NAME}.app"
    local intel_binary="$intel_build/${APP_NAME}.app/Contents/MacOS/$APP_NAME"
    local arm_binary="$arm_build/${APP_NAME}.app/Contents/MacOS/$APP_NAME"
    local universal_binary="$universal_app/Contents/MacOS/$APP_NAME"
    
    if [ -f "$intel_binary" ] && [ -f "$arm_binary" ]; then
        lipo -create "$intel_binary" "$arm_binary" -output "$universal_binary"
        
        # Verify universal binary
        print_status "Universal binary created:"
        lipo -info "$universal_binary"
        file "$universal_binary"
    else
        print_error "Failed to create universal binary - source binaries not found"
        return 1
    fi
    
    # Move universal build to main dist directory
    rm -rf dist/
    mv "$universal_build" dist/
    rm -rf "$intel_build" "$arm_build"
    
    print_status "Universal binary build completed"
}

# Function to display help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --app-only        Build only the .app bundle"
    echo "  --dmg-only        Create only DMG (requires existing .app)"
    echo "  --universal       Create Universal Binary (Intel + Apple Silicon)"
    echo "  --sign            Enable code signing (requires Developer ID)"
    echo "  --notarize        Enable notarization (requires notarization profile)"
    echo "  --skip-tests      Skip running tests"
    echo "  --clean-only      Clean build artifacts and exit"
    echo "  --help            Show this help"
    echo ""
    echo "Environment Variables:"
    echo "  DEVELOPER_ID      Developer ID Application certificate name"
    echo "  TEAM_ID           Apple Developer Team ID"
    echo "  NOTARIZATION_PROFILE  Notarytool keychain profile name"
    echo ""
    echo "Examples:"
    echo "  $0                Build .app and .dmg"
    echo "  $0 --universal    Create Universal Binary"
    echo "  $0 --sign        Build with code signing"
    echo "  $0 --sign --notarize  Build, sign, and notarize"
}

# Function to setup code signing configuration
setup_code_signing() {
    print_step "Setting up code signing configuration..."
    
    # List available certificates
    print_status "Available code signing certificates:"
    security find-identity -v -p codesigning
    
    if [ -z "$DEVELOPER_ID" ]; then
        print_warning "No DEVELOPER_ID set. To enable code signing:"
        echo "  export DEVELOPER_ID='Developer ID Application: Your Name (TEAM_ID)'"
    fi
    
    if [ -z "$NOTARIZATION_PROFILE" ]; then
        print_warning "No NOTARIZATION_PROFILE set. To enable notarization:"
        echo "  1. Create notarization profile:"
        echo "     xcrun notarytool store-credentials 'notarytool-profile' \\"
        echo "       --apple-id 'your-apple-id@example.com' \\"
        echo "       --team-id 'TEAM_ID' \\"
        echo "       --password 'app-specific-password'"
        echo "  2. Export profile:"
        echo "     export NOTARIZATION_PROFILE='notarytool-profile'"
    fi
}

# Main function
main() {
    local app_only=false
    local dmg_only=false
    local universal=false
    local enable_signing=false
    local enable_notarization=false
    local skip_tests=false
    local clean_only=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --app-only)
                app_only=true
                shift
                ;;
            --dmg-only)
                dmg_only=true
                shift
                ;;
            --universal)
                universal=true
                shift
                ;;
            --sign)
                enable_signing=true
                shift
                ;;
            --notarize)
                enable_notarization=true
                enable_signing=true  # Notarization requires signing
                shift
                ;;
            --skip-tests)
                skip_tests=true
                shift
                ;;
            --clean-only)
                clean_only=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Check if running on macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "This script must be run on macOS"
        exit 1
    fi
    
    # Check macOS version
    check_macos_version
    
    # Clean only option
    if [ "$clean_only" = true ]; then
        clean_build
        print_status "Build artifacts cleaned"
        exit 0
    fi
    
    # Setup environment
    setup_venv
    
    # DMG only option
    if [ "$dmg_only" = true ]; then
        if [ ! -d "dist/${APP_NAME}.app" ]; then
            print_error "App bundle not found. Build the app first."
            exit 1
        fi
        create_dmg
        if [ "$enable_signing" = true ]; then
            sign_dmg
        fi
        if [ "$enable_notarization" = true ]; then
            notarize_dmg
        fi
        exit 0
    fi
    
    # Run tests
    if [ "$skip_tests" = false ]; then
        run_tests
    fi
    
    # Clean and build
    clean_build
    
    if [ "$universal" = true ]; then
        create_universal_binary
    else
        build_app_bundle
    fi
    
    # Code signing
    if [ "$enable_signing" = true ]; then
        if [ -z "$DEVELOPER_ID" ]; then
            setup_code_signing
            print_error "DEVELOPER_ID not set. Code signing disabled."
        else
            sign_app_bundle
        fi
    fi
    
    # Create DMG unless app-only
    if [ "$app_only" = false ]; then
        create_dmg
        
        if [ "$enable_signing" = true ] && [ -n "$DEVELOPER_ID" ]; then
            sign_dmg
        fi
        
        if [ "$enable_notarization" = true ] && [ -n "$NOTARIZATION_PROFILE" ]; then
            notarize_dmg
        fi
    fi
    
    print_status "macOS build completed successfully!"
    
    # Show build artifacts
    echo -e "${BLUE}Build artifacts:${NC}"
    if [ -d "dist/${APP_NAME}.app" ]; then
        echo -e "  ${GREEN}App Bundle: dist/${APP_NAME}.app${NC}"
        echo -e "    Size: $(du -sh "dist/${APP_NAME}.app" | cut -f1)"
    fi
    if [ -f "$DMG_NAME" ]; then
        echo -e "  ${GREEN}DMG Installer: $DMG_NAME${NC}"
        echo -e "    Size: $(du -sh "$DMG_NAME" | cut -f1)"
    fi
    
    # Show installation instructions
    echo -e "${BLUE}Installation:${NC}"
    if [ -f "$DMG_NAME" ]; then
        echo -e "  ${YELLOW}1. Open $DMG_NAME${NC}"
        echo -e "  ${YELLOW}2. Drag $APP_NAME.app to Applications folder${NC}"
    else
        echo -e "  ${YELLOW}Copy dist/$APP_NAME.app to /Applications/${NC}"
    fi
    
    if [ "$enable_signing" = false ]; then
        echo -e "${YELLOW}Note: App is not code-signed. Users may need to bypass Gatekeeper:${NC}"
        echo -e "  ${YELLOW}Right-click app → Open → Open${NC}"
    fi
}

# Run main function with all arguments
main "$@"
