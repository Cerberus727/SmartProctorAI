class RiskEngine:
    def __init__(self):
        self.current_risk = 0.0
        self.priorities = {
            "NO_FACE_DETECTED": "HIGH",
            "PHONE": "HIGH", 
            "MULTIPLE_PERSON": "HIGH",
            "MULTIPLE_FACES_DETECTED": "HIGH",
            "PHONE_AND_LOOKING_DOWN": "HIGH",
            "LOOKING_AWAY": "MEDIUM",
            "FACE_NOT_VISIBLE": "MEDIUM",
            "LOOKING_DOWN": "LOW"
        }
        
    def compute(self, flags, behaviors):
        risk = 0.0
        reasons = []
        prioritized_events = {"HIGH": [], "MEDIUM": [], "LOW": []}
        
        # Behaviors already contain all centralized events from main.py
        behaviors_list = list(set(behaviors)) # Remove potential duplicates
            
        for event in behaviors_list:
            level = self.priorities.get(event, "LOW")
            prioritized_events[level].append(event)
            
            # Simple additive risk score
            if event == "NO_FACE_DETECTED":
                risk += 0.5
            elif event == "PHONE":
                risk += 0.5
            elif event == "LOOKING_AWAY":
                risk += 0.3
            elif event == "PHONE_AND_LOOKING_DOWN":
                risk += 0.2  # Additional boost if phone and looking down
            elif event in ("MULTIPLE_PERSON", "MULTIPLE_FACES_DETECTED"):
                risk += 0.5
            elif event == "FACE_NOT_VISIBLE":
                risk += 0.3
                
            reasons.append(f"{event} ({level})")
            
        self.current_risk = max(0.0, min(risk, 1.0))
        return self.current_risk, reasons, prioritized_events