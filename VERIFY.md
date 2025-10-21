# ✅ Danh Sách Kiểm Tra Cài Đặt

Sử dụng danh sách này để đảm bảo cài đặt thành công.

## 📋 Trước Khi Cài Đặt

- [ ] Kiểm tra Python version (3.8-3.11)
  ```bash
  python --version
  # hoặc
  python3 --version
  ```
  
- [ ] Có camera/webcam hoạt động
  ```bash
  # Test trên Linux/Mac
  ls /dev/video*
  ```

- [ ] Có ít nhất 4GB RAM

- [ ] Kết nối internet để tải dependencies

## 🔧 Cài Đặt

- [ ] Clone repository thành công
  ```bash
  git clone https://github.com/TanDat-Ho/ITS_A-Real-Time-Driver-Fatigue-Alert-System.git
  cd ITS_A-Real-Time-Driver-Fatigue-Alert-System
  ```

- [ ] Tạo môi trường ảo thành công
  ```bash
  python3.11 -m venv .venv
  ```

- [ ] Kích hoạt môi trường ảo
  ```bash
  source .venv/bin/activate  # Linux/Mac
  # hoặc
  .venv\Scripts\activate     # Windows
  ```
  Kiểm tra: Có `(.venv)` ở đầu prompt

- [ ] Cài đặt dependencies thành công
  ```bash
  pip install -r requirements.txt
  ```
  Không có lỗi "ERROR" trong output

- [ ] Tạo thư mục cần thiết
  ```bash
  python run.py --setup
  ```

## ✅ Kiểm Tra Hoạt Động

- [ ] Xem thông tin cấu hình
  ```bash
  python run.py --info
  ```
  Không có lỗi import

- [ ] Test import modules
  ```bash
  python -c "import cv2; import mediapipe; import numpy; print('✅ All imports OK')"
  ```

- [ ] Kiểm tra camera
  ```bash
  python -c "import cv2; cap = cv2.VideoCapture(0); ret, _ = cap.read(); print('✅ Camera OK' if ret else '❌ Camera failed'); cap.release()"
  ```

## 🚀 Chạy Ứng Dụng

- [ ] Chạy lần đầu với cấu hình mặc định
  ```bash
  python run.py
  ```
  Nhấn Enter khi được yêu cầu

- [ ] Kiểm tra các phím tắt
  - [ ] `p` - Hiển thị thống kê
  - [ ] `r` - Reset
  - [ ] `s` - Chụp màn hình
  - [ ] `q` - Thoát

- [ ] Kiểm tra các chế độ
  - [ ] `python run.py --config sensitive`
  - [ ] `python run.py --config conservative`

## 📊 Kiểm Tra Hiệu Suất

Chạy ứng dụng và nhấn `p` để xem thống kê:

- [ ] Capture FPS > 20
- [ ] Processing FPS > 15
- [ ] Avg Time < 100ms
- [ ] Detection Rate > 80%
- [ ] Dropped frames < 50

## 🐛 Nếu Có Vấn Đề

### Camera không hoạt động
- [ ] Kiểm tra camera có hoạt động trong ứng dụng khác
- [ ] Thử thay đổi camera index trong config
- [ ] Kiểm tra quyền truy cập camera

### FPS thấp
- [ ] Giảm độ phân giải trong config
- [ ] Đóng các ứng dụng khác
- [ ] Kiểm tra CPU/RAM usage

### Import errors
- [ ] Kiểm tra môi trường ảo đã kích hoạt
- [ ] Cài lại dependencies
- [ ] Kiểm tra Python version

## 📝 Ghi Chú

Sau khi hoàn thành tất cả các bước:

**Ngày kiểm tra**: _______________

**Python version**: _______________

**Hệ điều hành**: _______________

**Vấn đề gặp phải**: _______________

**Giải pháp**: _______________

---

✅ **Hoàn thành tất cả? Chúc mừng! Bạn đã cài đặt thành công!**

📚 Đọc thêm:
- [README.md](README.md) - Tài liệu đầy đủ
- [docs/USAGE.md](docs/USAGE.md) - Hướng dẫn sử dụng
- [QUICKSTART.md](QUICKSTART.md) - Tham khảo nhanh
