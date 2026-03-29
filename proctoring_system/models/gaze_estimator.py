from collections import deque
import statistics
import math

class GazeEstimator:
    def __init__(self, history_len=15):
        self.history = deque(maxlen=history_len)
        self.prev_gaze = "center"
        self.current_stable_gaze = "center"

    def estimate(self, points, pose=None):
        if not points:
            return self._smooth("unknown")

        current_gaze = "center"
        eye_gaze = self._get_eye_gaze(points)

        # Calculate head roll from eye corners
        left_eye = points[33]
        right_eye = points[263]
        dx = right_eye[0] - left_eye[0]
        dy = right_eye[1] - left_eye[1]
        roll = math.degrees(math.atan2(dy, dx)) if dx != 0 else 0

        # 1. Evaluate combining head pose and eyes
        if pose is not None:
            # Inject roll into pose for downstream behavior engine
            pose['roll'] = roll
            
            yaw_deg = pose['yaw'] * 100
            abs_yaw = abs(yaw_deg)
            
            # Confidence score based on yaw magnitude and eye deviation from center (0.5)
            eye_ratio = self._get_eye_ratio(points)
            eye_dev = abs(eye_ratio - 0.5)
            confidence = (abs_yaw / 30.0) + (eye_dev * 2.0)
            
            if confidence < 0.4:
                current_gaze = "center"
            elif abs(roll) > 15:
                # If head is tilted, ignore yaw completely and rely on eyes
                current_gaze = eye_gaze
            elif pose['pitch'] > 0.6 and abs_yaw <= 8:
                current_gaze = "down"
            elif abs_yaw > 15:
                # Case 1: Strong head turn
                current_gaze = "right" if yaw_deg > 0 else "left"
            elif 8 < abs_yaw <= 15:
                # Case 2: Mild head turn: depends on eye direction
                if eye_gaze != "center":
                    current_gaze = eye_gaze
                else:
                    current_gaze = "center"
            else:
                # Case 3: Head centered (abs_yaw <= 8)
                current_gaze = eye_gaze
        else:
            current_gaze = eye_gaze
            
        self.prev_gaze = current_gaze
            
        # 4. Apply temporal smoothing
        return self._smooth(current_gaze)
        
    def _get_eye_ratio(self, points):
        left_outer = points[33]
        left_inner = points[133]
        left_iris = points[468] 
        
        eye_width = left_inner[0] - left_outer[0]
        if eye_width == 0:
            return 0.5
            
        iris_offset = left_iris[0] - left_outer[0]
        return iris_offset / eye_width
        
    def _get_eye_gaze(self, points):
        eye_ratio = self._get_eye_ratio(points)
        
        # Define tighter thresholds for eye-based gaze
        if eye_ratio < 0.35:
            return "left"
        elif eye_ratio > 0.65:
            return "right"
        return "center"

    def _smooth(self, new_val):
        self.history.append(new_val)
        try:
            mode_val = statistics.mode(self.history)
            # Add small delay/stability by requiring majority in history
            if self.history.count(mode_val) >= len(self.history) * 0.6:
                self.current_stable_gaze = mode_val
            return self.current_stable_gaze
        except statistics.StatisticsError:
            # Fallback if tied (for older Python versions)
            return self.current_stable_gaze