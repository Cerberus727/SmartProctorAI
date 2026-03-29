import time

class AlertManager:
    def __init__(self, cooldown=3.0):
        self.logs = []
        self.last_alert_time = {}
        self.cooldown = cooldown

    def log(self, event):
        current_time = time.time()
        last_time = self.last_alert_time.get(event, 0)
        
        if current_time - last_time > self.cooldown:
            self.logs.append(event)
            self.last_alert_time[event] = current_time
            print(f"ALERT: {event}")

    def list_logs(self):
        return self.logs