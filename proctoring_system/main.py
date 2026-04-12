import cv2
import time
import json
from datetime import datetime

import torch
# PyTorch 2.6+ strict weight loading policy override
import builtins
_original_torch_load = torch.load
def _torch_load_wrapper(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)
torch.load = _torch_load_wrapper

from input.video_stream import get_video_stream
from models.yolo_detector import YoloDetector
from models.tracker import SimpleTracker
from models.face_recognition import FaceRecognition
from models.face_mesh import FaceMeshDetector
from models.head_pose import HeadPoseEstimator
from models.gaze_estimator import GazeEstimator
from facenet_module.face_verifier import FaceVerifier
from core.behavior_engine import BehaviorEngine
from core.risk_engine import RiskEngine
from core.alert_manager import AlertManager
from models.temporal_inference import TemporalIntegrationManager
from utils.drawing import draw_boxes, draw_tracks
from utils.helpers import get_rects
from config.settings import CAMERA_ID

def main():
    stream = None
    try:
        stream = None
        try:
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
            
            print("[INFO] Initializing FaceNet Verifier...")
            verifier = FaceVerifier(device='cpu')  # Ensure it runs reliably 
            reference_set = False
            frame_count = 0
            facenet_result = None
    
            behavior_engine = BehaviorEngine(history_len=15)
            risk_engine = RiskEngine()
            alert_manager = AlertManager()  # Uses new 3-second cooldown logic
            
            print("[INFO] Initializing Temporal Integration Manager...")
            temporal_manager = TemporalIntegrationManager()
            current_temporal_pred = 0.0

            print("[INFO] System ready! Press 'q' to quit.")
            DEBUG = False  # Set to True to display extra debug info

            frame_count = 0
            last_detections = []
    
            # Phone tracking state
            phone_miss_counter = 0
            last_phone_bbox = None
            phone_visible = False
            last_verification_status = True
    
            # Event tracking state
            active_events = {}

            for frame in stream:
                frame_count += 1
                
                # Handle automatic enrollment or verification
                facenet_result = None
                if not verifier.is_enrolled:
                    current_samples, required_samples = verifier.auto_capture(frame)
                    
                    import os
                    p1 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "events.json"))
                    p2 = os.path.abspath(os.path.join(os.path.dirname(__file__), "events.json"))
                    
                    if verifier.is_enrolled:
                        # Just completed enrollment this frame
                        init_event = {
                            "event": "VERIFICATION_COMPLETE",
                            "status": "VERIFIED",
                            "verified": True,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        init_event = {
                            "event": "INITIALIZING",
                            "status": "INITIALIZING",
                            "verified": False,
                            "progress": current_samples,
                            "required": required_samples,
                            "timestamp": datetime.now().isoformat()
                        }
                    
                    # Broadcast the phase status via events log so backend / websockets catch it
                    for p in [p1, p2]:
                        try:
                            with open(p, "a") as f:
                                f.write(json.dumps(init_event) + "\n")
                        except Exception:
                            pass

                    if not verifier.is_enrolled:
                        # Draw enrollment status centered
                        h, w, _ = frame.shape
                        text = f"Initializing Proctoring: Face {current_samples}/{required_samples}"
                        (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
                        text_x = max(0, (w - text_w) // 2)
                        text_y = max(0, (h + text_h) // 2)
                        cv2.putText(frame, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
                        
                        cv2.imshow("Proctoring System", frame)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                        
                        # Return/continue early: DO NOT run YOLO, behavior, or risk engines!
                        continue
                
                # Periodically verify the person against the reference image (every 10 frames)
                if frame_count % 10 == 0:
                        try:
                            same, dist = verifier.verify(frame)
                            if dist is not None:
                                facenet_result = {
                                    "same_person": same,
                                    "distance": dist
                                }
                                last_verification_status = same
                        except Exception as e:
                            pass
        
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

                # Phone & object tracking state
                phone_detected = False
                headphone_detected = False
                book_detected = False
                
                for det in detections:
                    if det['class_name'] == 'cell phone':
                        phone_detected = True
                        last_phone_bbox = det['bbox']
                    elif det['class_name'] == 'headphone':
                        headphone_detected = True
                    elif det['class_name'] == 'book':
                        book_detected = True
                
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
                    "phone": phone_visible,
                    "headphone": headphone_detected,
                    "book": book_detected
                }
        
                # Start event collection
                frame_events = set()
                if flags["phone"]:
                    frame_events.add("PHONE")
                if flags["headphone"]:
                    frame_events.add("HEADPHONE")
                if flags["book"]:
                    frame_events.add("BOOK")

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
        
                # --- 4. FACENET VERIFICATION (Identity Mismatch Alert) ---
                if facenet_result is not None and not facenet_result.get("same_person", True):
                    if "IDENTITY_MISMATCH" not in all_events:
                        all_events.append("IDENTITY_MISMATCH")
                elif not last_verification_status:
                    if "IDENTITY_MISMATCH" not in all_events:
                        all_events.append("IDENTITY_MISMATCH")

                # --- 5. TEMPORAL MODEL (Sequence-based Cheating Detection) ---
                raw_features_dict = {
                    'timestamp': float(frame_count),
                    'face_verified': 1.0 if last_verification_status else 0.0,
                    'num_faces': float(face_count),
                    'gaze_center': 1.0 if gaze == 'center' else 0.0,
                    'mouth_open': 1.0 if "TALKING" in all_events else 0.0,
                    'head_rotation': float(abs(pose.get('yaw', 0.0))) * 100,
                    'left_iris': 0.0,
                    'right_iris': 0.0,
                    'iris_diff': 0.0,
                    'cell_phone': 1.0 if phone_visible else 0.0,
                    'multiple_persons': 1.0 if face_count > 1 else 0.0,
                    'book': 1.0 if flags.get("book") else 0.0,
                    'screen': 1.0 if "SCREEN" in all_events else 0.0,
                    'person': 1.0 if face_count > 0 else 0.0,
                    'mouth_ratio': 0.0,
                    'eye_ratio': 0.0,
                    'head_pose_x': float(pose.get('pitch', 0.0)) * 100,
                    'head_pose_y': float(pose.get('yaw', 0.0)) * 100,
                    'head_pose_z': float(pose.get('roll', 0.0)),
                    'face_distance': 0.0,
                    'f_distance': 0.0,
                    'gaze_left_right': 1.0 if gaze in ['left', 'right', 'down'] else 0.0,
                    'suspicious_movement': 1.0 if "LOOKING_AWAY" in all_events else 0.0
                }
                
                # Push into frame buffer and predict
                temporal_manager.process_frame_features(raw_features_dict)
                temporal_pred = temporal_manager.get_temporal_prediction()
                if temporal_pred is not None:
                    # In temporal_inference.py, it returns a dict with 'score' or float! 
                    score_val = temporal_pred if isinstance(temporal_pred, float) else temporal_pred.get("score", 0.0)
                    current_temporal_pred = score_val
                    if score_val > 0.7: # threshold for cheating probability
                        if "TEMPORAL_CHEATING" not in all_events:
                            all_events.append("TEMPORAL_CHEATING")

                # Risk Scoring and Alerting with FaceNet identity result passed down
                risk_score, reasons, prioritized_events = risk_engine.compute(flags, all_events, facenet_result=facenet_result)

                # The computing method may have appended DIFFERENT_PERSON to `all_events` directly 
                # Be sure we log it down properly.
                for event in set(all_events): 
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
                        import os; p1=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "events.json")); p2=os.path.abspath(os.path.join(os.path.dirname(__file__), "events.json")); 
                        with open(p1, "a") as f:
                            f.write(json.dumps(log_entry) + "\n")
                        with open(p2, "a") as f:
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
                    "is_verified": facenet_result.get("same_person") if facenet_result else True,
                    "debug": DEBUG
                }

                # Prepare stabilized detections for drawing
                draw_detections = [d for d in detections if d['class_name'] != 'cell phone']
                if phone_visible and last_phone_bbox is not None:
                    draw_detections.append({'class_name': 'cell phone', 'bbox': last_phone_bbox})

                # Render frame UI based on the latest data
                frame_data["temporal_pred"] = current_temporal_pred

                # Rendering
                from utils.drawing import draw_ui  # To decouple heavy drawing
                draw_boxes(frame, draw_detections)
                draw_tracks(frame, tracks, debug=DEBUG)
                draw_ui(frame, frame_data)

                cv2.imshow("Proctoring System", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            cv2.destroyAllWindows()

        finally:
            if stream and hasattr(stream, 'close'):
                stream.close()
            cv2.destroyAllWindows()

    finally:
        if stream and hasattr(stream, 'close'):
            stream.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()