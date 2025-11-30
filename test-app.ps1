# Test Application for PYZ Error Fix
Write-Host "🧪 Testing Driver Fatigue Alert Application" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

$exePath = "dist\DriverFatigueAlert\DriverFatigueAlert.exe"

if (-not (Test-Path $exePath)) {
    Write-Host "❌ Executable not found: $exePath" -ForegroundColor Red
    exit 1
}

# Get executable info
$exe = Get-Item $exePath
$sizeMB = [math]::Round($exe.Length / 1MB, 2)
Write-Host "📦 Executable Info:" -ForegroundColor White
Write-Host "   Size: $sizeMB MB" -ForegroundColor Gray
Write-Host "   Path: $($exe.FullName)" -ForegroundColor Gray
Write-Host "   Created: $($exe.CreationTime)" -ForegroundColor Gray
Write-Host ""

# Test basic functionality
Write-Host "🚀 Starting application test..." -ForegroundColor Yellow
Write-Host "   - Console window will open" -ForegroundColor Gray
Write-Host "   - Check for any error messages" -ForegroundColor Gray
Write-Host "   - Application should start without PYZ error" -ForegroundColor Gray
Write-Host ""

try {
    # Start with error capture
    $processInfo = New-Object System.Diagnostics.ProcessStartInfo
    $processInfo.FileName = $exePath
    $processInfo.UseShellExecute = $false
    $processInfo.RedirectStandardOutput = $true
    $processInfo.RedirectStandardError = $true
    $processInfo.CreateNoWindow = $false
    $processInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Normal
    
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $processInfo
    
    Write-Host "⏳ Launching application..." -ForegroundColor Yellow
    $started = $process.Start()
    
    if ($started) {
        Write-Host "✅ Application started successfully!" -ForegroundColor Green
        Write-Host "   PID: $($process.Id)" -ForegroundColor Gray
        
        # Wait a moment to capture any immediate errors
        Start-Sleep -Seconds 3
        
        if (-not $process.HasExited) {
            Write-Host "✅ Application is running normally" -ForegroundColor Green
            Write-Host "   No PYZ archive error detected!" -ForegroundColor Green
            Write-Host ""
            Write-Host "🎉 SUCCESS: PYZ error has been fixed!" -ForegroundColor Green
            Write-Host ""
            Write-Host "📋 What to check now:" -ForegroundColor Cyan
            Write-Host "   1. Test all application features" -ForegroundColor Gray
            Write-Host "   2. Test camera functionality" -ForegroundColor Gray
            Write-Host "   3. Test fatigue detection" -ForegroundColor Gray
            Write-Host "   4. Test alert system" -ForegroundColor Gray
            
            # Let user interact with the app
            Write-Host ""
            Write-Host "Press any key to close this test..." -ForegroundColor Yellow
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            
        } else {
            Write-Host "❌ Application exited immediately" -ForegroundColor Red
            $stderr = $process.StandardError.ReadToEnd()
            $stdout = $process.StandardOutput.ReadToEnd()
            
            if ($stderr) {
                Write-Host "Error Output:" -ForegroundColor Red
                Write-Host $stderr -ForegroundColor Red
            }
            if ($stdout) {
                Write-Host "Standard Output:" -ForegroundColor Yellow
                Write-Host $stdout -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "❌ Failed to start application" -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ Test Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   This might indicate remaining issues" -ForegroundColor Red
}

Write-Host ""
Write-Host "📊 Test Summary:" -ForegroundColor Cyan
Write-Host "================" -ForegroundColor Cyan

if (Test-Path "dist\DriverFatigueAlert") {
    $files = Get-ChildItem "dist\DriverFatigueAlert" | Measure-Object
    $totalSize = (Get-ChildItem "dist\DriverFatigueAlert" -Recurse | Measure-Object -Property Length -Sum).Sum
    $totalSizeMB = [math]::Round($totalSize / 1MB, 2)
    
    Write-Host "📁 Distribution folder: $($files.Count) files" -ForegroundColor White
    Write-Host "📦 Total size: $totalSizeMB MB" -ForegroundColor White
}

Write-Host ""
Write-Host "🔧 If you still see errors:" -ForegroundColor Yellow
Write-Host "   1. Try OneFile build: .\fix-pyz-onefile.ps1" -ForegroundColor Gray
Write-Host "   2. Check Windows Defender/Antivirus settings" -ForegroundColor Gray
Write-Host "   3. Run as Administrator" -ForegroundColor Gray
Write-Host "   4. Update PyInstaller: pip install --upgrade pyinstaller" -ForegroundColor Gray
Write-Host ""
