import cv2
import sys
import time
import os
import platform

# Add: enable console key input on Windows
USE_WINDOWS_CONSOLE_KEYS = (os.name == "nt")
if USE_WINDOWS_CONSOLE_KEYS:
    import msvcrt

# If this script is run directly, ensure the project root is on sys.path so
# imports like `from src...` work regardless of the current working directory.
try:
    # Try the import first (fast path)
    from src.input_layer.camera_handler import CameraHandler
    from src.processing_layer.detect_landmark.landmark import FaceLandmarkDetector
except ModuleNotFoundError:
    # Compute project root by walking up from this file's directory until we find a folder
    # that contains the top-level `src` directory (two levels up from this file normally).
    THIS_DIR = os.path.dirname(os.path.abspath(__file__))
    # project root is three levels up from this file: src/processing_layer/detect_landmark -> src -> project root
    project_root = os.path.abspath(os.path.join(THIS_DIR, "..", "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Retry imports
    from src.input_layer.camera_handler import CameraHandler
    from src.processing_layer.detect_landmark.landmark import FaceLandmarkDetector

def main():
    # Initialize components
    cam = CameraHandler(target_size=(640, 480), fps_limit=30)
    detector = FaceLandmarkDetector()
    
    print("Starting camera and face detection...")
    print("Press 'q' to quit, 's' to save snapshot")
    
    try:
        # Start camera thread
        cam.start()
        
        # Give camera time to initialize
        time.sleep(1.0)
        
        frame_count = 0
        while True:
            # Get frame from camera
            frame = cam.read_frame()
            
            if frame is None:
                print("No frame available, waiting...")
                time.sleep(0.1)
                continue
                
            frame_count += 1
            
            # Process landmarks
            landmarks, annotated = detector.detect(frame)
            
            if landmarks:
                features = detector.extract_important_points(landmarks)
                if features:
                    annotated = detector.draw_debug_overlay(annotated, features)
                    # Add status text
                    cv2.putText(annotated, f"Landmarks: {len(landmarks)}", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                # No face detected
                cv2.putText(annotated, "No face detected", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Add frame counter
            cv2.putText(annotated, f"Frame: {frame_count}", 
                       (10, annotated.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Show frame
            cv2.imshow("Debug Overlay", annotated)
            
            # Handle keyboard input (window)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                snapshot_path = f"snapshot_{frame_count}.jpg"
                cv2.imwrite(snapshot_path, annotated)
                print(f"Saved snapshot: {snapshot_path}")

            # Also accept keys from terminal on Windows so pressing 'q' in terminal works
            if USE_WINDOWS_CONSOLE_KEYS and msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch.lower() == 'q':
                    break
                elif ch.lower() == 's':
                    snapshot_path = f"snapshot_{frame_count}.jpg"
                    cv2.imwrite(snapshot_path, annotated)
                    print(f"Saved snapshot: {snapshot_path}")
                
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        print("Cleaning up...")
        cam.release()
        detector.release()
        cv2.destroyAllWindows()
        print("Done!")

if __name__ == "__main__":
    main()
