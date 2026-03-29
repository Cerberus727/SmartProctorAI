import time
from collections import deque

class BehaviorEngine:
    def __init__(self, history_len=15):
        self.gaze_history = deque(maxlen=history_len)
        self.pose_history = deque(maxlen=history_len)
        
        # Time-based tracking
        self.away_start_time = None
        self.no_face_start_time = None
        self.multiple_face_frames = 0
        
        self.persistent_events = {}
        self.event_logs = []
        self.active_tracked_events = {}
        
    def process(self, gaze, pose, face_count=1, flags=None):
        if flags is None:
            flags = {}
            
        events = set()
        current_time = time.time()
        
        # 1. Face count processing
        if face_count == 0:
            self.multiple_face_frames = 0
            if self.no_face_start_time is None:
                self.no_face_start_time = current_time
            else:
                duration = current_time - self.no_face_start_time
                if duration > 3.0:
                    events.add("NO_FACE_DETECTED")
                elif duration > 1.0:
                    events.add("FACE_NOT_VISIBLE")
        else:
            self.no_face_start_time = None
            if face_count > 1:
                self.multiple_face_frames += 1
                if self.multiple_face_frames >= 10:
                    events.add("MULTIPLE_FACES_DETECTED")
            else:
                self.multiple_face_frames = 0
            
        self.gaze_history.append(gaze)
        self.pose_history.append(pose)
            
        # 2. Gaze tracking with time
        if gaze in ["left", "right"]:
            if self.away_start_time is None:
                self.away_start_time = current_time
            elif current_time - self.away_start_time > 1.0: # 1 second threshold
                events.add("LOOKING_AWAY")
        elif gaze in ["center", "down"]:
            # Reset away timer
            self.away_start_time = None
            
        # Pose abnormality smoothing
        bad_pose_count = 0
        down_pose_count = 0
        
        for p in self.pose_history:
            if not p:
                continue
                
            yaw_val = abs(p.get('yaw', 0.0))
            pitch_val = p.get('pitch', 0.0)
            roll_val = abs(p.get('roll', 0.0))
            
            if yaw_val > 0.2 and gaze != "center" and roll_val <= 15:
                bad_pose_count += 1
            if pitch_val > 0.6:
                down_pose_count += 1
                
        if bad_pose_count >= 10:
            events.add("LOOKING_AWAY")
            
        if down_pose_count >= 10:
            events.add("LOOKING_DOWN")
            
        # 3. Multi-Condition Logic
        if gaze == "down" and flags.get("phone", False):
            events.add("PHONE_AND_LOOKING_DOWN")
            
        # 4. Event Persistence (short-lived memory for 1.5 seconds)
        for e in events:
            self.persistent_events[e] = current_time
            if e not in self.active_tracked_events:
                self.active_tracked_events[e] = current_time
            
        # Cleanup expired events and log them
        active_events = []
        for e, timestamp in list(self.persistent_events.items()):
            if current_time - timestamp < 1.5:
                active_events.append(e)
            else:
                del self.persistent_events[e]
                # Event ended, log it
                start_time = self.active_tracked_events.pop(e, timestamp)
                duration = current_time - start_time
                self.event_logs.append({
                    "timestamp": time.time(),
                    "event": e,
                    "duration": round(duration, 2)
                })
                
        return set(active_events)