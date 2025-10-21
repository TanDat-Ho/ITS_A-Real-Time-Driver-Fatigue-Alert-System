# 📖 Hướng Dẫn Sử Dụng Chi Tiết

## Mục Lục

1. [Khởi Động Ứng Dụng](#khởi-động-ứng-dụng)
2. [Các Chế Độ Cấu Hình](#các-chế-độ-cấu-hình)
3. [Hiểu Giao Diện](#hiểu-giao-diện)
4. [Các Tình Huống Thực Tế](#các-tình-huống-thực-tế)
5. [Tối Ưu Hiệu Suất](#tối-ưu-hiệu-suất)

---

## Khởi Động Ứng Dụng

### Cách 1: Chạy Đơn Giản

```bash
python run.py
```

### Cách 2: Chạy Với Cấu Hình Cụ Thể

```bash
# Chế độ mặc định
python run.py --config default

# Chế độ nhạy - phát hiện sớm
python run.py --config sensitive

# Chế độ bảo thủ - ít cảnh báo sai
python run.py --config conservative
```

### Cách 3: Xem Thông Tin

```bash
python run.py --info
```

---

## Các Chế Độ Cấu Hình

### 1. Default (Mặc Định)
- Cân bằng giữa phát hiện và false positive
- Phù hợp sử dụng hàng ngày

### 2. Sensitive (Nhạy)
- Phát hiện sớm hơn
- Phù hợp lái xe đường dài, ban đêm
- Có thể có nhiều false positive

### 3. Conservative (Bảo Thủ)
- Ít cảnh báo sai
- Phù hợp test hệ thống
- Phát hiện chậm hơn

---

## Hiểu Giao Diện

### Cấp Độ Cảnh Báo

| Cấp Độ | Màu | Ý Nghĩa | Hành Động |
|--------|-----|---------|-----------|
| NONE | 🟢 | Tỉnh táo | Tiếp tục |
| LOW | 🟡 | Hơi mệt | Chú ý |
| MEDIUM | 🟠 | Mệt vừa | Cân nhắc nghỉ |
| HIGH | 🔴 | Mệt nhiều | Nghỉ ngay |
| CRITICAL | 🟣 | Nguy hiểm | Dừng xe ngay |

### Các Chỉ Số

- **EAR**: Eye Aspect Ratio (Mắt)
  - > 0.25: Mắt mở
  - < 0.25: Mắt nhắm
  
- **MAR**: Mouth Aspect Ratio (Miệng)
  - < 0.4: Đóng
  - > 0.6: Ngáp
  
- **Pitch**: Góc đầu
  - < 12°: Bình thường
  - > 20°: Cúi đầu

---

## Các Tình Huống Thực Tế

### Lái Xe Đường Dài
```bash
python run.py --config sensitive
```

### Lái Xe Trong Thành Phố
```bash
python run.py --config default
```

### Test Hệ Thống
```bash
python run.py --config conservative
```

---

## Tối Ưu Hiệu Suất

### Giảm Độ Phân Giải
Trong `src/app/config.py`:
```python
CAMERA_CONFIG = {
    "target_size": (480, 360)
}
```

### Giảm FPS
```python
CAMERA_CONFIG = {
    "fps_limit": 25
}
```

---

## Tips & Tricks

### Phím Tắt
- `q` - Thoát
- `r` - Reset
- `s` - Chụp màn hình
- `p` - Xem thống kê

### Vị Trí Camera Tốt Nhất
- Khoảng cách: 50-70cm
- Nhìn thẳng vào mặt
- Ánh sáng đồng đều

### Tránh False Positive
- Chuyển sang chế độ conservative
- Kiểm tra ánh sáng
- Điều chỉnh camera
- Reset thống kê (phím `r`)

---

**Xem thêm:**
- [README.md](../README.md) - Tổng quan
- [QUICKSTART.md](../QUICKSTART.md) - Bắt đầu nhanh
- [CHANGELOG.md](../CHANGELOG.md) - Lịch sử thay đổi
