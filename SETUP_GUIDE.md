# 🚀 Hướng dẫn cài đặt Driver Fatigue Detection System

## 📋 Yêu cầu hệ thống
- **Python**: 3.8 → 3.11 (bắt buộc cho mediapipe)
- **OS**: Windows 10/11, macOS, Linux
- **RAM**: Tối thiểu 4GB, khuyến nghị 8GB+
- **Camera**: Webcam hoặc camera USB

## 🔧 Cài đặt từng bước

### 1️⃣ Kiểm tra và cài đặt Python

#### Kiểm tra version hiện tại:
```bash
python --version
# Hoặc
py --version
```

#### Nếu không có Python hoặc sai version:
📥 **Tải Python 3.11**: https://www.python.org/downloads/release/python-3118/
- Chọn: `Windows installer (64-bit)` 
- ⚠️ **Quan trọng**: Tick ☑️ "Add Python 3.11 to PATH" khi cài đặt

#### Kiểm tra lại sau khi cài:
```bash
py -3.11 --version
```

### 2️⃣ Tạo môi trường ảo (Virtual Environment)

```bash
# Tạo môi trường ảo
py -3.11 -m venv .venv

# Kích hoạt môi trường (Windows)
.venv\Scripts\activate

# Kích hoạt môi trường (Git Bash)
source .venv/Scripts/activate

# Kích hoạt môi trường (macOS/Linux)  
source .venv/bin/activate
```

✅ **Thành công**: Dòng lệnh sẽ có `(.venv)` ở đầu

### 3️⃣ Cài đặt dependencies

#### Cài đặt production (người dùng):
```bash
pip install -r requirements.txt
```

#### Cài đặt development (developer):
```bash  
pip install -r requirements-dev.txt
```

### 4️⃣ Cài đặt VS Code (khuyến nghị)

#### Tự động chọn Python interpreter:
1. Mở project trong VS Code
2. `Ctrl + Shift + P` 
3. Gõ: "Python: Select Interpreter"
4. Chọn: `.venv\Scripts\python.exe`

## 🎮 Chạy ứng dụng

### Từ source code:
```bash
# Kích hoạt môi trường trước
.venv\Scripts\activate

# Chạy ứng dụng
python src/main.py
```

### Từ executable (Windows):
```bash
# Chạy file .exe đã build
.\dist\DriverFatigueAlert\DriverFatigueAlert.exe

# Hoặc cài đặt từ installer
.\dist\DriverFatigueSetup-1.0.0.exe
```

## 🛠️ Build ứng dụng

### Windows build:
```bash
.\build-windows.ps1 -Clean -Verbose
.\build-installer-windows.ps1
```

### All platforms:
```bash
.\build-all.ps1 -Platform all -Installer
```

## ❌ Tắt môi trường ảo
```bash
deactivate
```

## 🔧 Khắc phục sự cố

### Lỗi mediapipe:
- Đảm bảo Python version 3.8-3.11
- Cài lại: `pip uninstall mediapipe && pip install mediapipe==0.10.14`

### Lỗi opencv:
```bash
pip uninstall opencv-python
pip install opencv-python>=4.8.0
```

### Lỗi permission (Windows):
- Chạy PowerShell as Administrator
- Hoặc: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### Lỗi camera không detect:
- Kiểm tra quyền truy cập camera
- Thử camera index khác (0, 1, 2...)
- Restart ứng dụng

## 📦 Dependencies chính

| Package | Version | Mục đích |
|---------|---------|----------|
| opencv-python | ≥4.8.0 | Xử lý video/ảnh |
| mediapipe | 0.10.14 | AI face detection |
| numpy | ≥1.21.0 | Tính toán ma trận |
| pygame | ≥2.1.0 | Âm thanh cảnh báo |
| pillow | ≥9.0.0 | Xử lý ảnh |
| imutils | ≥0.5.4 | OpenCV utilities |
| pynput | ≥1.7.6 | Input handling |

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra Python version: `python --version`
2. Kiểm tra môi trường ảo: có `(.venv)` không?
3. Cài lại dependencies: `pip install -r requirements.txt --force-reinstall`
4. Xem logs lỗi trong `log/` folder

---
📅 **Cập nhật**: November 29, 2025  
🔧 **Tương thích**: Python 3.8-3.11, Windows/macOS/Linux
