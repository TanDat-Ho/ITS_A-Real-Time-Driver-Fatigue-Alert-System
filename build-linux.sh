#!/bin/bash
# build-linux.sh - Cross-platform build script for Linux and macOS
# Driver Fatigue Detection System - PyInstaller Build Script

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="FatigueDetectionApp"
VERSION="1.0.0"
BUILD_DIR="dist"
ASSETS_DIR="assets"
SPEC_FILE="fatigue_app.spec"

# Platform detection
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
    DMG_NAME="${APP_NAME}-${VERSION}-macOS.dmg"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="linux"
    APPIMAGE_NAME="${APP_NAME}-${VERSION}-x86_64.AppImage"
else
    echo -e "${RED}Error: Unsupported platform: $OSTYPE${NC}"
    exit 1
fi

echo -e "${BLUE}===========================================${NC}"
echo -e "${BLUE}  Driver Fatigue Detection System Build  ${NC}"
echo -e "${BLUE}  Platform: $PLATFORM${NC}"
echo -e "${BLUE}  Version: $VERSION${NC}"
echo -e "${BLUE}===========================================${NC}"

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

# Function to check if command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "Command '$1' not found. Please install it first."
        exit 1
    fi
}

# Function to create desktop entry file
create_desktop_entry() {
    local desktop_file="$1"
    print_status "Creating desktop entry: $desktop_file"
    
    cat > "$desktop_file" << 'EOF'
[Desktop Entry]
Type=Application
Version=1.0
Name=Driver Fatigue Detection
GenericName=Fatigue Detection System
Comment=Real-time driver fatigue detection system using computer vision
Exec=FatigueDetectionApp
TryExec=FatigueDetectionApp
Icon=fatigue-detection
Terminal=false
Categories=Utility;Science;AudioVideo;Security;
Keywords=fatigue;driver;detection;safety;monitoring;camera;vision;
StartupNotify=true
StartupWMClass=FatigueDetectionApp
MimeType=application/x-fatigue-data;
Actions=Configure;About;

[Desktop Action Configure]
Name=Configure Settings
Comment=Open application settings
Exec=FatigueDetectionApp --configure

[Desktop Action About]
Name=About
Comment=About Driver Fatigue Detection
Exec=FatigueDetectionApp --about
EOF
}

# Function to create app icons in multiple sizes
create_app_icons() {
    local appdir="$1"
    local base_icon="assets/icon/app_icon.png"
    
    if [ ! -f "$base_icon" ]; then
        print_warning "Base icon not found: $base_icon"
        return
    fi
    
    print_status "Creating app icons in multiple sizes..."
    
    # Define icon sizes
    local sizes=(16 24 32 48 64 96 128 256 512)
    
    for size in "${sizes[@]}"; do
        local icon_dir="$appdir/usr/share/icons/hicolor/${size}x${size}/apps"
        mkdir -p "$icon_dir"
        
        # Use ImageMagick convert if available, otherwise use cp for 256x256
        if command -v convert &> /dev/null; then
            convert "$base_icon" -resize ${size}x${size} "$icon_dir/fatigue-detection.png"
        elif [ "$size" = "256" ]; then
            cp "$base_icon" "$icon_dir/fatigue-detection.png"
        fi
    done
    
    # Create symbolic link for app name
    ln -sf "fatigue-detection.png" "$appdir/usr/share/icons/hicolor/256x256/apps/FatigueDetectionApp.png"
}

