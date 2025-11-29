# PowerShell Build Script for Driver Fatigue Alert System
# Version: 1.0.0
# Author: ITS Project Team

param(
    [ValidateSet("onefile", "onedir")]
    [string]$BuildMode = "onedir",
    
    [switch]$Debug = $false,
    [switch]$Clean = $true,
    [switch]$CreateInstaller = $false,
    [switch]$SkipTests = $false,
    [string]$Version = ""
)

# Color functions
function Write-Info($message) {
    Write-Host "[INFO] $message" -ForegroundColor Cyan
}

function Write-Success($message) {
    Write-Host "[SUCCESS] $message" -ForegroundColor Green
}

function Write-Warning($message) {
    Write-Host "[WARNING] $message" -ForegroundColor Yellow
}

function Write-Error($message) {
    Write-Host "[ERROR] $message" -ForegroundColor Red
}

function Write-Step($message) {
    Write-Host ""
    Write-Host "[STEP] $message" -ForegroundColor Blue
    Write-Host "=" * 50 -ForegroundColor Blue
}

# Main header
Write-Host ""
Write-Host "Driver Fatigue Alert System - PyInstaller Build" -ForegroundColor Magenta
Write-Host "=" * 60 -ForegroundColor Magenta
Write-Host ""

# Generate version if not provided
if (-not $Version) {
    $timestamp = Get-Date -Format "yyyy.MM.dd"
    $buildNumber = Get-Date -Format "HHmm"
    $Version = "$timestamp.$buildNumber"
}

Write-Info "Build Configuration:"
Write-Host "   Mode: $BuildMode"
Write-Host "   Debug: $Debug"
Write-Host "   Version: $Version"
Write-Host "   Create Installer: $CreateInstaller"
Write-Host ""

# Check Python installation
Write-Step "Checking Python Installation"
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Python not found" }
    Write-Success "Python found: $pythonVersion"
} catch {
    Write-Error "Python not found. Please install Python 3.8+ and add to PATH."
    Write-Info "Download from: https://python.org/downloads/"
    exit 1
}

# Check virtual environment
if ($env:VIRTUAL_ENV) {
    Write-Success "Virtual environment active: $env:VIRTUAL_ENV"
} else {
    Write-Warning "No virtual environment detected. Proceeding with global Python..."
}

# Install/check dependencies
Write-Step "Installing Dependencies"
try {
    Write-Info "Installing PyInstaller..."
    pip install pyinstaller --quiet --upgrade
    
    Write-Info "Installing project dependencies..."
    pip install -r requirements-pip.txt --quiet
    
    Write-Success "Dependencies installed successfully"
} catch {
    Write-Error "Failed to install dependencies: $($_.Exception.Message)"
    exit 1
}

# Run tests (unless skipped)
if (-not $SkipTests) {
    Write-Step "Running Tests"
    try {
        if (Test-Path "tests") {
            Write-Info "Running pytest..."
            python -m pytest tests/ -v --tb=short
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "Some tests failed, but continuing build..."
            } else {
                Write-Success "All tests passed"
            }
        } else {
            Write-Warning "No tests directory found, skipping tests"
        }
    } catch {
        Write-Warning "Test execution failed: $($_.Exception.Message)"
    }
}

# Clean previous builds
if ($Clean) {
    Write-Step "Cleaning Previous Builds"
    $foldersToClean = @("build", "dist", "__pycache__")
    
    foreach ($folder in $foldersToClean) {
        if (Test-Path $folder) {
            Write-Info "Removing $folder..."
            Remove-Item -Recurse -Force $folder
        }
    }
    
    # Clean Python cache
    Get-ChildItem -Recurse -Name "__pycache__" | Remove-Item -Recurse -Force
    Get-ChildItem -Recurse -Name "*.pyc" | Remove-Item -Force
    
    Write-Success "Build directories cleaned"
}

# Create necessary directories
Write-Step "Creating Build Environment"
$directories = @("output/snapshots", "output/screenshots", "output/reports", "log")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Info "Created directory: $dir"
    }
}

# Set environment variables for PyInstaller
$env:PYINSTALLER_BUILD_MODE = $BuildMode
$env:PYINSTALLER_DEBUG = if ($Debug) { "true" } else { "false" }
$env:FATIGUE_APP_VERSION = $Version

