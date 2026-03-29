import cv2

try:
    import mediapipe as mp
except ImportError:
    raise ImportError("MediaPipe not installed correctly. Install mediapipe==0.10.9")

class FaceMeshDetector:
    def __init__(self):
        try:
            if not hasattr(mp, 'solutions'):
                raise RuntimeError("MediaPipe installation is broken. Reinstall mediapipe==0.10.9")
                
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=5,  # Increased to detect multiple faces
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
        except Exception as e:
            raise RuntimeError(f"MediaPipe installation is broken. Reinstall mediapipe==0.10.9. Error: {str(e)}")

    def detect(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        if not results.multi_face_landmarks:
            return None, 0
            
        num_faces = len(results.multi_face_landmarks)
        
        # Primary face is the first one detected (or largest if we sorted, but MP usually gives the most prominent one first)
        landmarks = results.multi_face_landmarks[0]
        h, w, _ = frame.shape
        
        points = [(int(pt.x * w), int(pt.y * h)) for pt in landmarks.landmark]
        
        return points, num_faces