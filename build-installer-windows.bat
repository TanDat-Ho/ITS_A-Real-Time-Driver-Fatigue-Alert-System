@echo off
REM Windows NSIS Installer Build Script
REM This script creates a Windows installer using NSIS

setlocal enabledelayedexpansion

REM Configuration
set APP_NAME=Driver Fatigue Detection System
set APP_VERSION=1.0.0
set NSIS_SCRIPT=installer\windows\installer.nsi

echo ===============================================
echo   Windows Installer Build Script
echo   %APP_NAME% v%APP_VERSION%
echo ===============================================
echo.

REM Check if NSIS is installed
where makensis >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] NSIS not found in PATH
    echo Please install NSIS from https://nsis.sourceforge.io/
    echo Or ensure makensis.exe is in your PATH
    echo.
    echo Quick install with Chocolatey:
    echo   choco install nsis
    echo.
    echo Quick install with Scoop:
    echo   scoop install nsis
    pause
    exit /b 1
)

echo [INFO] NSIS found, checking version...
makensis /VERSION
echo.

REM Check if PyInstaller build exists
if not exist "dist\DriverFatigueAlert\DriverFatigueAlert.exe" (
    echo [ERROR] PyInstaller build not found
    echo Please run build-windows.ps1 first to create the executable
    pause
    exit /b 1
)

echo [INFO] PyInstaller build found
echo.

REM Create installer directory if it doesn't exist
if not exist "installer\windows" (
    mkdir installer\windows
    echo [INFO] Created installer\windows directory
)

REM Check if NSIS script exists
if not exist "%NSIS_SCRIPT%" (
    echo [ERROR] NSIS script not found: %NSIS_SCRIPT%
    echo Please ensure the installer.nsi file exists
    pause
    exit /b 1
)

echo [INFO] Building Windows installer...
echo [INFO] Using script: %NSIS_SCRIPT%
echo.

REM Build the installer
cd installer\windows
makensis installer.nsi

if !errorlevel! equ 0 (
    echo.
    echo [SUCCESS] Windows installer created successfully!
    echo.
    
    REM Check if installer was created
    if exist "..\..\dist\DriverFatigueSetup-!APP_VERSION!.exe" (
        echo [INFO] Installer location: dist\DriverFatigueSetup-!APP_VERSION!.exe
        
        REM Get installer size
        for %%A in ("..\..\dist\DriverFatigueSetup-!APP_VERSION!.exe") do (
            set size=%%~zA
            set /a size_mb=!size!/1024/1024
            echo [INFO] Installer size: !size_mb! MB
        )
    ) else (
        echo [WARNING] Installer file not found at expected location
    )
) else (
    echo.
    echo [ERROR] Installer build failed!
    pause
    exit /b 1
)

cd ..\..

echo.
echo ===============================================
echo   Build Summary
echo ===============================================
echo Application: dist\DriverFatigueAlert\DriverFatigueAlert.exe
echo Installer: dist\DriverFatigueSetup-!APP_VERSION!.exe
echo.
echo To test the installer:
echo   .\dist\DriverFatigueSetup-!APP_VERSION!.exe
echo.
pause
