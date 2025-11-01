import cv2

print("Testing camera availability...")

# Test different camera indices
for i in range(5):
    print(f"\nTesting camera index {i}:")
    
    # Try different backends
    backends = [
        ("DSHOW", cv2.CAP_DSHOW),
        ("MSMF", cv2.CAP_MSMF), 
        ("ANY", cv2.CAP_ANY)
    ]
    
    for backend_name, backend in backends:
        try:
            cap = cv2.VideoCapture(i, backend)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    print(f"  ✅ {backend_name}: Working! Frame shape: {frame.shape}")
                    cap.release()
                    break
                else:
                    print(f"  ❌ {backend_name}: Opened but no frame")
            else:
                print(f"  ❌ {backend_name}: Failed to open")
            cap.release()
        except Exception as e:
            print(f"  ❌ {backend_name}: Exception - {e}")

print("\nCamera test completed!")