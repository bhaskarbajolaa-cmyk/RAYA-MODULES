import base64
import numpy as np
from io import BytesIO
from PIL import Image
import face_recognition
from typing import List, Dict, Any, Optional, Tuple
from database import get_raya_connection, serialize_vector, deserialize_vector

class BiometricMatcher:
    def __init__(self, threshold: float = 0.5):
        """
        Initializes biometric matcher with Euclidean distance matching threshold.
        Typical values are 0.5 to 0.6 (where lower means stricter match).
        """
        self.threshold = threshold

    @staticmethod
    def base64_to_image(b64_str: str) -> np.ndarray:
        """
        Converts base64 image data URL (e.g. data:image/jpeg;base64,...) to RGB numpy array.
        """
        if "," in b64_str:
            b64_str = b64_str.split(",")[1]
        img_data = base64.b64decode(b64_str)
        image = Image.open(BytesIO(img_data))
        return np.array(image.convert("RGB"))

    def extract_face_encoding(self, image_np: np.ndarray) -> Optional[List[float]]:
        """
        Detects faces in an RGB image and returns the 128-dimensional face encoding vector
        for the first detected face. Returns None if no face is found.
        """
        face_locations = face_recognition.face_locations(image_np, model="hog")
        if not face_locations:
            return None
        
        # Extract face encoding for the first detected face
        encodings = face_recognition.face_encodings(image_np, known_face_locations=[face_locations[0]])
        if encodings:
            return encodings[0].tolist()
        return None

    def identify_user(self, face_encoding: List[float]) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Matches a query face encoding against raya.db database using SQLite euclidean_distance.
        Returns a tuple of (matched_user_dict or None, distance_float).
        """
        serialized_query = serialize_vector(face_encoding)
        
        with get_raya_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, full_name, abha_number, last_checkin, created_at,
                       euclidean_distance(face_encoding, ?) AS distance
                FROM raya_users
                ORDER BY distance ASC
                LIMIT 1
                """,
                (serialized_query,)
            )
            row = cursor.fetchone()
            
            if row:
                record = dict(row)
                distance = record.pop("distance")
                if distance <= self.threshold:
                    # Update check-in time
                    conn.execute("UPDATE raya_users SET last_checkin = CURRENT_TIMESTAMP WHERE id = ?", (record["id"],))
                    conn.commit()
                    return record, distance
                else:
                    return None, distance
                    
        return None, float('inf')

    def register_user(self, full_name: str, face_encoding: List[float], abha_number: Optional[str] = None) -> int:
        """
        Saves user biometrics to local database. Returns the new user's ID.
        """
        serialized_encoding = serialize_vector(face_encoding)
        
        with get_raya_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO raya_users (full_name, face_encoding, abha_number)
                VALUES (?, ?, ?)
                """,
                (full_name, serialized_encoding, abha_number)
            )
            user_id = cursor.lastrowid
            conn.commit()
            return user_id