# Function to create metainfo file for AppImage
create_metainfo_file() {
    local metainfo_file="$1"
    print_status "Creating metainfo file: $metainfo_file"
    
    cat > "$metainfo_file" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>com.fatiguedetection.App</id>
  <metadata_license>MIT</metadata_license>
  <project_license>MIT</project_license>
  <name>Driver Fatigue Detection</name>
  <summary>Real-time driver fatigue detection system</summary>
  <description>
    <p>
      A comprehensive system for detecting driver fatigue using computer vision
      and machine learning techniques. The application monitors eye movements,
      head pose, and other fatigue indicators to alert drivers in real-time.
    </p>
    <p>Features:</p>
    <ul>
      <li>Real-time fatigue detection using webcam</li>
      <li>Eye monitoring with EAR (Eye Aspect Ratio) algorithm</li>
      <li>Yawn detection using MAR (Mouth Aspect Ratio) algorithm</li>
      <li>Head pose estimation for distraction detection</li>
      <li>Multi-level alert system</li>
      <li>Performance metrics and logging</li>
    </ul>
  </description>
  <launchable type="desktop-id">fatigue-detection.desktop</launchable>
  <screenshots>
    <screenshot type="default">
      <caption>Main application interface</caption>
    </screenshot>
  </screenshots>
  <url type="homepage">https://github.com/yourorg/driver-fatigue-detection</url>
  <url type="bugtracker">https://github.com/yourorg/driver-fatigue-detection/issues</url>
  <url type="help">https://github.com/yourorg/driver-fatigue-detection/wiki</url>
  <developer_name>Driver Fatigue Detection Team</developer_name>
  <categories>
    <category>Utility</category>
    <category>Science</category>
    <category>AudioVideo</category>
  </categories>
  <keywords>
    <keyword>fatigue</keyword>
    <keyword>driver</keyword>
    <keyword>detection</keyword>
    <keyword>safety</keyword>
    <keyword>monitoring</keyword>
    <keyword>camera</keyword>
    <keyword>vision</keyword>
  </keywords>
  <provides>
    <binary>FatigueDetectionApp</binary>
  </provides>
  <releases>
    <release version="1.0.0" date="2025-11-29">
      <description>
        <p>Initial release with core fatigue detection features</p>
      </description>
    </release>
  </releases>
  <content_rating type="oars-1.1"/>
</component>
EOF
}

# Function to create MIME type file
create_mime_file() {
    local mime_file="$1"
    print_status "Creating MIME type file: $mime_file"
    
    cat > "$mime_file" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="application/x-fatigue-data">
    <comment>Fatigue Detection Data File</comment>
    <comment xml:lang="en">Fatigue Detection Data File</comment>
    <icon name="fatigue-detection"/>
    <glob-deleteall/>
    <glob pattern="*.fatigue"/>
    <glob pattern="*.fdata"/>
    <magic priority="50">
      <match value="FATIGUE" type="string" offset="0"/>
    </magic>
  </mime-type>
</mime-info>
EOF
}

# Function to setup Python virtual environment
setup_venv() {
    print_status "Setting up Python virtual environment..."
    
    # Check Python version
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)
    if [[ $(echo "$python_version >= 3.8" | bc -l) -eq 0 ]]; then
        print_error "Python 3.8+ required. Found: $python_version"
        exit 1
    fi
    
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

# Function to run tests
run_tests() {
    if [ "$1" = "--skip-tests" ]; then
        print_warning "Skipping tests as requested"
        return
    fi
    
    print_status "Running tests..."
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
    print_status "Cleaning previous builds..."
    rm -rf dist/
    rm -rf build/
    rm -rf *.egg-info/
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
}

# Function to build with PyInstaller
build_pyinstaller() {
    local build_mode=${1:-onefile}
    
    print_status "Building application with PyInstaller (mode: $build_mode)..."
    
    # Ensure spec file exists
    if [ ! -f "$SPEC_FILE" ]; then
        print_error "PyInstaller spec file not found: $SPEC_FILE"
        exit 1
    fi
    
    # Modify spec file for build mode
    if [ "$build_mode" = "onedir" ]; then
        sed -i.bak 's/onefile=True/onefile=False/' "$SPEC_FILE"
    else
        sed -i.bak 's/onefile=False/onefile=True/' "$SPEC_FILE"
    fi
    
    # Run PyInstaller
    python -m PyInstaller "$SPEC_FILE" --clean --noconfirm
    
    # Restore original spec file
    if [ -f "${SPEC_FILE}.bak" ]; then
        mv "${SPEC_FILE}.bak" "$SPEC_FILE"
    fi
    
    print_status "PyInstaller build completed"
}

# Function to create macOS DMG
create_macos_dmg() {
    if [ "$PLATFORM" != "macos" ]; then
        return
    fi
    
    print_status "Creating macOS DMG installer..."
    
    # Check for required tools
    check_command "hdiutil"
    check_command "create-dmg"
    
    local app_path="dist/${APP_NAME}.app"
    if [ ! -d "$app_path" ]; then
        print_error "Application bundle not found: $app_path"
        exit 1
    fi
    
    # Create DMG
    create-dmg \
        --volname "$APP_NAME" \
        --volicon "assets/icon/app_icon.icns" \
        --window-pos 200 120 \
        --window-size 600 300 \
        --icon-size 100 \
        --icon "$APP_NAME.app" 175 120 \
        --hide-extension "$APP_NAME.app" \
        --app-drop-link 425 120 \
        "$DMG_NAME" \
        "$app_path"
    
    print_status "DMG created: $DMG_NAME"
}

