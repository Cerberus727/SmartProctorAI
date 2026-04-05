import cv2
import threading
import time

_camera_lock = threading.Lock()

def get_video_stream(src=0):
    import time
    with _camera_lock:
        cap = None
        # If src is an integer, try a fallback of indices if the primary fails
        indices_to_try = [src] if isinstance(src, str) else [src, 1, 2]

        for index in indices_to_try:
            print(f"[INFO] Attempting to start camera on src {index}...")
            # Use CAP_DSHOW on Windows to prevent driver instability and hanging
            import os
            cap_options = []
            if os.name == 'nt':
                cap_options = [
                    (index, cv2.CAP_MSMF, None),
                    (index, cv2.CAP_DSHOW, None),
                    (index, cv2.CAP_ANY, None)
                ]
            else:
                cap_options = [(index, cv2.CAP_ANY, None)]
            
            for src_idx, backend, fourcc in cap_options:
                cap = cv2.VideoCapture(src_idx, backend)
                if fourcc is not None:
                    cap.set(cv2.CAP_PROP_FOURCC, fourcc)
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                
                if cap.isOpened():
                    # Minimal warm up
                    time.sleep(0.1)
                    # Test grab a frame to ensure it's actually streaming and not pure black
                    valid_frame = False
                    for _ in range(5):
                        ret, test_frame = cap.read()
                        if ret and test_frame is not None and test_frame.max() > 0:
                            valid_frame = True
                            break
                        time.sleep(0.01)
                        
                    if valid_frame:
                        print(f"[INFO] Camera successfully engaged on src {index}")
                        break
                    else:
                        print(f"[WARNING] Camera returned no valid frame. Releasing.")
                        cap.release()
                        cap = None
                        
            if cap is not None and cap.isOpened():
                break
        
        if cap is None or not cap.isOpened():
            print(f"[ERROR] Could not open video source. Please check your camera connection.")
            return

    try:
        missed_frames = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                missed_frames += 1
                if missed_frames > 30:
                    print("[ERROR] Failed to grab frame from camera for 30 consecutive attempts.")
                    break
                time.sleep(0.01)
                continue
            missed_frames = 0
            yield frame
    finally:
        if cap is not None:
            cap.release()
        print("[INFO] Camera released")
