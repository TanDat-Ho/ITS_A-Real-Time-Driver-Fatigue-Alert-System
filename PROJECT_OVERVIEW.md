# 📚 Tổng Quan Dự Án

## 🎯 Mục Đích

Hệ thống phát hiện mệt mỏi và buồn ngủ của tài xế theo thời gian thực để nâng cao an toàn giao thông.

## 📁 Cấu Trúc Tài Liệu

### Tài Liệu Chính

1. **[README.md](README.md)** (435 dòng)
   - Giới thiệu tổng quan hệ thống
   - Hướng dẫn cài đặt chi tiết từng bước
   - Yêu cầu hệ thống (phần cứng & phần mềm)
   - Kiến trúc hệ thống
   - Hướng dẫn chạy ứng dụng với các chế độ khác nhau
   - Giải thích chi tiết về EAR, MAR, Head Pose
   - Xử lý sự cố thường gặp
   - Cấu hình nâng cao

2. **[QUICKSTART.md](QUICKSTART.md)** (96 dòng)
   - Hướng dẫn cài đặt nhanh trong 5 phút
   - Các lệnh chính thường dùng
   - Xử lý lỗi nhanh
   - Liên kết đến tài liệu đầy đủ

3. **[CHANGELOG.md](CHANGELOG.md)** (44 dòng)
   - Lịch sử thay đổi của dự án
   - Các tính năng đã triển khai
   - Cải tiến và cập nhật

4. **[docs/USAGE.md](docs/USAGE.md)** (150 dòng)
   - Hướng dẫn sử dụng chi tiết
   - Giải thích các chế độ cấu hình
   - Hiểu giao diện và các chỉ số
   - Các tình huống thực tế
   - Tối ưu hiệu suất
   - Tips & Tricks

5. **[requirements.txt](requirements.txt)** (30 dòng)
   - Danh sách thư viện cần thiết
   - Hướng dẫn cài đặt
   - Lưu ý về phiên bản Python

## 🚀 Bắt Đầu Nhanh

### Cho Người Dùng Mới

1. Đọc [QUICKSTART.md](QUICKSTART.md) - 5 phút
2. Cài đặt theo hướng dẫn
3. Chạy `python run.py`

### Cho Người Dùng Có Kinh Nghiệm

1. Đọc [README.md](README.md) phần "Cài Đặt" và "Chạy Ứng Dụng"
2. Tùy chỉnh cấu hình trong `src/app/config.py`
3. Đọc [docs/USAGE.md](docs/USAGE.md) để tối ưu

## 📖 Hướng Dẫn Đọc Tài Liệu

### Theo Trường Hợp Sử Dụng

#### "Tôi muốn cài đặt và chạy ngay"
→ [QUICKSTART.md](QUICKSTART.md)

#### "Tôi muốn hiểu hệ thống hoạt động như thế nào"
→ [README.md](README.md) - Phần "Kiến Trúc" và "Hiểu Về Các Chỉ Số"

#### "Tôi gặp lỗi khi cài đặt"
→ [README.md](README.md) - Phần "Xử Lý Sự Cố"

#### "Tôi muốn tùy chỉnh hệ thống"
→ [README.md](README.md) - Phần "Cấu Hình Nâng Cao"
→ [docs/USAGE.md](docs/USAGE.md) - Phần "Tối Ưu Hiệu Suất"

#### "Tôi muốn biết cách sử dụng hiệu quả"
→ [docs/USAGE.md](docs/USAGE.md)

#### "Tôi muốn biết lịch sử phát triển"
→ [CHANGELOG.md](CHANGELOG.md)

## 🎓 Kiến Thức Cần Biết

### Cơ Bản
- Python cơ bản
- Sử dụng command line/terminal
- Hiểu về camera và webcam

### Nâng Cao
- Computer Vision cơ bản
- OpenCV
- Mediapipe
- Các khái niệm EAR, MAR trong phát hiện mệt mỏi

## 🛠️ Công Nghệ Sử Dụng

### Core Technologies
- **Python 3.8-3.11**: Ngôn ngữ lập trình
- **OpenCV**: Xử lý ảnh và video
- **Mediapipe**: Phát hiện khuôn mặt (468 landmarks)
- **NumPy**: Tính toán ma trận

