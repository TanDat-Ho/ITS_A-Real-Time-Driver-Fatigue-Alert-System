# 🚗 ITS_A - Hệ Thống Phát Hiện Mệt Mỏi Tài Xế Thời Gian Thực

## 📋 Giới Thiệu

Hệ thống phát hiện mệt mỏi và buồn ngủ của tài xế theo thời gian thực sử dụng:

- **EAR (Eye Aspect Ratio)**: Phát hiện mắt nhắm/chớp mắt
- **MAR (Mouth Aspect Ratio)**: Phát hiện ngáp
- **Head Pose**: Phát hiện cúi đầu/nghiêng đầu

### ✨ Tính Năng Chính

- ✅ Phát hiện mệt mỏi theo thời gian thực qua webcam
- ✅ Phát hiện nhiều trạng thái: mắt nhắm, ngáp, cúi đầu
- ✅ Hệ thống cảnh báo đa cấp độ (NONE → LOW → MEDIUM → HIGH → CRITICAL)
- ✅ Giao diện hiển thị trực quan với thông số chi tiết
- ✅ Hiệu suất cao với kiến trúc đa luồng (multi-threaded)
- ✅ Ghi log và thống kê chi tiết
- ✅ Hỗ trợ nhiều chế độ cấu hình (mặc định, nhạy, bảo thủ)

### 🚀 Tính Năng Nâng Cao (Enhanced Mode)

- 🎯 **Input Optimization**: Hardware-adaptive configuration, quality validation
- 📊 **Performance Monitoring**: Real-time FPS, processing time, quality metrics
- 🔧 **Smart Configuration**: Auto-detect CPU/memory và optimize settings
- ✨ **Enhanced Detection**: Improved MediaPipe parameters, input validation
- 📈 **Quality Assessment**: Frame brightness/contrast/blur analysis
- 🛠️ **Robust Error Handling**: Better camera management, graceful degradation

### 🏗️ Kiến Trúc Hệ Thống

```
│
├── 📁 assets/              ← Tài nguyên (âm thanh, icon)
│   ├── icon/
│   └── sounds/
│
├── 📁 src/
│   ├── 📁 input_layer/     ← Lớp thu nhận dữ liệu
│   │   └── camera_handler.py    # Mở webcam, đọc frame, resize
│   │
│   ├── 📁 processing_layer/     ← Lớp xử lý & phân tích
│   │   ├── detect_landmark/
│   │   │   └── landmark.py      # Phát hiện 468 điểm khuôn mặt
│   │   ├── detect_rules/
│   │   │   ├── ear.py          # Tính toán Eye Aspect Ratio
│   │   │   ├── mar.py          # Tính toán Mouth Aspect Ratio
│   │   │   └── head_pose.py    # Tính toán góc đầu
│   │   └── vision_processor/
│   │       └── rule_based.py   # Logic phát hiện mệt mỏi
│   │
│   ├── 📁 output_layer/         ← Lớp phản hồi & cảnh báo
│   │   ├── alert_module.py     # Cảnh báo âm thanh, UI
│   │   └── logger.py           # Ghi log
│   │
│   └── 📁 app/
│       ├── main.py             # Pipeline tổng thể
│       └── config.py           # Cấu hình thông số
│
├── 📁 tests/                   ← Unit tests
│   └── test_detection_rules.py
│
├── 📄 requirements.txt
├── 📄 README.md
└── 📄 run.py                   ← Entry point chính
```

## 🔧 Yêu Cầu Hệ Thống

### Phần Cứng

- **Camera/Webcam**: Độ phân giải tối thiểu 640x480, khuyến nghị 720p trở lên
- **CPU**: Tối thiểu Intel Core i3 hoặc tương đương
- **RAM**: Tối thiểu 4GB, khuyến nghị 8GB trở lên

### Phần Mềm

- **Hệ điều hành**: Windows 10/11, macOS 10.15+, hoặc Linux (Ubuntu 20.04+)
- **Python**: Phiên bản 3.8 đến 3.11 (bắt buộc vì Mediapipe không hỗ trợ các phiên bản khác)

## 📦 Cài Đặt

### Bước 1: Kiểm Tra Python

