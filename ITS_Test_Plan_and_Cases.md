
# 🧪 Test Plan – ITS: Real-Time Driver Fatigue Alert System

## 🎯 1. Mục tiêu
Đảm bảo hệ thống *ITS – Real-Time Driver Fatigue Alert System* hoạt động chính xác và ổn định, phát hiện được trạng thái mệt mỏi của tài xế theo thời gian thực và đưa ra cảnh báo phù hợp.

---

## 📦 2. Phạm vi kiểm thử
Kiểm thử phần **phần mềm** của hệ thống, bao gồm:
- Phát hiện khuôn mặt và mắt người lái.
- Theo dõi chuyển động mắt (nhắm, mở, chớp).
- Phát hiện trạng thái buồn ngủ hoặc mệt mỏi.
- Phát âm thanh hoặc cảnh báo khi phát hiện tình trạng nguy hiểm.
- Đảm bảo hoạt động ổn định trong điều kiện thời gian thực (video stream).

---

## ⚙️ 3. Môi trường kiểm thử
- **Ngôn ngữ:** Python 3.11  
- **Thư viện:** OpenCV, dlib, numpy, playsound, v.v.  
- **Thiết bị:** Laptop có webcam hoặc camera ngoài  
- **OS:** Windows 10 hoặc Linux  

---

## 👥 4. Vai trò
- Tester: sinh viên / QA  
- Developer: nhóm phát triển hệ thống ITS  
- Người quan sát: giảng viên hướng dẫn  

---

## 📅 5. Lịch trình kiểm thử

| Giai đoạn | Hoạt động | Thời gian dự kiến |
|------------|------------|-------------------|
| 1 | Phân tích yêu cầu & thiết kế test case | 1 ngày |
| 2 | Thực hiện kiểm thử đơn vị (unit test) | 2 ngày |
| 3 | Thực hiện kiểm thử tích hợp (integration test) | 2 ngày |
| 4 | Báo cáo kết quả & sửa lỗi | 1 ngày |

---

## ✅ 6. Tiêu chí chấp nhận

| STT | Tiêu chí | Mô tả | Kết quả mong đợi |
|-----|-----------|--------|------------------|
| 1 | Phát hiện khuôn mặt | Hệ thống nhận diện chính xác khuôn mặt người lái | Xác định đúng ≥ 95% khung hình có mặt |
| 2 | Phát hiện mắt nhắm | Khi mắt nhắm > 3 giây, hệ thống báo mệt mỏi | Cảnh báo được kích hoạt |
| 3 | Phát cảnh báo âm thanh | Khi phát hiện buồn ngủ, âm thanh được phát | Âm thanh vang lên rõ ràng |
| 4 | Hiệu năng thời gian thực | FPS ≥ 10 khung hình/giây | Đáp ứng trong thời gian thực |
| 5 | Ổn định hệ thống | Không bị crash hoặc treo khi chạy >10 phút | Ổn định trong toàn phiên |

---

## 🧩 7. Test Case cơ bản

| TC ID | Mô tả | Dữ liệu đầu vào | Kết quả mong đợi | Loại test |
|-------|--------|-----------------|------------------|------------|
| TC01 | Khởi động hệ thống | Chạy `run.py` | Camera mở, giao diện khởi động bình thường | Functional |
| TC02 | Nhận diện khuôn mặt | Video có khuôn mặt người lái | Hệ thống vẽ khung quanh mặt | Functional |
| TC03 | Nhận diện mắt | Hình ảnh người với mắt mở | Hệ thống phát hiện chính xác vị trí mắt | Functional |
| TC04 | Phát hiện nhắm mắt lâu | Video mắt nhắm >3 giây | Cảnh báo phát ra (âm thanh) | Functional |
| TC05 | Không có khuôn mặt | Ảnh/video trống | Hệ thống không kích hoạt cảnh báo | Negative |
| TC06 | Xử lý video dài | Video 10 phút | Hệ thống vẫn hoạt động ổn định | Performance |
| TC07 | Thiếu webcam | Ngắt kết nối camera | Hệ thống hiển thị lỗi “Không tìm thấy camera” | Exception |
| TC08 | FPS đo được | Video chuẩn HD | FPS ≥ 10 | Performance |

---

📘 **Kết luận:**  
Tài liệu này định nghĩa kế hoạch và tiêu chí kiểm thử cơ bản cho hệ thống ITS.  
Các test case có thể mở rộng để bao gồm kiểm thử tự động bằng `pytest` hoặc kiểm thử thực tế trên camera.
