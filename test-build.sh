#!/bin/bash
# test-build.sh - Test script for build system validation
# Tests both Linux and macOS build scripts

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[TEST]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

test_prerequisites() {
    print_status "Testing build prerequisites..."
    
    # Test Python
    if python3 --version; then
        print_status "✓ Python 3 available"
    else
        print_error "✗ Python 3 not found"
        return 1
    fi
    
    # Test pip
    if python3 -m pip --version; then
        print_status "✓ pip available"
    else
        print_error "✗ pip not found"
        return 1
    fi
    
    # Test required files
    local required_files=(
        "launcher.py"
        "fatigue_app.spec"
        "requirements-build.txt"
        "assets/icon/app_icon.png"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            print_status "✓ Required file: $file"
        else
            print_error "✗ Missing required file: $file"
            return 1
        fi
    done
}

test_linux_build() {
    print_status "Testing Linux build script..."
    
    if [ ! -f "build-linux.sh" ]; then
        print_error "build-linux.sh not found"
        return 1
    fi
    
    # Make executable
    chmod +x build-linux.sh
    
    # Test help option
    if ./build-linux.sh --help; then
        print_status "✓ Linux build script help works"
    else
        print_error "✗ Linux build script help failed"
        return 1
    fi
    
    # Test dry run (if supported)
    print_status "Linux build script is executable and help works"
}

test_macos_build() {
    print_status "Testing macOS build script..."
    
    if [ ! -f "build-macos.sh" ]; then
        print_error "build-macos.sh not found"
        return 1
    fi
    
    # Make executable
    chmod +x build-macos.sh
    
    # Test help option
    if ./build-macos.sh --help; then
        print_status "✓ macOS build script help works"
    else
        print_error "✗ macOS build script help failed"
        return 1
    fi
    
    print_status "macOS build script is executable and help works"
}

test_spec_file() {
    print_status "Testing PyInstaller spec file..."
    
    if [ ! -f "fatigue_app.spec" ]; then
        print_error "fatigue_app.spec not found"
        return 1
    fi
    
    # Basic syntax check
    if python3 -c "
import ast
with open('fatigue_app.spec', 'r') as f:
    content = f.read()
try:
    # Try to parse as Python (spec files are Python scripts)
    ast.parse(content)
    print('✓ Spec file syntax is valid')
except SyntaxError as e:
    print(f'✗ Spec file syntax error: {e}')
    exit(1)
"; then
        print_status "✓ PyInstaller spec file syntax is valid"
    else
        print_error "✗ PyInstaller spec file has syntax errors"
        return 1
    fi
}

test_desktop_files() {
    print_status "Testing desktop entry files..."
    
    if [ -f "assets/fatigue-detection.desktop" ]; then
        if command -v desktop-file-validate &> /dev/null; then
            if desktop-file-validate "assets/fatigue-detection.desktop"; then
                print_status "✓ Desktop entry file is valid"
            else
                print_warning "⚠ Desktop entry file has validation warnings"
            fi
        else
            print_status "✓ Desktop entry file exists (desktop-file-validate not available)"
        fi
    else
        print_warning "⚠ Desktop entry file not found"
    fi
}

test_icon_files() {
    print_status "Testing icon files..."
    
    local icon_files=(
        "assets/icon/app_icon.png"
        "assets/icon/app_icon.ico"
        "assets/icon/app_icon.icns"
    )
    
    for icon in "${icon_files[@]}"; do
        if [ -f "$icon" ]; then
            print_status "✓ Icon file exists: $icon"
            
            # Test if it's a valid image (if file command available)
            if command -v file &> /dev/null; then
                local file_type=$(file "$icon")
                if [[ "$file_type" == *"image"* ]] || [[ "$file_type" == *"icon"* ]]; then
                    print_status "  ✓ Valid image format"
                else
                    print_warning "  ⚠ May not be a valid image: $file_type"
                fi
            fi
        else
            if [[ "$icon" == *".png" ]]; then
                print_error "✗ Required icon missing: $icon"
                return 1
            else
                print_warning "⚠ Optional icon missing: $icon"
            fi
        fi
    done
}

test_dependencies() {
    print_status "Testing Python dependencies..."
    
    if [ -f "requirements-build.txt" ]; then
        # Create temporary virtual environment for testing
        local temp_venv=".test_venv"
        python3 -m venv "$temp_venv"
        source "$temp_venv/bin/activate"
        
        if pip install -r requirements-build.txt; then
            print_status "✓ All dependencies can be installed"
            
            # Test critical imports
            local critical_modules=(
                "PyInstaller"
                "cv2"
                "mediapipe"
                "numpy"
            )
            
            for module in "${critical_modules[@]}"; do
                if python3 -c "import $module; print(f'✓ {module} import successful')"; then
                    print_status "  ✓ $module import successful"
                else
                    print_error "  ✗ $module import failed"
                    deactivate
                    rm -rf "$temp_venv"
                    return 1
                fi
            done
            
            deactivate
        else
            print_error "✗ Failed to install dependencies"
            deactivate
            rm -rf "$temp_venv"
            return 1
        fi
        
        # Cleanup
        rm -rf "$temp_venv"
    else
        print_error "✗ requirements-build.txt not found"
        return 1
    fi
}

test_project_structure() {
    print_status "Testing project structure..."
    
    local required_dirs=(
        "src"
        "assets"
        "docs"
        "tests"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            print_status "✓ Required directory: $dir"
        else
            print_error "✗ Missing required directory: $dir"
            return 1
        fi
    done
    
    # Test if main entry point exists
    if [ -f "launcher.py" ]; then
        if python3 -c "
import ast
with open('launcher.py', 'r') as f:
    content = f.read()
try:
    ast.parse(content)
    print('✓ launcher.py syntax is valid')
except SyntaxError as e:
    print(f'✗ launcher.py syntax error: {e}')
    exit(1)
"; then
            print_status "✓ Main entry point (launcher.py) is valid"
        else
            print_error "✗ Main entry point has syntax errors"
            return 1
        fi
    else
        print_error "✗ Main entry point (launcher.py) not found"
        return 1
    fi
}

run_platform_specific_tests() {
    print_status "Running platform-specific tests..."
    
    case "$OSTYPE" in
        linux-gnu*)
            print_status "Platform: Linux"
            test_linux_build
            
            # Test Linux-specific dependencies
            if command -v dpkg-deb &> /dev/null; then
                print_status "✓ dpkg-deb available for DEB packaging"
            else
                print_warning "⚠ dpkg-deb not available (DEB packaging will be skipped)"
            fi
            
            if command -v rpmbuild &> /dev/null; then
                print_status "✓ rpmbuild available for RPM packaging"
            else
                print_warning "⚠ rpmbuild not available (RPM packaging will be skipped)"
            fi
            ;;
            
        darwin*)
            print_status "Platform: macOS"
            test_macos_build
            
            # Test macOS-specific dependencies
            if command -v create-dmg &> /dev/null; then
                print_status "✓ create-dmg available for DMG creation"
            else
                print_warning "⚠ create-dmg not available (install with: brew install create-dmg)"
            fi
            
            if command -v codesign &> /dev/null; then
                print_status "✓ codesign available for app signing"
            else
                print_warning "⚠ codesign not available"
            fi
            ;;
            
        msys*|cygwin*|mingw*)
            print_status "Platform: Windows (using bash)"
            print_warning "⚠ Use PowerShell script for Windows builds: build-windows.ps1"
            ;;
            
        *)
            print_warning "⚠ Unknown platform: $OSTYPE"
            ;;
    esac
}

