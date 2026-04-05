import cv2
from collections import deque
from ultralytics import YOLO
from config.settings import TARGET_CLASSES

CLASS_THRESHOLDS = {
    'person': 0.5,
    'cell phone': 0.4,
    'book': 0.5,
    'laptop': 0.4,
    'tv': 0.4,
    'remote': 0.4,
    'keyboard': 0.4,
    'mouse': 0.4
}
RELAXED_PHONE_THRESHOLD = 0.2

def compute_iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter = max(0, x2 - x1) * max(0, y2 - y1)
    if inter == 0:
        return 0

    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - inter
    return inter / union if union > 0 else 0

import os
import torch
import ultralytics.nn.tasks

# Fix for PyTorch 2.6+ strict weight loading policy
torch.serialization.add_safe_globals([ultralytics.nn.tasks.DetectionModel])

class YoloDetector:
    def __init__(self, model_path='yolov8n.pt'):
        # Resolve the model path relative to the current file's directory if it's just a filename
        if model_path == 'yolov8n.pt' and not os.path.exists(model_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(base_dir, 'yolov8n.pt')
            
        self.model = YOLO(model_path)
    
    def preprocess(self, frame):
        # Only enhance if frame is somewhat dark on average
        mean_brightness = frame.mean()
        if mean_brightness > 100:
            return frame

        # Boost base brightness/contrast slightly
        adjusted = cv2.convertScaleAbs(frame, alpha=1.2, beta=30)
        
        # Apply light Gaussian blur to reduce low-light pixel noise
        blurred = cv2.GaussianBlur(adjusted, (3, 3), 0)

        # Apply CLAHE on the Lightness channel
        lab = cv2.cvtColor(blurred, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        return cv2.cvtColor(cv2.merge((cl, a, b)), cv2.COLOR_LAB2BGR)

    def extract_boxes(self, results, scale_factor=1.0):
        bboxes = []
        for box in results.boxes:
            conf = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = self.model.names[class_id]
            
            if class_name in TARGET_CLASSES:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                if scale_factor != 1.0:
                    x1, y1, x2, y2 = [int(v / scale_factor) for v in (x1, y1, x2, y2)]
                
                # Remove extremely small noise boxes but keep edge ones
                w, h = x2 - x1, y2 - y1
                if w < 15 or h < 15:
                    continue

                # Filter out false "person" boxes that have phone/invalid proportions
                if class_name == 'person':
                    ratio = w / h if h > 0 else 0
                    if ratio < 0.3 or ratio > 1.5:
                        continue

                bboxes.append({
                    'class_name': class_name,
                    'confidence': conf,
                    'bbox': (x1, y1, x2, y2)
                })
        return bboxes

    def nms(self, detections, iou_thresh=0.5):
        # First sort by confidence
        detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)
        kept = []
        
        # Check overlaps
        for det in detections:
            overlap = False
            
            # If it's a person, check if it heavily overlaps with any detected phone first
            if det['class_name'] == 'person':
                for k in kept:
                    if k['class_name'] == 'cell phone':
                        if compute_iou(det['bbox'], k['bbox']) > 0.5:
                            overlap = True
                            break
            
            if overlap:
                continue

            for k in kept:
                # NMS per class to remove duplicate boxes
                if det['class_name'] == k['class_name']:
                    if compute_iou(det['bbox'], k['bbox']) > iou_thresh:
                        overlap = True
                        break
            
            if not overlap:
                kept.append(det)
                
        return kept

    def detect(self, frame):
        enhanced_frame = self.preprocess(frame)
        
        # 1. Original scale
        results_orig = self.model(enhanced_frame, verbose=False)[0]
        raw_detections = self.extract_boxes(results_orig)
        
        # 2. Multi-scale slightly zoomed out
        scale = 0.8
        h, w = enhanced_frame.shape[:2]
        small_frame = cv2.resize(enhanced_frame, (int(w * scale), int(h * scale)))
        results_small = self.model(small_frame, verbose=False)[0]
        raw_detections.extend(self.extract_boxes(results_small, scale_factor=scale))
        
        # We rely strictly on the model detections per frame to remove stale boxes
        detections = []
        phones_raw = []
        phone_detected_current = False
        
        for det in raw_detections:
            cls = det['class_name']
            conf = det['confidence']
            if cls == 'cell phone':
                phones_raw.append(det)

            threshold = CLASS_THRESHOLDS.get(cls, 0.5)
            if conf >= threshold:
                detections.append(det)
                if cls == 'cell phone':
                    phone_detected_current = True

        # Secondary relaxed check for cell phones
        if not phone_detected_current:
            for det in phones_raw:
                if det['confidence'] >= RELAXED_PHONE_THRESHOLD:
                    detections.append(det)
                    break
        
        # Avoid duplicate boxes and false persons overlapping with phones
        final_detections = self.nms(detections)

        return final_detections