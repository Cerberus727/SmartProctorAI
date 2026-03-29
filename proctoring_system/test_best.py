import cv2
import os
from ultralytics import YOLO

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, "best.pt")

    print(f"Loading model from: {model_path}")
    try:
        model = YOLO(model_path)
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot access webcam")
        return

    print("Webcam started")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.resize(frame, (640, 480))

        try:
            results = model(frame, conf=0.5, iou=0.5, verbose=False)
            annotated_frame = frame.copy()
            
            boxes = results[0].boxes
            if boxes is not None and len(boxes) > 0:
                valid_boxes = [box for box in boxes if box.conf[0] > 0.6]
                
                if valid_boxes:
                    best_box = max(valid_boxes, key=lambda b: b.conf[0])
                    
                    x1, y1, x2, y2 = map(int, best_box.xyxy[0])
                    conf = float(best_box.conf[0])
                    
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(annotated_frame, f"Phone: {conf:.2f}", (x1, max(y1 - 10, 10)), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    print("Detections: 1")
                else:
                    print("No detections")
            else:
                print("No detections")

        except Exception as e:
            print(f"Inference error: {e}")
            annotated_frame = frame

        cv2.imshow("YOLO Test", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()