Kiểm tra phiên bản Python hiện tại:

```bash
python --version
# hoặc
python3 --version
```

⚠️ **Lưu ý quan trọng**: Mediapipe chỉ hỗ trợ Python 3.8 - 3.11. Nếu bạn có phiên bản khác, cần cài đặt lại.

#### Cài Đặt Python 3.11 (Khuyến nghị)

**Windows:**

1. Tải Python 3.11.8 từ: https://www.python.org/downloads/release/python-3118/
2. Chọn: `Windows installer (64-bit)` (file tên: python-3.11.8-amd64.exe)
3. Khi cài đặt, **nhớ tick**: ✅ "Add Python 3.11 to PATH"
4. Kiểm tra cài đặt:
   ```bash
   py -3.11 --version
   ```

**macOS:**

```bash
brew install python@3.11
```

**Linux (Ubuntu/Debian):**

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

### Bước 2: Clone Repository

```bash
git clone https://github.com/TanDat-Ho/ITS_A-Real-Time-Driver-Fatigue-Alert-System.git
cd ITS_A-Real-Time-Driver-Fatigue-Alert-System
```

### Bước 3: Tạo Môi Trường Ảo

**Windows:**

```bash
# Với Python 3.11
py -3.11 -m venv .venv

# Kích hoạt môi trường ảo
.venv\Scripts\activate

# Hoặc với Git Bash
source .venv/Scripts/activate
```

**macOS/Linux:**

```bash
# Tạo môi trường ảo
python3.11 -m venv .venv

# Kích hoạt môi trường ảo
source .venv/bin/activate
```

✅ Khi thành công, bạn sẽ thấy `(.venv)` xuất hiện ở đầu dòng lệnh.

**Tự động kích hoạt trong VS Code (Khuyến nghị):**

1. Nhấn `Ctrl + Shift + P` (Windows/Linux) hoặc `Cmd + Shift + P` (macOS)
2. Chọn "Python: Select Interpreter"
3. Chọn môi trường ảo `.venv` vừa tạo

### Bước 4: Cài Đặt Thư Viện

```bash
# Cài đặt tất cả các thư viện cần thiết
pip install -r requirements.txt
```

Hoặc cài đặt thủ công từng thư viện:

```bash
# 1. OpenCV - Xử lý ảnh và video
pip install opencv-python

# 2. Mediapipe - Phát hiện khuôn mặt (468 landmarks)
pip install mediapipe==0.10.14

# 3. NumPy - Xử lý ma trận, tính toán
pip install numpy

# 4. Imutils - Hỗ trợ xử lý ảnh
pip install imutils
```

### Bước 5: Tạo Thư Mục Cần Thiết

```bash
python run.py --setup
```

Lệnh này sẽ tự động tạo các thư mục:

- `log/` - Lưu log hệ thống
- `assets/sounds/` - Âm thanh cảnh báo
- `assets/icon/` - Icon ứng dụng
- `output/snapshots/` - Ảnh chụp màn hình

## 🚀 Chạy Ứng Dụng

### 🎯 Launcher Chính (Khuyến Nghị)

```bash
# GUI Mode với Enhanced features mặc định
python launcher.py

# CLI Mode với Enhanced input optimization
python launcher.py --enhanced

# Test input system trước khi chạy
python launcher.py --test-input

# Enhanced mode với config khác nhau
python launcher.py --config sensitive --enhanced
```

### 📟 Legacy Mode

```bash
# Chạy trực tiếp (legacy)
python run.py

# Với cấu hình mặc định
python run.py --config default
```

### Chạy Với Các Chế Độ Khác Nhau

#### 1. Chế Độ Nhạy (Sensitive) - Phát hiện sớm hơn

```bash
python run.py --config sensitive
```

Đặc điểm:

- Ngưỡng thời gian ngắn hơn
- Phát hiện mệt mỏi nhanh hơn
- Có thể có nhiều false positive hơn

#### 2. Chế Độ Bảo Thủ (Conservative) - Ít cảnh báo sai

```bash
python run.py --config conservative
```

Đặc điểm:

- Ngưỡng thời gian dài hơn
- Giảm false positive
- Chỉ cảnh báo khi chắc chắn mệt mỏi

