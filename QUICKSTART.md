# 🚀 Hướng Dẫn Cài Đặt Nhanh

## TL;DR - Cài Đặt Nhanh (5 phút)

```bash
# 1. Clone repository
git clone https://github.com/TanDat-Ho/ITS_A-Real-Time-Driver-Fatigue-Alert-System.git
cd ITS_A-Real-Time-Driver-Fatigue-Alert-System

# 2. Tạo và kích hoạt môi trường ảo (Python 3.8-3.11)
python3.11 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# hoặc
.venv\Scripts\activate     # Windows

# 3. Cài đặt thư viện
pip install -r requirements.txt

# 4. Chạy ứng dụng
python run.py
```

## ⚡ Các Lệnh Chính

### Khởi Động Ứng Dụng

```bash
# Chạy với cấu hình mặc định
python run.py

# Chạy với chế độ nhạy (phát hiện sớm hơn)
python run.py --config sensitive

# Chạy với chế độ bảo thủ (ít false positive)
python run.py --config conservative

# Xem thông tin cấu hình
python run.py --info

# Tạo thư mục cần thiết
python run.py --setup
```

### Phím Tắt Trong Ứng Dụng

- `q` - Thoát ứng dụng
- `r` - Reset thống kê
- `s` - Chụp ảnh màn hình
- `p` - Hiển thị thống kê chi tiết
- `Ctrl+C` - Thoát khẩn cấp

## 📋 Yêu Cầu Hệ Thống

- **Python**: 3.8 - 3.11 (bắt buộc)
- **Camera**: Webcam hoặc camera USB
- **RAM**: Tối thiểu 4GB
- **CPU**: Tối thiểu Intel Core i3

## 🐛 Xử Lý Lỗi Thường Gặp

### Lỗi Camera
```bash
# Thử thay đổi camera index trong src/app/config.py
CAMERA_CONFIG = {"src": 1}  # Thử 0, 1, 2...
```

### Lỗi Mediapipe
```bash
pip uninstall mediapipe
pip install mediapipe==0.10.14
```

### Lỗi Python Version
```bash
# Xóa môi trường cũ và tạo lại với Python 3.11
rm -rf .venv
python3.11 -m venv .venv
```

## 📚 Tài Liệu Đầy Đủ

Xem [README.md](README.md) để biết thêm chi tiết về:
- Kiến trúc hệ thống
- Cấu hình nâng cao
- Hiểu về các chỉ số (EAR, MAR, Head Pose)
- Troubleshooting chi tiết

## 🎯 Bắt Đầu Ngay

1. Đảm bảo có Python 3.8-3.11
2. Clone repository
3. Chạy `pip install -r requirements.txt`
4. Chạy `python run.py`
5. Nhấn Enter để bắt đầu

**Chúc bạn sử dụng thành công! 🚗💨**