### Architecture
- **Multi-threaded**: Xử lý song song
  - Capture Thread: Đọc camera
  - Processing Thread: Phân tích
  - Display Thread: Hiển thị UI
- **Queue-based**: Giao tiếp giữa các thread
- **Rule-based**: Logic phát hiện mệt mỏi

### Detection Algorithms
- **EAR (Eye Aspect Ratio)**: Phát hiện mắt nhắm
- **MAR (Mouth Aspect Ratio)**: Phát hiện ngáp
- **Head Pose Estimation**: Phát hiện cúi đầu

## 📊 Cấp Độ Cảnh Báo

```
NONE → LOW → MEDIUM → HIGH → CRITICAL
 🟢     🟡      🟠      🔴       🟣
```

## 🎯 Use Cases

1. **Lái xe đường dài**: Sử dụng chế độ `sensitive`
2. **Lái xe trong thành phố**: Sử dụng chế độ `default`
3. **Test và demo**: Sử dụng chế độ `conservative`
4. **Nghiên cứu**: Tùy chỉnh trong `src/app/config.py`

## 📞 Hỗ Trợ

### Vấn Đề Thường Gặp
Xem [README.md](README.md) - Phần "Xử Lý Sự Cố"

### Báo Lỗi
Tạo issue trên GitHub với thông tin:
- Hệ điều hành
- Phiên bản Python
- Log lỗi
- Các bước tái hiện

### Đóng Góp
1. Fork repository
2. Tạo branch mới
3. Commit changes
4. Tạo Pull Request

## 🔗 Liên Kết Hữu Ích

### Nội Bộ
- [README.md](README.md) - Tài liệu chính
- [QUICKSTART.md](QUICKSTART.md) - Bắt đầu nhanh
- [CHANGELOG.md](CHANGELOG.md) - Lịch sử thay đổi
- [docs/USAGE.md](docs/USAGE.md) - Hướng dẫn sử dụng
- [requirements.txt](requirements.txt) - Dependencies

### Mã Nguồn
- `run.py` - Entry point
- `src/app/main.py` - Pipeline chính
- `src/app/config.py` - Cấu hình
- `src/input_layer/camera_handler.py` - Camera
- `src/processing_layer/` - Xử lý
- `src/output_layer/` - Cảnh báo

### External
- [Mediapipe Documentation](https://mediapipe.dev/)
- [OpenCV Documentation](https://docs.opencv.org/)
- [Python Documentation](https://docs.python.org/)

## ✅ Checklist Hoàn Thành

### Tài Liệu
- [x] README.md đầy đủ và chi tiết
- [x] QUICKSTART.md cho người dùng mới
- [x] CHANGELOG.md để tracking
- [x] docs/USAGE.md hướng dẫn chi tiết
- [x] requirements.txt rõ ràng

### Nội Dung
- [x] Hướng dẫn cài đặt từng bước
- [x] Yêu cầu hệ thống
- [x] Kiến trúc hệ thống
- [x] Hướng dẫn chạy
- [x] Giải thích các chỉ số
- [x] Xử lý sự cố
- [x] Cấu hình nâng cao
- [x] Use cases thực tế
- [x] Tips & Tricks

### Ngôn Ngữ
- [x] Toàn bộ bằng tiếng Việt
- [x] Dễ hiểu, rõ ràng
- [x] Có ví dụ minh họa
- [x] Có emoji để dễ đọc

## 🎉 Kết Luận

Dự án đã có tài liệu đầy đủ và chi tiết bằng tiếng Việt, bao gồm:

- **755 dòng** tài liệu tổng cộng
- **5 file** tài liệu chính
- Hướng dẫn cho **mọi cấp độ** người dùng
- Giải thích **kỹ thuật chi tiết**
- **Use cases thực tế**
- **Troubleshooting đầy đủ**

**Người dùng có thể bắt đầu sử dụng ngay từ bây giờ! 🚀**

---

*Tài liệu này được tạo tự động để tổng hợp toàn bộ tài liệu dự án.*