### Xem Thông Tin Cấu Hình

```bash
python run.py --info
```

Lệnh này sẽ hiển thị:

- Các ngưỡng EAR, MAR, Head Pose
- Thời gian duration cho mỗi chế độ
- Hướng dẫn sử dụng

## 🎮 Hướng Dẫn Sử Dụng

### Phím Tắt Trong Ứng Dụng

| Phím     | Chức Năng                    |
| -------- | ---------------------------- |
| `q`      | Thoát ứng dụng               |
| `r`      | Reset thống kê và trạng thái |
| `s`      | Chụp ảnh màn hình hiện tại   |
| `p`      | Hiển thị thống kê chi tiết   |
| `Ctrl+C` | Thoát khẩn cấp               |

### Giao Diện Hiển Thị

#### Khu Vực Trên Cùng (Bên Trái)

- **Status**: Trạng thái cảnh báo hiện tại
- **Confidence**: Độ tin cậy (0.0 - 1.0)
- **EAR**: Giá trị Eye Aspect Ratio và trạng thái
- **MAR**: Giá trị Mouth Aspect Ratio và trạng thái
- **Pitch**: Góc nghiêng đầu và trạng thái

#### Khu Vực Dưới Cùng (Bên Trái)

- **Capture FPS**: Tốc độ đọc camera
- **Process FPS**: Tốc độ xử lý
- **Avg Time**: Thời gian xử lý trung bình
- **Dropped**: Số frame bị bỏ qua

#### Khu Vực Trên Cùng (Bên Phải)

- **Faces**: Số khuôn mặt phát hiện / Tổng số frame
- **Alerts**: Tổng số cảnh báo

#### Khu Vực Dưới Cùng (Giữa)

- Hiển thị đề xuất hành động dựa trên mức độ cảnh báo

### Cấp Độ Cảnh Báo

| Cấp Độ       | Màu Sắc    | Ý Nghĩa   | Hành Động               |
| ------------ | ---------- | --------- | ----------------------- |
| **NONE**     | 🟢 Xanh lá | Tỉnh táo  | Tiếp tục lái xe an toàn |
| **LOW**      | 🟡 Vàng    | Hơi mệt   | Chú ý tập trung         |
| **MEDIUM**   | 🟠 Cam     | Mệt vừa   | Cân nhắc nghỉ ngơi      |
| **HIGH**     | 🔴 Đỏ      | Mệt nhiều | Cần nghỉ ngơi ngay      |
| **CRITICAL** | 🟣 Tím     | Nguy hiểm | **DỪNG XE NGAY**        |

## ⚙️ Cấu Hình Nâng Cao

### Tùy Chỉnh Thông Số

Chỉnh sửa file `src/app/config.py`:

```python
# ===== EAR (Eye Aspect Ratio) CONFIGURATION =====
EAR_CONFIG = {
    "blink_threshold": 0.25,      # Ngưỡng EAR phát hiện chớp mắt
    "blink_frames": 3,            # Số frame liên tiếp xác nhận chớp mắt
    "drowsy_threshold": 0.25,     # Ngưỡng EAR phát hiện buồn ngủ
    "drowsy_duration": 1.5        # Thời gian (giây) xác nhận buồn ngủ
}

# ===== MAR (Mouth Aspect Ratio) CONFIGURATION =====
MAR_CONFIG = {
    "yawn_threshold": 0.6,        # Ngưỡng MAR phát hiện ngáp
    "yawn_duration": 1.2,         # Thời gian (giây) xác nhận ngáp
    "speaking_threshold": 0.4     # Ngưỡng MAR phân biệt nói/im lặng
}

# ===== HEAD POSE CONFIGURATION =====
HEAD_POSE_CONFIG = {
    "normal_threshold": 12.0,     # Góc pitch bình thường (độ)
    "drowsy_threshold": 20.0,     # Góc pitch buồn ngủ (độ)
    "drowsy_duration": 2.0        # Thời gian (giây) xác nhận buồn ngủ
}
```

### Cấu Hình Camera

Chỉnh sửa trong `src/app/config.py`:

