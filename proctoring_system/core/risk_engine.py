class RiskEngine:
    def __init__(self):
        self.current_risk = 0.0
        self.decay_rate = 0.01  # Gradual decay per frame if behavior is normal
        self.priorities = {
            "NO_FACE_DETECTED": "HIGH",
            "PHONE": "HIGH", 
            "MULTIPLE_PERSON": "HIGH",
            "MULTIPLE_FACES_DETECTED": "HIGH",
            "PHONE_AND_LOOKING_DOWN": "HIGH",
            "DIFFERENT_PERSON": "HIGH",
            "LOOKING_AWAY": "MEDIUM",
            "FACE_NOT_VISIBLE": "MEDIUM",
            "LOOKING_DOWN": "LOW"
        }
        
    def compute(self, flags, behaviors, facenet_result=None):
        reasons = []
        prioritized_events = {"HIGH": [], "MEDIUM": [], "LOW": []}
        
        # Add FaceNet processing
        if facenet_result:
            if not facenet_result.get("same_person", True):
                distance = facenet_result.get("distance")
                if "DIFFERENT_PERSON" not in behaviors:
                    behaviors.append("DIFFERENT_PERSON")

        behaviors_list = list(set(behaviors))
        
        # Risk increments per frame for active events
        risk_step = 0.0
        
        for event in behaviors_list:
            level = self.priorities.get(event, "LOW")
            prioritized_events[level].append(event)
            
            # Weighted formula: Accumulate risk dynamically based on severity
            if event == "DIFFERENT_PERSON":
                risk_step += 0.15
                reasons.append(f"{event} (HIGH)")
            elif event == "PHONE" or event == "PHONE_AND_LOOKING_DOWN":
                risk_step += 0.15
                reasons.append(f"{event} (HIGH)")
            elif event in ("MULTIPLE_PERSON", "MULTIPLE_FACES_DETECTED"):
                risk_step += 0.10
                reasons.append(f"{event} (HIGH)")
            elif event == "NO_FACE_DETECTED":
                risk_step += 0.05
                reasons.append(f"{event} (HIGH)")
            elif event == "LOOKING_AWAY":
                risk_step += 0.02
                reasons.append(f"{event} (MEDIUM)")
            elif event == "FACE_NOT_VISIBLE":
                risk_step += 0.05
                reasons.append(f"{event} (MEDIUM)")
            elif event == "LOOKING_DOWN":
                risk_step += 0.01
                reasons.append(f"{event} (LOW)")
            else:
                reasons.append(f"{event} ({level})")
                
        # Apply formula: Add risk_step if cheating, else decay securely
        if risk_step > 0:
            self.current_risk += risk_step
        else:
            self.current_risk -= self.decay_rate
            
        # Bound securely between 0.0 and 1.0 (equivalent to 0% to 100%)
        self.current_risk = max(0.0, min(self.current_risk, 1.0))
        
        return self.current_risk, reasons, prioritized_events