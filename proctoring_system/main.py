import cv2
import time
import json
from datetime import datetime
from input.video_stream import get_video_stream
from models.yolo_detector import YoloDetector
from models.tracker import SimpleTracker
from models.face_recognition import FaceRecognition
from models.face_mesh import FaceMeshDetector
from models.head_pose import HeadPoseEstimator
from models.gaze_estimator import GazeEstimator
from core.behavior_engine import BehaviorEngine
from core.risk_engine import RiskEngine
from core.alert_manager import AlertManager
from utils.drawing import draw_boxes, draw_tracks
from utils.helpers import get_rects
from config.settings import CAMERA_ID

def main():
    print("[INFO] Starting Proctoring System...")
    print("[INFO] Initializing Video Stream...")
    stream = get_video_stream(CAMERA_ID)
    
    print("[INFO] Loading YOLO Detector (this might take a moment if downloading weights)...")
    detector = YoloDetector()
    
    print("[INFO] Initializing Phase 2 Intelligence Engines...")
    tracker = SimpleTracker()
    face_recognition = FaceRecognition()
    
    # Phase 2 Components
    mesh_detector = FaceMeshDetector()
    pose_estimator = HeadPoseEstimator()
    gaze_estimator = GazeEstimator()
    
    behavior_engine = BehaviorEngine(history_len=15)
    risk_engine = RiskEngine()
    alert_manager = AlertManager()  # Uses new 3-second cooldown logic

    print("[INFO] System ready! Press 'q' to quit.")
    DEBUG = False  # Set to True to display extra debug info

    frame_count = 0
    last_detections = []
    
    # Phone tracking state
    phone_miss_counter = 0
    last_phone_bbox = None
    phone_visible = False
    
    # Event tracking state
    active_events = {}

    for frame in stream:
        frame_count += 1
        
        # Run detection every 2nd frame for performance
        if frame_count % 2 != 0:
            detections = detector.detect(frame)
            last_detections = detections
        else:
            detections = last_detections
        
        # Only pass PERSON detections to tracker
        person_boxes = [
            det['bbox']
            for det in detections
            if det['class_name'] == 'person'
        ]
        
        # Select primary person (largest area) if robustly found
        primary_person_roi = None
        if person_boxes:
            largest_area = 0
            for box in person_boxes:
                area = (box[2] - box[0]) * (box[3] - box[1])
                if area > largest_area:
                    largest_area = area
                    primary_person_roi = box
            
            # Skip evaluation if person is too small (e.g. background noise)
            if largest_area < 5000:
                primary_person_roi = None

        # Phone smoothing logic with heuristic fallback
        phone_detected = False
        for det in detections:
            if det['class_name'] == 'cell phone':
                phone_detected = True
                last_phone_bbox = det['bbox']
                break
                
        if phone_detected:
            phone_miss_counter = 0
            phone_visible = True
        else:
            phone_miss_counter += 1
            
        if phone_miss_counter > 2:
            phone_visible = False
            last_phone_bbox = None
        
        tracks = tracker.update(person_boxes)

        # Basic face recognition placeholder
        recognized_faces = []
        for rect in person_boxes:
            recognized_faces.append(face_recognition.recognize(frame, rect))

        # Centralized frame flags
        flags = {
            "phone": phone_visible
        }
        
        # Start event collection
        frame_events = set()
        if flags["phone"]:
            frame_events.add("PHONE")

        # MediaPipe Face Mesh & Behavior Processing
        gaze = "unknown"
        pose = {"yaw": 0.0, "pitch": 0.0}
        face_count = 0
        
        # Only process mesh if we have a valid primary person in view
        if primary_person_roi is not None and len(primary_person_roi) == 4:
            # Optionally isolate ROI, but MediaPipe handles full frame well
            # Expand slightly for face mesh finding or process the FULL frame to catch multiple background faces!
            mesh_results = mesh_detector.detect(frame)  # Using full frame for accurate multi-face
            if mesh_results[0] is not None:
                mesh_points, face_count = mesh_results
                pose = pose_estimator.estimate(mesh_points)
                gaze = gaze_estimator.estimate(mesh_points, pose)
        else:
            # Fallback to scan full frame anyway to find faces if primary tracking failed
            mesh_results = mesh_detector.detect(frame)
            if mesh_results[0] is not None:
                mesh_points, face_count = mesh_results
                pose = pose_estimator.estimate(mesh_points)
                gaze = gaze_estimator.estimate(mesh_points, pose)
        
        behavior_events = behavior_engine.process(gaze, pose, face_count, flags)
        all_events = list(frame_events.union(behavior_events))
        
        # Risk Scoring and Alerting
        risk_score, reasons, prioritized_events = risk_engine.compute(flags, all_events)

        for event in all_events:
            alert_manager.log(event)
            
        # --- Event Logging Logic ---
        current_time = time.time()
        EVENT_GRACE_PERIOD = 1.0  # seconds
        
        # 1. Update active events
        for event in all_events:
            if event not in active_events:
                active_events[event] = {"start_time": current_time, "last_seen": current_time}
            else:
                active_events[event]["last_seen"] = current_time
                
        # 2. End events that exceeded grace period
        ended_events = []
        for event, data in active_events.items():
            if current_time - data["last_seen"] > EVENT_GRACE_PERIOD:
                duration = data["last_seen"] - data["start_time"]
                ended_events.append(event)
                
                log_entry = {
                    "event": event,
                    "start_time": datetime.fromtimestamp(data["start_time"]).isoformat(),
                    "duration": round(duration, 2),
                    "risk_score": round(risk_score, 2)
                }
                
                # Append to JSON file as a new line
                with open("events.json", "a") as f:
                    f.write(json.dumps(log_entry) + "\n")
                    
        # Remove ended events from active tracking
        for event in ended_events:
            del active_events[event]

        frame_data = {
            "detections": detections,
            "tracks": tracks,
            "gaze": gaze,
            "head_pose": pose,
            "events": all_events,
            "reasons": reasons,
            "risk_score": risk_score,
            "flags": flags,
            "debug": DEBUG
        }

        # Prepare stabilized detections for drawing
        draw_detections = [d for d in detections if d['class_name'] != 'cell phone']
        if phone_visible and last_phone_bbox is not None:
            draw_detections.append({'class_name': 'cell phone', 'bbox': last_phone_bbox})

        # Rendering
        from utils.drawing import draw_ui  # To decouple heavy drawing
        draw_boxes(frame, draw_detections)
        draw_tracks(frame, tracks, debug=DEBUG)
        draw_ui(frame, frame_data)

        cv2.imshow("Proctoring System", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()