# Function to create Linux AppImage
create_linux_appimage() {
    if [ "$PLATFORM" != "linux" ]; then
        return
    fi
    
    print_status "Creating Linux AppImage..."
    
    # Check if linuxdeploy is available
    if ! command -v linuxdeploy &> /dev/null; then
        print_status "Downloading linuxdeploy..."
        wget -O linuxdeploy https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
        chmod +x linuxdeploy
    fi
    
    # Create AppDir structure
    local appdir="${APP_NAME}.AppDir"
    rm -rf "$appdir"
    mkdir -p "$appdir/usr/bin"
    mkdir -p "$appdir/usr/share/applications"
    mkdir -p "$appdir/usr/share/icons/hicolor/256x256/apps"
    mkdir -p "$appdir/usr/share/metainfo"
    mkdir -p "$appdir/usr/share/mime/packages"
    
    # Copy executable
    cp "dist/$APP_NAME" "$appdir/usr/bin/"
    chmod +x "$appdir/usr/bin/$APP_NAME"
    
    # Create desktop file
    create_desktop_entry "$appdir/usr/share/applications/fatigue-detection.desktop"
    
    # Copy icon in multiple sizes
    create_app_icons "$appdir"
    
    # Create AppRun script
    cat > "$appdir/AppRun" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
export APPDIR="$(pwd)"
export PATH="$APPDIR/usr/bin:$PATH"
export LD_LIBRARY_PATH="$APPDIR/usr/lib:$LD_LIBRARY_PATH"
exec "$APPDIR/usr/bin/FatigueDetectionApp" "$@"
EOF
    chmod +x "$appdir/AppRun"
    
    # Create .DirIcon
    if [ -f "assets/icon/app_icon.png" ]; then
        cp "assets/icon/app_icon.png" "$appdir/.DirIcon"
    fi
    
    # Create metainfo file
    create_metainfo_file "$appdir/usr/share/metainfo/com.fatiguedetection.App.metainfo.xml"
    
    # Create MIME type file
    create_mime_file "$appdir/usr/share/mime/packages/fatigue-detection.xml"
    
    # Create AppImage using linuxdeploy
    print_status "Building AppImage with linuxdeploy..."
    ./linuxdeploy --appdir "$appdir" --output appimage
    
    # Rename to standard format
    if ls ${APP_NAME}-*.AppImage &> /dev/null; then
        mv ${APP_NAME}-*.AppImage "$APPIMAGE_NAME" 2>/dev/null || true
    fi
    
    # Set executable permissions
    if [ -f "$APPIMAGE_NAME" ]; then
        chmod +x "$APPIMAGE_NAME"
        print_status "AppImage created: $APPIMAGE_NAME"
        print_status "AppImage size: $(du -sh "$APPIMAGE_NAME" | cut -f1)"
    else
        print_error "AppImage creation failed"
        return 1
    fi
}

