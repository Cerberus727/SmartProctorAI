import torch
import numpy as np
from collections import deque
import os

from temporalModel.temporal_models import LSTMModel

class TemporalDecisionController:
    def __init__(self):
        self.prev_smoothed = 0.0
        self.recent_preds = deque(maxlen=5)
        self.state = "GREEN"

    def update(self, model_output, raw_outputs):
        # 1. Exponential Moving Average (EMA)
        alpha = 0.7
        smoothed = alpha * model_output + (1 - alpha) * self.prev_smoothed

        # 2. Adaptive Decay
        if model_output < 0.3:
            smoothed *= 0.85

        # 3. Short-term Memory Check
        self.recent_preds.append(model_output)
        if len(self.recent_preds) == 5 and all(p < 0.3 for p in self.recent_preds):
            smoothed *= 0.6

        # 5. Anti-Stuck Logic: check for cheating signals
        phone = float(raw_outputs.get("cell_phone", 0.0))
        gaze_lr = float(raw_outputs.get("gaze_left_right", 0.0))
        book = float(raw_outputs.get("book", 0.0))
        mult = float(raw_outputs.get("multiple_persons", 0.0))
        
        # If no obvious cheating signals, decay faster
        if phone == 0.0 and book == 0.0 and mult == 0.0 and gaze_lr == 0.0:
            smoothed *= 0.7

        smoothed = max(0.0, min(1.0, smoothed))
        self.prev_smoothed = smoothed

        # 4. Hysteresis Thresholding
        if self.state == "RED":
            if smoothed < 0.4:
                self.state = "GREEN"
            elif smoothed < 0.75:
                self.state = "YELLOW"
        elif self.state == "YELLOW":
            if smoothed > 0.75:
                self.state = "RED"
            elif smoothed < 0.35:
                self.state = "GREEN"
        else: # GREEN
            if smoothed > 0.75:
                self.state = "RED"
            elif smoothed > 0.35:
                self.state = "YELLOW"

        return {
            "score": smoothed,
            "state": self.state
        }


def build_feature_vector(raw_outputs):
    """
    Maps the frame dictionary into the EXACT order the PyTorch model expects based on its saved standard scaler.
    The order must reflect the training CSV (verification, num_faces, eyes, mouth, pose, gaze, objects, distance).
    Overrides missing/uncalculated metrics with their dataset means to prevent false anomalies (-6 std dev deviations).
    """
    features = [
        float(raw_outputs.get("timestamp", 0.0)),
        float(raw_outputs.get("face_verified", 1.0)),      # 1: verification_result
        float(raw_outputs.get("num_faces", 1.0)),          # 2: num_faces
        -0.051,                                            # 3: iris_pos (mean mock)
        0.390,                                             # 4: iris_ratio (mean mock)
        float(raw_outputs.get("mouth_open", 0.015)),       # 5: mouth_zone 
        100.686,                                           # 6: mouth_area (mean mock)
        float(raw_outputs.get("head_pose_x", 0.0)),        # 7: x_rotation (pitch)
        float(raw_outputs.get("head_pose_y", 0.0)),        # 8: y_rotation (yaw)
        float(raw_outputs.get("head_pose_z", 0.0)),        # 9: z_rotation (roll)
        7.256,                                             # 10: radial_distance (mean mock)
        float(raw_outputs.get("gaze_left_right", 0.684)),  # 11: gaze_direction 
        0.177,                                             # 12: gaze_zone (mean mock)
        0.027,                                             # 13: watch_detected
        0.343,                                             # 14: headphone_detected
        float(raw_outputs.get("book", 0.0)),               # 15: book
        0.0,                                               # 16: earpiece
        float(raw_outputs.get("cell_phone", 0.0)),         # 17: cell_phone
        float(raw_outputs.get("book", 0.0)),               # 18: book (duplicate mapping)
        0.0,                                               # 19: chits
        0.0016,                                            # 20: sheet
        8085.66,                                           # 21: H-Distance
        9794.13                                            # 22: F-Distance
    ]
    return features


class TemporalIntegrationManager:
    def __init__(self, model_path=None):
        if model_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(base_dir, "temporalModel", "temporal_proctor_trained_on_processed.pt")
            
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load the new LSTMModel
        self.model = LSTMModel(input_size=23, pooling="attention")
        
        self.scaler_mean = np.zeros(23)
        self.scaler_scale = np.ones(23)
        
        try:
            checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)
            if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                self.model.load_state_dict(checkpoint["model_state_dict"], strict=False)
                if "scaler_mean" in checkpoint:
                    self.scaler_mean = checkpoint["scaler_mean"]
                if "scaler_scale" in checkpoint:
                    self.scaler_scale = checkpoint["scaler_scale"]
            else:
                self.model.load_state_dict(checkpoint)
            
            print(f"[Temporal] Model loaded successfully to CPU")
        except Exception as e:
            print(f"[Temporal] Loading failed. Details: {e}")
            
        self.model.to(self.device)
        self.model.eval()
        
        self.decision_controller = TemporalDecisionController()
        self.sequence_buffer = deque(maxlen=15)
        self.last_raw_outputs = {}

    def process_frame_features(self, raw_outputs):
        self.last_raw_outputs = raw_outputs
        
        feature_vector = build_feature_vector(raw_outputs)
        self.sequence_buffer.append(feature_vector)

    def get_temporal_prediction(self):
        if len(self.sequence_buffer) < 15:
            return None
            
        seq = np.array(self.sequence_buffer)       # (15, 23)
        
        # Override the timestamp column (index 0) to be a clean relative step
        seq[:, 0] = np.arange(15)

        # Scale the features using parameters from training phase
        scale_safe = np.where(self.scaler_scale == 0, 1.0, self.scaler_scale)
        scaled_seq = (seq - self.scaler_mean) / scale_safe
        
        seq = np.expand_dims(scaled_seq, axis=0)          # (1, 15, 23)
        seq_tensor = torch.tensor(seq, dtype=torch.float32).to(self.device)

        with torch.no_grad():
            output = self.model(seq_tensor)
            prob = torch.sigmoid(output).item()

        return self.decision_controller.update(prob, self.last_raw_outputs)
