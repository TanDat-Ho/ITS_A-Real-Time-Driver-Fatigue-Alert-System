# ITS_A-Real-Time-Driver-Fatigue-Alert-System/

```
│
├── 📁 assets/ ← Tài nguyên (âm thanh, icon)
│ ├── icon/
│ ├── sounds/
│
├── 📁 src/
│ ├── 📁 input_layer/ ← Lớp thu nhận dữ liệu
│ │ └── camera_handler.py # Mở webcam, đọc frame, resize, chuẩn hóa
│ │
│ ├── 📁 processing_layer/ ← Lớp xử lý & phân tích
│ │ ├── detect_landmark/
│ │ │ └── landmark.py
│ │ ├── detect_rules/
│ │ │ ├── ear.py
│ │ │ ├── mar.py
│ │ │ ├── head_pose.py
│ │ │ └── **init**.py
│ │ ├── vision_processor/
│ │ │ └── rule_based.py # Rule-based logic + state machine
│ │ └── **init**.py
│ │
│ ├── 📁 output_layer/ ← Lớp phản hồi & cảnh báo
│ │ ├── alert_module.py # playsound, text overlay, CAN bus
│ │ ├── logger.py # ghi log ra file
│ │ ├── ui/
│ │ │ └── main_window.py
│ │ └── **init**.py
│ │
│ ├── 📁 app/
│ │ ├── main.py # file điều phối pipeline tổng thể
│ │ ├── config.py # chứa threshold EAR, MAR, pitch
│ │ └── **init**.py
│ │
│ └── **init**.py
│
├── 📁 logs/ ← Lưu log và dữ liệu thực nghiệm
│ └── drowsy_log_2025-10-12.txt
│
├── 📁 tests/ ← Unit tests cho EAR, MAR, Head Pose
│ └── test_detection_rules.py
│
├── 📄 requirements.txt
├── 📄 README.md
├── 📄 run.py ← Entry point: chạy toàn bộ hệ thống
└── 🚫 .gitignore
```