generate_test_report() {
    print_status "Generating test report..."
    
    local report_file="build-test-report.txt"
    
    cat > "$report_file" << EOF
Build System Test Report
========================
Generated: $(date)
Platform: $OSTYPE
Python: $(python3 --version 2>&1)

Test Results:
EOF
    
    # Re-run tests and capture results
    {
        echo "Prerequisites Test:"
        if test_prerequisites; then
            echo "  ✓ PASSED"
        else
            echo "  ✗ FAILED"
        fi
        
        echo "Project Structure Test:"
        if test_project_structure; then
            echo "  ✓ PASSED"
        else
            echo "  ✗ FAILED"
        fi
        
        echo "Spec File Test:"
        if test_spec_file; then
            echo "  ✓ PASSED"
        else
            echo "  ✗ FAILED"
        fi
        
        echo "Desktop Files Test:"
        if test_desktop_files; then
            echo "  ✓ PASSED"
        else
            echo "  ✗ FAILED"
        fi
        
        echo "Icon Files Test:"
        if test_icon_files; then
            echo "  ✓ PASSED"
        else
            echo "  ✗ FAILED"
        fi
    } >> "$report_file" 2>&1
    
    print_status "Test report saved to: $report_file"
}

main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Build System Test Suite              ${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    local test_failed=false
    
    # Run all tests
    if ! test_prerequisites; then
        test_failed=true
    fi
    
    if ! test_project_structure; then
        test_failed=true
    fi
    
    if ! test_spec_file; then
        test_failed=true
    fi
    
    test_desktop_files  # Non-critical
    test_icon_files     # Non-critical for basic functionality
    
    run_platform_specific_tests  # Platform-specific tests
    
    # Test dependencies last (requires network)
    if [ "${1:-}" != "--skip-deps" ]; then
        print_status "Testing dependencies (use --skip-deps to skip)..."
        if ! test_dependencies; then
            test_failed=true
        fi
    else
        print_warning "Skipping dependency test as requested"
    fi
    
    # Generate report
    generate_test_report
    
    echo -e "${BLUE}========================================${NC}"
    if [ "$test_failed" = true ]; then
        print_error "Some tests failed! Check the issues above."
        exit 1
    else
        print_status "All critical tests passed! Build system is ready."
        echo -e "${GREEN}✓ Build system validation successful${NC}"
    fi
    echo -e "${BLUE}========================================${NC}"
}

# Show help
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    echo "Build System Test Suite"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --skip-deps   Skip dependency installation test"
    echo "  --help        Show this help"
    echo ""
    echo "This script tests the build system components:"
    echo "  - Prerequisites (Python, pip, required files)"
    echo "  - Project structure"
    echo "  - PyInstaller spec file"
    echo "  - Desktop entry files"
    echo "  - Icon files"
    echo "  - Platform-specific build scripts"
    echo "  - Python dependencies"
    exit 0
fi

main "$@"
