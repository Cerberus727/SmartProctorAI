import cv2

def get_video_stream(src=0):
    # Try DirectShow backend on Windows as default capture can sometimes hang
    cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)
    if not cap.isOpened():
        # Fallback to default if DSHOW fails
        cap = cv2.VideoCapture(src)
        
    if not cap.isOpened():
        print(f"[ERROR] Could not open video source {src}")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Failed to grab frame from camera.")
                break
            # Yield the frame instead of returning to keep the stream going
            yield frame
    finally:
        cap.release()