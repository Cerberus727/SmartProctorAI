class HeadPoseEstimator:
    def estimate(self, points):
        if not points:
            return {"yaw": 0.0, "pitch": 0.0}

        # Simplified robust geometric approach mapping landmarks
        left_eye = points[33]
        right_eye = points[263]
        nose = points[1]
        chin = points[152]
        
        face_width = right_eye[0] - left_eye[0]
        face_height = chin[1] - left_eye[1]
        
        if face_width == 0 or face_height == 0:
            return {"yaw": 0.0, "pitch": 0.0}
        
        eye_center_x = (left_eye[0] + right_eye[0]) / 2.0
        eye_center_y = (left_eye[1] + right_eye[1]) / 2.0
        
        # Calculate shifts to estimate angles
        yaw_ratio = (nose[0] - eye_center_x) / face_width
        pitch_ratio = (nose[1] - eye_center_y) / face_height
        
        return {"yaw": yaw_ratio, "pitch": pitch_ratio}