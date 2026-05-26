import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from database.raya_db import find_nearest_neighbor, insert_raya_user, update_user_checkin

class BiometricMatcher:
    """
    Handles biometric identity verification. It matches query vectors against
    stored L2-normalized 128-dimensional face embedding vectors.
    """

    def __init__(self, threshold: float = 0.6):
        """
        Initializes the matcher with a distance threshold.
        Default is 0.6, typical for 128-D face embeddings (e.g. dlib, FaceNet).
        Distances below this threshold indicate the same individual.
        """
        self.threshold = threshold

    @staticmethod
    def generate_random_encoding() -> List[float]:
        """
        Generates a random 128-dimensional face embedding unit vector.
        Biometric face encodings are typically L2-normalized (length = 1.0).
        """
        vec = np.random.randn(128)
        norm = np.linalg.norm(vec)
        if norm == 0:
            vec[0] = 1.0
            norm = 1.0
        unit_vec = vec / norm
        return unit_vec.tolist()

    @staticmethod
    def generate_probe_encoding(base_encoding: List[float], noise_level: float = 0.05) -> List[float]:
        """
        Simulates a repeated biometric capture of the same individual by adding
        Gaussian noise to the base embedding and re-normalizing it to a unit vector.
        """
        base_arr = np.array(base_encoding)
        noise = np.random.randn(128) * noise_level
        probe = base_arr + noise
        norm = np.linalg.norm(probe)
        if norm == 0:
            return base_encoding
        unit_probe = probe / norm
        return unit_probe.tolist()

    def identify_user(self, probe_encoding: List[float]) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Queries the database for the closest face embedding and checks it against 
        the distance threshold.
        
        Returns:
            A tuple of (matched_user_dict or None, distance_float)
            If the distance <= threshold, returns (user_record, distance).
            Otherwise, returns (None, distance) representing an unrecognized face.
        """
        match = find_nearest_neighbor(probe_encoding)
        if not match:
            return None, float('inf')
            
        user, distance = match
        if distance <= self.threshold:
            update_user_checkin(user["id"])
            return user, distance
            
        # Match found, but distance is greater than the threshold (unrecognized face)
        return None, distance

    def register_user_biometrics(
        self,
        full_name: str,
        face_encoding: List[float],
        abha_number: Optional[str] = None
    ) -> int:
        """
        Registers a new user in the RAYA system with their name, facial encoding, 
        and an optional linked ABHA number.
        """
        return insert_raya_user(full_name, face_encoding, abha_number)
