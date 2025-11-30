# Alternative OneFile Build - PYZ Error Fix
# Single executable file approach

Write-Host "🚀 OneFile Build - PYZ Error Alternative Fix" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Clean builds
Write-Host "🧹 Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

# Set OneFile mode
Write-Host "⚙️ Setting OneFile build mode..." -ForegroundColor Yellow
$env:PYINSTALLER_BUILD_MODE = "onefile"
$env:PYINSTALLER_DEBUG = "true"

Write-Host "🔨 Building single executable..." -ForegroundColor Cyan

try {
    # OneFile build with critical imports
    pyinstaller --onefile --name="DriverFatigueAlert" --icon="assets/icon/app_icon.ico" --add-data="assets;assets" --add-data="config;config" --add-data="src;src" --hidden-import="cv2" --hidden-import="mediapipe" --hidden-import="numpy" --hidden-import="PIL" --hidden-import="pygame" --hidden-import="tkinter" --hidden-import="src.app.main" --hidden-import="src.input_layer.camera_handler" --hidden-import="src.processing_layer.detect_landmark.landmark" --hidden-import="src.output_layer.ui.main_window" --console --clean launcher.py
    
    if (Test-Path "dist\DriverFatigueAlert.exe") {
        Write-Host ""
        Write-Host "✅ ONEFILE BUILD SUCCESSFUL!" -ForegroundColor Green
        
        $exeInfo = Get-Item "dist\DriverFatigueAlert.exe"
        $sizeMB = [math]::Round($exeInfo.Length / 1MB, 2)
        Write-Host "📦 Executable: $sizeMB MB" -ForegroundColor White
        
        # Test run
        Write-Host "🧪 Testing OneFile executable..." -ForegroundColor Yellow
        Start-Process -FilePath "dist\DriverFatigueAlert.exe" -PassThru
        
        Write-Host "✅ OneFile approach completed!" -ForegroundColor Green
        Write-Host "   Single executable: dist\DriverFatigueAlert.exe" -ForegroundColor Gray
        
    } else {
        Write-Host "❌ OneFile build failed!" -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ OneFile Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Reset environment
Remove-Item Env:\PYINSTALLER_DEBUG -ErrorAction SilentlyContinue
Remove-Item Env:\PYINSTALLER_BUILD_MODE -ErrorAction SilentlyContinue
