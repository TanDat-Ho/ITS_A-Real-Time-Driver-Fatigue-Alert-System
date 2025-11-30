# Fix PyInstaller PYZ Archive Error
# Safe rebuild with debug enabled

Write-Host "🔧 Fixing PyInstaller PYZ Archive Error" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Clean previous builds
Write-Host "🧹 Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") { 
    Remove-Item -Recurse -Force "build"
    Write-Host "   ✅ Removed build directory" -ForegroundColor Green
}
if (Test-Path "dist") { 
    Remove-Item -Recurse -Force "dist" 
    Write-Host "   ✅ Removed dist directory" -ForegroundColor Green
}

# Step 2: Verify dependencies
Write-Host "🔍 Checking dependencies..." -ForegroundColor Yellow
$requiredPackages = @("opencv-python", "mediapipe", "numpy", "Pillow", "pygame", "pyinstaller")
foreach ($package in $requiredPackages) {
    $result = pip show $package 2>$null
    if ($result) {
        $version = ($result | Select-String "Version:").ToString().Split(":")[1].Trim()
        Write-Host "   ✅ $package $version" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $package NOT INSTALLED" -ForegroundColor Red
        Write-Host "      Installing $package..." -ForegroundColor Yellow
        pip install $package
    }
}

# Step 3: Set debug environment
Write-Host "🐛 Enabling debug mode..." -ForegroundColor Yellow
$env:PYINSTALLER_DEBUG = "true"
$env:PYINSTALLER_BUILD_MODE = "onedir"

# Step 4: Build with enhanced error handling
Write-Host "🔨 Building with debug mode..." -ForegroundColor Cyan
Write-Host "   Using spec file: fatigue_app.spec" -ForegroundColor Gray
Write-Host "   Output: dist/DriverFatigueAlert/" -ForegroundColor Gray
Write-Host ""

try {
    # Run PyInstaller with verbose output
    pyinstaller fatigue_app.spec --clean --noconfirm --log-level=DEBUG
    
    # Check if build succeeded
    if (Test-Path "dist\DriverFatigueAlert\DriverFatigueAlert.exe") {
        Write-Host ""
        Write-Host "✅ BUILD SUCCESSFUL!" -ForegroundColor Green
        Write-Host ""
        
        # Get executable info
        $exeInfo = Get-Item "dist\DriverFatigueAlert\DriverFatigueAlert.exe"
        $sizeMB = [math]::Round($exeInfo.Length / 1MB, 2)
        Write-Host "📦 Executable Info:" -ForegroundColor White
        Write-Host "   Size: $sizeMB MB" -ForegroundColor Gray
        Write-Host "   Path: $($exeInfo.FullName)" -ForegroundColor Gray
        Write-Host ""
        
        # Test run with error capture
        Write-Host "🧪 Testing application..." -ForegroundColor Yellow
        Write-Host "   Opening debug console window..." -ForegroundColor Gray
        
        # Start with error capture
        $testResult = Start-Process -FilePath "dist\DriverFatigueAlert\DriverFatigueAlert.exe" -PassThru -WindowStyle Normal
        
        if ($testResult) {
            Write-Host "✅ Application started successfully!" -ForegroundColor Green
            Write-Host "   PID: $($testResult.Id)" -ForegroundColor Gray
            Write-Host ""
            Write-Host "🎯 If PYZ error is fixed, you should see the app interface." -ForegroundColor Cyan
            Write-Host "   If still errors, check the console window for details." -ForegroundColor Gray
        }
        
    } else {
        Write-Host ""
        Write-Host "❌ BUILD FAILED!" -ForegroundColor Red
        Write-Host "   Executable not found in dist/DriverFatigueAlert/" -ForegroundColor Red
        
        # Check for build logs
        if (Test-Path "build\fatigue_app\warn-fatigue_app.txt") {
            Write-Host ""
            Write-Host "⚠️ Build Warnings:" -ForegroundColor Yellow
            Get-Content "build\fatigue_app\warn-fatigue_app.txt" | Select-Object -First 10
        }
    }
    
} catch {
    Write-Host ""
    Write-Host "❌ PYINSTALLER ERROR:" -ForegroundColor Red
    Write-Host "   $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔧 Try Alternative Fix:" -ForegroundColor Yellow
    Write-Host "   Run: pip install --upgrade pyinstaller" -ForegroundColor Gray
    Write-Host "   Or:  pip uninstall pyinstaller && pip install pyinstaller==5.13.2" -ForegroundColor Gray
}

Write-Host ""
Write-Host "📋 Next Steps if Still Error:" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "1. Check console output for specific error details" -ForegroundColor Gray
Write-Host "2. Try OneFile build: .\fix-pyz-onefile.ps1" -ForegroundColor Gray  
Write-Host "3. Update dependencies: pip install --upgrade opencv-python mediapipe" -ForegroundColor Gray
Write-Host "4. Check file permissions and antivirus software" -ForegroundColor Gray
Write-Host ""

# Reset environment
Remove-Item Env:\PYINSTALLER_DEBUG -ErrorAction SilentlyContinue
Remove-Item Env:\PYINSTALLER_BUILD_MODE -ErrorAction SilentlyContinue
