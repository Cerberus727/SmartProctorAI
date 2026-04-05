import torch
import cv2
import time
from facenet_pytorch import MTCNN
from .facenet_model import get_facenet_model

class FaceVerifier:
    def __init__(self, device='cpu'):
        """
        Initializes the MTCNN face detector and FaceNet embedder.
        """
        self.device = device
        # MTCNN for face detection and cropping
        self.mtcnn = MTCNN(keep_all=False, device=self.device)
        # Pretrained InceptionResnetV1
        self.model = get_facenet_model(self.device)
        
        # Store multiple embeddings to finalize the reference
        self.reference_embeddings = []
        self.reference_embedding = None
        self.is_enrolled = False
        self.required_samples = 10
        self.last_capture_time = 0
        
        # Temporal smoothing counter
        self.mismatch_counter = 0

    def get_embedding(self, frame):
        """
        Detects a face in the frame using MTCNN and extracts its normalized embedding.
        Returns None if no face is detected.
        """
        # Convert BGR (OpenCV) to RGB (MTCNN expects RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect and crop face
        face = self.mtcnn(rgb_frame)
        if face is None:
            return None
        
        # Add batch dimension: [1, 3, 160, 160]
        face = face.unsqueeze(0).to(self.device)
        
        # Compute embedding
        with torch.no_grad():
            embedding = self.model(face)
            # Normalize embedding
            embedding = embedding / embedding.norm()
            
        return embedding

    def auto_capture(self, frame):
        """
        Automatically captures references over time until required samples are collected.
        Returns the number of current samples and required samples.
        """
        if self.is_enrolled:
            return self.required_samples, self.required_samples

        current_time = time.time()
        # Add 0.3s time gap between captures
        if current_time - self.last_capture_time >= 0.3:
            embedding = self.get_embedding(frame)
            if embedding is not None:
                self.reference_embeddings.append(embedding)
                self.last_capture_time = current_time
                print(f"Capturing face: {len(self.reference_embeddings)}/{self.required_samples}")
                
                if len(self.reference_embeddings) >= self.required_samples:
                    self.finalize_reference()
                    
        return len(self.reference_embeddings), self.required_samples

    def add_reference(self, frame):
        """
        Captures a face embedding and adds it to the reference samples list.
        """
        embedding = self.get_embedding(frame)
        if embedding is not None:
            self.reference_embeddings.append(embedding)
            print(f"Sample captured. Total samples: {len(self.reference_embeddings)}")
            return True
        else:
            print("Warning: No face detected. Could not capture sample.")
            return False

    def finalize_reference(self):
        """
        Computes the mean of all collected embeddings to finalize the reference.
        """
        if not self.reference_embeddings:
            print("Warning: No reference samples available to finalize.")
            return False
        
        # Compute mean
        mean_embedding = torch.mean(torch.stack(self.reference_embeddings), dim=0)
        # Normalize the mean embedding
        self.reference_embedding = mean_embedding / mean_embedding.norm()
        self.is_enrolled = True
        print("Reference capture complete. System ready for verification.")
        return True

    def verify(self, frame, threshold=0.9, consecutive_checks=5):
        """
        Computes the L2 distance between the current face and the reference.
        Returns a tuple: (is_same_person, distance)
        Uses temporal smoothing to avoid false positives.
        """
        if self.reference_embedding is None:
            # Not initialized/finalized yet, skip verification
            return True, None

        embedding = self.get_embedding(frame)
        if embedding is None:
            # Safe verify logic: If no face detected, do not trigger mismatch
            self.mismatch_counter = max(0, self.mismatch_counter - 1)
            return True, None

        # Compute L2 distance between normalized current and reference embedding
        diff = embedding - self.reference_embedding
        dist = torch.norm(diff).item()

        # Check distance against threshold
        if dist < threshold:
            self.mismatch_counter = 0
            is_same = True
        else:
            self.mismatch_counter += 1
            # Require sustained mismatch
            if self.mismatch_counter >= consecutive_checks:
                is_same = False
            else:
                is_same = True

        return is_same, dist
