import time
from collections import deque

class EventEngine:
    def __init__(self):
        self.events = []
        # Use simple score instead of naive deque for phone memory
        self.phone_score = 0
        self.max_phone_score = 10
        self.phone_alert_threshold = 5

        self.no_face_history = deque(maxlen=15)
        self.multiple_persons_history = deque(maxlen=15)
        
        # Cooldown management
        self.last_alert_time = {
            "NO_FACE_DETECTED": 0,
            "MULTIPLE_PERSONS_DETECTED": 0,
            "PHONE_DETECTED": 0
        }
        self.cooldown_seconds = 3.0

    def _is_near_person(self, phone_box, person_boxes):
        if not person_boxes:
            return False
            
        px1, py1, px2, py2 = phone_box
        for (bx1, by1, bx2, by2) in person_boxes:
            # Expand person box slightly to check vicinity
            ex1, ey1, ex2, ey2 = bx1 - 150, by1 - 150, bx2 + 150, by2 + 150
            if px1 < ex2 and px2 > ex1 and py1 < ey2 and py2 > ey1:
                return True
        return False

    def process(self, detections, tracks, recognized_faces):
        current_events = []
        person_boxes = []
        phone_boxes = []

        for det in detections:
            if det['class_name'] == 'person':
                person_boxes.append(det['bbox'])
            elif det['class_name'] == 'cell phone':
                phone_boxes.append(det['bbox'])

        persons = len(person_boxes)
        
        # Check if any phone is actually near a person
        phone_detected = False
        for p_box in phone_boxes:
            if self._is_near_person(p_box, person_boxes):
                phone_detected = True
                break

        current_time = time.time()

        self.no_face_history.append(persons == 0)
        if sum(self.no_face_history) == self.no_face_history.maxlen:
            if current_time - self.last_alert_time["NO_FACE_DETECTED"] > self.cooldown_seconds:
                current_events.append("NO_FACE_DETECTED")
                self.last_alert_time["NO_FACE_DETECTED"] = current_time
            self.no_face_history.clear() # Reset after alert

        self.multiple_persons_history.append(persons > 1)
        if sum(self.multiple_persons_history) == self.multiple_persons_history.maxlen:
            if current_time - self.last_alert_time["MULTIPLE_PERSONS_DETECTED"] > self.cooldown_seconds:
                current_events.append("MULTIPLE_PERSONS_DETECTED")
                self.last_alert_time["MULTIPLE_PERSONS_DETECTED"] = current_time
            self.multiple_persons_history.clear()

        # Decay-based logic for phone detection
        if phone_detected:
            self.phone_score = min(self.phone_score + 1, self.max_phone_score)
        else:
            self.phone_score = max(self.phone_score - 2, 0)

        # Alert if phone_score is high enough over time
        if self.phone_score >= self.phone_alert_threshold:
            if current_time - self.last_alert_time["PHONE_DETECTED"] > self.cooldown_seconds:
                current_events.append("PHONE_DETECTED")
                self.last_alert_time["PHONE_DETECTED"] = current_time
                # Drop score so it doesn't immediately double-trigger
                self.phone_score = 0 

        self.events.extend(current_events)
        return current_events