```python
CAMERA_CONFIG = {
    "src": 0,                     # Chỉ số camera (0 = camera mặc định)
    "target_size": (640, 480),    # Kích thước frame
    "fps_limit": 30,              # Giới hạn FPS
    "color": "bgr",               # Định dạng màu
    "normalize": False            # Chuẩn hóa giá trị pixel
}
```

## 🐛 Xử Lý Sự Cố

### Lỗi: "ModuleNotFoundError: No module named 'mediapipe'"

**Giải pháp:**

```bash
pip install mediapipe==0.10.14
```

### Lỗi: "Camera not found" hoặc không mở được camera

**Giải pháp:**

1. Kiểm tra camera có hoạt động không
2. Thử thay đổi chỉ số camera trong `config.py`:
   ```python
   CAMERA_CONFIG = {
       "src": 1,  # Thử 1, 2, 3... nếu 0 không hoạt động
   }
   ```
3. Kiểm tra quyền truy cập camera của ứng dụng

### Lỗi: FPS thấp hoặc lag

**Giải pháp:**

1. Giảm độ phân giải camera:
   ```python
   CAMERA_CONFIG = {
       "target_size": (480, 360),  # Giảm từ (640, 480)
   }
   ```
2. Đóng các ứng dụng khác đang sử dụng camera
3. Kiểm tra CPU và RAM

### Lỗi: Python version không phù hợp

**Giải pháp:**

```bash
# Gỡ cài đặt môi trường cũ
rm -rf .venv

# Tạo lại với Python 3.11
python3.11 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# hoặc
.venv\Scripts\activate  # Windows

# Cài đặt lại thư viện
pip install -r requirements.txt
```

### Lỗi: ImportError liên quan đến OpenCV

**Giải pháp:**

```bash
pip uninstall opencv-python opencv-python-headless
pip install opencv-python
```

## 📊 Hiểu Về Các Chỉ Số

### EAR (Eye Aspect Ratio)

- **Công thức**: `EAR = (||p2-p6|| + ||p3-p5||) / (2 × ||p1-p4||)`
- **Mắt mở**: EAR ≈ 0.25 - 0.3
- **Chớp mắt**: EAR < 0.2 trong < 1.5 giây
- **Buồn ngủ**: EAR < 0.2 trong ≥ 1.5 giây

### MAR (Mouth Aspect Ratio)

- **Miệng đóng**: MAR ≈ 0.0 - 0.3
- **Nói chuyện**: MAR ≈ 0.3 - 0.5
- **Ngáp**: MAR > 0.6 trong ≥ 1.2 giây

### Head Pose (Góc Đầu)

- **Bình thường**: |pitch| < 12°
- **Hơi cúi**: 12° < |pitch| < 20°
- **Buồn ngủ**: |pitch| ≥ 20° trong ≥ 2.0 giây

## 🧪 Chạy Tests

```bash
# Chạy tất cả tests
python -m pytest tests/

# Chạy test cụ thể
python -m pytest tests/test_detection_rules.py -v

# Chạy với coverage
python -m pytest tests/ --cov=src --cov-report=html
```

## 📝 Ghi Log

Logs được lưu tại thư mục `log/`:

- `log/fatigue_detection.log` - Log chi tiết hệ thống
- Snapshots được lưu tại `output/snapshots/`

## 🤝 Đóng Góp

Mọi đóng góp đều được chào đón! Vui lòng:

1. Fork repository
2. Tạo branch mới (`git checkout -b feature/TenTinhNang`)
3. Commit thay đổi (`git commit -m 'Thêm tính năng X'`)
4. Push lên branch (`git push origin feature/TenTinhNang`)
5. Tạo Pull Request

## 📄 License

Dự án này được phát hành dưới MIT License.

## 📧 Liên Hệ

Nếu có câu hỏi hoặc vấn đề, vui lòng tạo issue trên GitHub.

## 🙏 Acknowledgments

- [Mediapipe](https://mediapipe.dev/) - Face detection và landmarks
- [OpenCV](https://opencv.org/) - Computer vision
- Các nghiên cứu về EAR và MAR trong phát hiện mệt mỏi tài xế

---

**Chúc bạn sử dụng thành công! 🚗💨**