# Function to create Linux DEB package
create_linux_deb() {
    if [ "$PLATFORM" != "linux" ]; then
        return
    fi
    
    print_status "Creating DEB package..."
    
    local package_name="driver-fatigue-detection"
    local deb_dir="${package_name}_${VERSION}_amd64"
    
    # Create package structure
    rm -rf "$deb_dir"
    mkdir -p "$deb_dir/DEBIAN"
    mkdir -p "$deb_dir/usr/bin"
    mkdir -p "$deb_dir/usr/share/applications"
    mkdir -p "$deb_dir/usr/share/icons/hicolor/256x256/apps"
    mkdir -p "$deb_dir/usr/share/doc/$package_name"
    
    # Copy executable
    cp "dist/$APP_NAME" "$deb_dir/usr/bin/"
    
    # Create control file
    cat > "$deb_dir/DEBIAN/control" << EOF
Package: $package_name
Version: $VERSION
Section: utils
Priority: optional
Architecture: amd64
Depends: python3 (>= 3.8), python3-tk, libgtk-3-0, libgstreamer1.0-0
Maintainer: Driver Fatigue Detection Team <team@example.com>
Homepage: https://github.com/yourorg/driver-fatigue-detection
Description: Real-time driver fatigue detection system
 A comprehensive system for detecting driver fatigue using computer vision
 and machine learning techniques. The application monitors eye movements,
 head pose, and other fatigue indicators to alert drivers in real-time.
 .
 Features include:
  * Real-time fatigue detection using webcam
  * Eye monitoring with EAR (Eye Aspect Ratio) algorithm
  * Yawn detection using MAR (Mouth Aspect Ratio) algorithm
  * Head pose estimation for distraction detection
  * Multi-level alert system
  * Performance metrics and logging
EOF

    # Create postinst script
    cat > "$deb_dir/DEBIAN/postinst" << 'EOF'
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
# Update MIME database
if command -v update-mime-database >/dev/null; then
    update-mime-database /usr/share/mime
fi
EOF
    chmod +x "$deb_dir/DEBIAN/postinst"

    # Create prerm script
    cat > "$deb_dir/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e
# Stop any running instances
pkill -f FatigueDetectionApp || true
EOF
    chmod +x "$deb_dir/DEBIAN/prerm"

    # Copy files
    cp "dist/$APP_NAME" "$deb_dir/usr/bin/"
    chmod +x "$deb_dir/usr/bin/$APP_NAME"
    
    # Create app icons
    create_app_icons "$deb_dir"
    
    # Copy documentation
    cp README.md "$deb_dir/usr/share/doc/$package_name/" 2>/dev/null || true
    echo "Driver Fatigue Detection System v${VERSION}" > "$deb_dir/usr/share/doc/$package_name/README"
    
    # Create desktop file
    create_desktop_entry "$deb_dir/usr/share/applications/fatigue-detection.desktop"
    
    # Create MIME type file
    mkdir -p "$deb_dir/usr/share/mime/packages"
    create_mime_file "$deb_dir/usr/share/mime/packages/fatigue-detection.xml"
    
    # Create menu file for older systems
    mkdir -p "$deb_dir/usr/share/menu"
    cat > "$deb_dir/usr/share/menu/$package_name" << EOF
?package($package_name):command="/usr/bin/$APP_NAME" \\
    icon="/usr/share/icons/hicolor/256x256/apps/fatigue-detection.png" \\
    needs="X11" \\
    section="Applications/Science" \\
    title="Driver Fatigue Detection" \\
    description="Real-time driver fatigue detection system"
EOF
[Desktop Entry]
Type=Application
Name=Driver Fatigue Detection
Comment=Real-time driver fatigue detection system
Exec=$APP_NAME
Icon=$APP_NAME
Categories=Utility;Science;
Terminal=false
EOF
    
    # Copy icon
    cp "assets/icon/app_icon.png" "$deb_dir/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
    
    # Copy documentation
    cp README.md "$deb_dir/usr/share/doc/$package_name/"
    
    # Build DEB package
    dpkg-deb --build "$deb_dir"
    
    print_status "DEB package created: ${deb_dir}.deb"
}

# Main build function
main() {
    local build_mode="onefile"
    local skip_tests=false
    local package_only=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --onedir)
                build_mode="onedir"
                shift
                ;;
            --onefile)
                build_mode="onefile"
                shift
                ;;
            --skip-tests)
                skip_tests=true
                shift
                ;;
            --package-only)
                package_only=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --onefile     Build as single executable (default)"
                echo "  --onedir      Build as directory with dependencies"
                echo "  --skip-tests  Skip running tests"
                echo "  --package-only Skip PyInstaller build, only create packages"
                echo "  --help        Show this help"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Setup environment
    setup_venv
    
    if [ "$package_only" = false ]; then
        # Run tests
        run_tests $skip_tests
        
        # Clean and build
        clean_build
        build_pyinstaller "$build_mode"
    fi
    
    # Create platform-specific packages
    if [ "$PLATFORM" = "macos" ]; then
        create_macos_dmg
    elif [ "$PLATFORM" = "linux" ]; then
        create_linux_appimage
        create_linux_deb
    fi
    
    print_status "Build completed successfully!"
    
    # Show build artifacts
    echo -e "${BLUE}Build artifacts:${NC}"
    ls -la dist/ || true
    if [ "$PLATFORM" = "macos" ] && [ -f "$DMG_NAME" ]; then
        echo -e "  ${GREEN}macOS DMG: $DMG_NAME${NC}"
    fi
    if [ "$PLATFORM" = "linux" ]; then
        [ -f "$APPIMAGE_NAME" ] && echo -e "  ${GREEN}Linux AppImage: $APPIMAGE_NAME${NC}"
        ls -la *.deb 2>/dev/null && echo -e "  ${GREEN}Linux DEB packages:${NC}" && ls *.deb
    fi
}

# Run main function with all arguments
main "$@"
