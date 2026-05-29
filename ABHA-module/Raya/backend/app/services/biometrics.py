import base64
import json
import math

class FaceBiometricService:
    def __init__(self):
        # We will use a mock implementation since OpenCV/MediaPipe failed to install on this environment.
        self.has_mediapipe = False
        
    def base64_to_image(self, base64_str: str):
        # Mock implementation: just return length of string as dummy image data
        return len(base64_str)

    def extract_embedding(self, image) -> list[float]:
        """
        Extracts a lightweight embedding.
        Since MediaPipe is unavailable in this environment, this generates a deterministic 
        dummy 128-D vector based on the image length so we can still test the DB logic.
        """
        # Create a deterministic but dummy 128-D array based on input "image" length
        val = (image % 100) / 100.0
        vector = [val * (i % 10) for i in range(128)]
        
        # Normalize
        norm = math.sqrt(sum(v*v for v in vector))
        if norm > 0:
            vector = [v/norm for v in vector]
            
        return vector
        
    def calculate_distance(self, emb1: list[float], emb2: list[float]) -> float:
        """Euclidean distance between two normalized embeddings"""
        return math.sqrt(sum((a - b)**2 for a, b in zip(emb1, emb2)))

# Singleton instance
biometrics = FaceBiometricService()
