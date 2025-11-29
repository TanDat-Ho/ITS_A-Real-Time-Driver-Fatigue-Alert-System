# Windows Installer Build Script using NSIS
# This script creates a Windows installer after PyInstaller build

param(
    [switch]$Clean,
    [switch]$Verbose
)

# Configuration
$APP_NAME = "Driver Fatigue Detection System"
$APP_VERSION = "1.0.0"
$NSIS_PATH = "${env:ProgramFiles(x86)}\NSIS\makensis.exe"
$INSTALLER_SCRIPT = "installer\windows\installer.nsi"
$BUILD_DIR = "dist"
$INSTALLER_OUTPUT = "$BUILD_DIR\DriverFatigueSetup-$APP_VERSION.exe"

# Colors for output
$RED = "Red"
$GREEN = "Green"
$YELLOW = "Yellow"
$BLUE = "Cyan"

function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $BLUE
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $GREEN
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $YELLOW
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $RED
}

# Header
Write-Host "===============================================" -ForegroundColor $BLUE
Write-Host "   Windows Installer Build Script" -ForegroundColor $BLUE
Write-Host "   $APP_NAME v$APP_VERSION" -ForegroundColor $BLUE
Write-Host "===============================================" -ForegroundColor $BLUE
Write-Host ""

# Check if NSIS is installed
if (-not (Test-Path $NSIS_PATH)) {
    Write-Error "NSIS not found at: $NSIS_PATH"
    Write-Error "Please install NSIS from https://nsis.sourceforge.io/"
    Write-Error ""
    Write-Error "Quick install options:"
    Write-Error "  winget install NSIS.NSIS"
    Write-Error "  choco install nsis"
    Write-Error "  scoop install nsis"
    exit 1
}

# Check NSIS version
try {
    $nsisVersion = & $NSIS_PATH /VERSION
    Write-Success "NSIS found: $nsisVersion"
} catch {
    Write-Error "Failed to get NSIS version"
    exit 1
}

# Check if PyInstaller build exists
if (-not (Test-Path "$BUILD_DIR\DriverFatigueAlert\DriverFatigueAlert.exe")) {
    Write-Error "PyInstaller build not found at: $BUILD_DIR\DriverFatigueAlert\DriverFatigueAlert.exe"
    Write-Error "Please run build-windows.ps1 first to create the executable"
    exit 1
}

Write-Success "PyInstaller build found"

# Get executable size
$exeSize = (Get-Item "$BUILD_DIR\DriverFatigueAlert\DriverFatigueAlert.exe").Length
$exeSizeMB = [math]::Round($exeSize / 1MB, 2)
Write-Status "Executable size: $exeSizeMB MB"

# Clean previous installer if requested
if ($Clean -and (Test-Path $INSTALLER_OUTPUT)) {
    Remove-Item $INSTALLER_OUTPUT -Force
    Write-Status "Removed previous installer"
}

# Check if installer script exists
if (-not (Test-Path $INSTALLER_SCRIPT)) {
    Write-Error "NSIS script not found: $INSTALLER_SCRIPT"
    exit 1
}

Write-Status "Using NSIS script: $INSTALLER_SCRIPT"

# Create installer directory if needed
$installerDir = Split-Path $INSTALLER_SCRIPT -Parent
if (-not (Test-Path $installerDir)) {
    New-Item -ItemType Directory -Path $installerDir -Force | Out-Null
    Write-Status "Created installer directory: $installerDir"
}

# Build the installer
Write-Status "Building Windows installer..."
Write-Status "This may take a few minutes..."

$startTime = Get-Date

try {
    Push-Location $installerDir
    
    $nsisArgs = @()
    if ($Verbose) {
        $nsisArgs += "/V3"
    } else {
        $nsisArgs += "/V1"
    }
    $nsisArgs += "installer.nsi"
    
    $process = Start-Process -FilePath $NSIS_PATH -ArgumentList $nsisArgs -Wait -PassThru -NoNewWindow
    
    if ($process.ExitCode -eq 0) {
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        
        Write-Success "Windows installer created successfully in $([math]::Round($duration, 1)) seconds!"
        
        # Check if installer was created and get its size
        if (Test-Path "..\..\$INSTALLER_OUTPUT") {
            $installerSize = (Get-Item "..\..\$INSTALLER_OUTPUT").Length
            $installerSizeMB = [math]::Round($installerSize / 1MB, 2)
            
            Write-Status "Installer location: $INSTALLER_OUTPUT"
            Write-Status "Installer size: $installerSizeMB MB"
              # Calculate compression ratio
            $originalSize = (Get-ChildItem "..\..\$BUILD_DIR\DriverFatigueAlert" -Recurse | Measure-Object -Property Length -Sum).Sum
            $originalSizeMB = [math]::Round($originalSize / 1MB, 2)
            $compressionRatio = [math]::Round(($installerSize / $originalSize) * 100, 1)
            
            Write-Status "Original app size: $originalSizeMB MB"
            Write-Status "Compression ratio: $compressionRatio%"
        } else {
            Write-Warning "Installer file not found at expected location"
        }
    } else {
        Write-Error "NSIS build failed with exit code: $($process.ExitCode)"
        exit 1
    }
} catch {
    Write-Error "Failed to build installer: $($_.Exception.Message)"
    exit 1
} finally {
    Pop-Location
}

# Test installer (optional)
if (Test-Path $INSTALLER_OUTPUT) {
    Write-Host ""
    Write-Host "===============================================" -ForegroundColor $GREEN
    Write-Host "   Build Summary" -ForegroundColor $GREEN
    Write-Host "===============================================" -ForegroundColor $GREEN
    Write-Host "Application: $BUILD_DIR\DriverFatigueAlert\DriverFatigueAlert.exe ($exeSizeMB MB)" -ForegroundColor $GREEN
    Write-Host "Installer: $INSTALLER_OUTPUT ($installerSizeMB MB)" -ForegroundColor $GREEN
    Write-Host ""
    Write-Status "To test the installer:"
    Write-Host "  .\$INSTALLER_OUTPUT" -ForegroundColor $YELLOW
    Write-Host ""
    Write-Status "To sign the installer (optional):"
    Write-Host '  signtool sign /f "certificate.pfx" /p "password" /t "http://timestamp.digicert.com" "' + $INSTALLER_OUTPUT + '"' -ForegroundColor $YELLOW
} else {
    Write-Error "Installer creation failed - file not found"
    exit 1
}

Write-Success "Windows installer build completed successfully!"