# Build with PyInstaller
Write-Step "Building Executable with PyInstaller"
try {
    Write-Info "Starting PyInstaller build..."
    Write-Info "Mode: $BuildMode"
    Write-Info "Debug: $Debug"
    
    $buildArgs = @(
        "fatigue_app.spec",
        "--clean",
        "--noconfirm",
        "--log-level=INFO"
    )
    
    if ($Debug) {
        $buildArgs += "--debug=all"
    }
    
    $startTime = Get-Date
    & pyinstaller @buildArgs
    $buildTime = (Get-Date) - $startTime
    
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller build failed with exit code $LASTEXITCODE"
    }
    
    Write-Success "Build completed in $($buildTime.TotalSeconds) seconds"
} catch {
    Write-Error "Build failed: $($_.Exception.Message)"
    exit 1
}

# Verify build output
Write-Step "Verifying Build Output"
if ($BuildMode -eq "onefile") {
    $exePath = "dist\DriverFatigueAlert.exe"
    $distSize = (Get-Item "dist\DriverFatigueAlert.exe").Length / 1MB
} else {
    $exePath = "dist\DriverFatigueAlert\DriverFatigueAlert.exe"
    $distSize = (Get-ChildItem "dist\DriverFatigueAlert" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
}

if (Test-Path $exePath) {
    Write-Success "Executable created: $exePath"
    Write-Info "Distribution size: $([math]::Round($distSize, 2)) MB"
} else {
    Write-Error "Executable not found at expected location: $exePath"
    exit 1
}

# Copy config to AppData for first run
Write-Step "Setting up Configuration"
try {
    $appDataPath = "$env:APPDATA\DriverFatigueAlert"
    if (-not (Test-Path $appDataPath)) {
        New-Item -ItemType Directory -Path $appDataPath -Force | Out-Null
        Write-Info "Created AppData directory: $appDataPath"
    }
    
    # Copy default config files
    if (Test-Path "config") {
        Copy-Item "config\*" $appDataPath -Force
        Write-Success "Configuration files copied to AppData"
    }
} catch {
    Write-Warning "Failed to setup AppData configuration: $($_.Exception.Message)"
}

# Create version info file
Write-Step "Creating Version Information"
try {
    $versionInfo = @{
        version = $Version
        buildMode = $BuildMode
        buildDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        pythonVersion = (python --version 2>&1)
        platform = "Windows"
        debug = $Debug
    } | ConvertTo-Json -Depth 2
    
    $versionPath = if ($BuildMode -eq "onefile") { "dist" } else { "dist\DriverFatigueAlert" }
    $versionInfo | Out-File "$versionPath\version.json" -Encoding UTF8
    
    Write-Success "Version information saved"
} catch {
    Write-Warning "Failed to create version info: $($_.Exception.Message)"
}

# Create installer (if requested)
if ($CreateInstaller) {
    Write-Step "Creating Windows Installer"
    
    # Check if NSIS is installed
    $nsisPath = Get-Command makensis -ErrorAction SilentlyContinue
    if ($nsisPath) {
        try {
            Write-Info "Creating NSIS installer..."
            & makensis installer\setup.nsi
            
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Installer created successfully"
            } else {
                Write-Error "Installer creation failed"
            }
        } catch {
            Write-Error "Failed to create installer: $($_.Exception.Message)"
        }
    } else {
        Write-Warning "NSIS not found. Download from: https://nsis.sourceforge.io/"
        Write-Info "Installer creation skipped"
    }
}

# Build summary
Write-Step "Build Summary"
Write-Success "Build completed successfully!"
Write-Host ""
Write-Info "Build Details:"
Write-Host "   Version: $Version"
Write-Host "   Mode: $BuildMode"
Write-Host "   Executable: $exePath"
Write-Host "   Size: $([math]::Round($distSize, 2)) MB"
Write-Host ""
Write-Info "Next Steps:"
Write-Host "   1. Test the executable: $exePath"
Write-Host "   2. Run installer (if created)"
Write-Host "   3. Deploy to target machines"
Write-Host ""

# Performance tips
Write-Info "Performance Tips:"
Write-Host "   • Use --onedir for faster startup time"
Write-Host "   • Use --onefile for easy distribution"
Write-Host "   • Add --debug for troubleshooting"
Write-Host ""

Write-Success "Build script completed successfully!"
