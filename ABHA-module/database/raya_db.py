import struct
from typing import List, Dict, Any, Optional, Tuple
from database.connection import get_connection

# Path to the simulated local RAYA database
RAYA_DB_PATH = "raya.db"

def serialize_vector(vector: List[float]) -> bytes:
    """
    Serializes a list of 128 floats into a 512-byte binary BLOB (float32).
    """
    if len(vector) != 128:
        raise ValueError(f"Vector must be exactly 128-dimensional, got {len(vector)}")
    return struct.pack("128f", *vector)

def deserialize_vector(blob: bytes) -> List[float]:
    """
    Deserializes a 512-byte binary BLOB into a list of 128 floats.
    """
    if len(blob) != 512:
        raise ValueError(f"BLOB must be exactly 512 bytes, got {len(blob)}")
    return list(struct.unpack("128f", blob))

def init_raya_db() -> None:
    """
    Initializes the RAYA database schema.
    """
    conn = get_connection(RAYA_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raya_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            face_encoding BLOB NOT NULL, -- 128-d float vector
            abha_number TEXT,            -- Link to ABHA database (optional/nullable)
            last_checkin TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def clear_raya_db() -> None:
    """
    Clears all records from the RAYA database.
    """
    conn = get_connection(RAYA_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS raya_users")
    conn.commit()
    conn.close()

def insert_raya_user(
    full_name: str,
    face_encoding: List[float],
    abha_number: Optional[str] = None
) -> int:
    """
    Inserts a new user with their biometric encoding and optional ABHA linkage.
    Returns the ID of the inserted row.
    """
    conn = get_connection(RAYA_DB_PATH)
    cursor = conn.cursor()
    
    blob = serialize_vector(face_encoding)
    cursor.execute(
        "INSERT INTO raya_users (full_name, face_encoding, abha_number) VALUES (?, ?, ?)",
        (full_name, blob, abha_number)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id

def update_user_abha_link(user_id: int, abha_number: Optional[str]) -> None:
    """
    Links or unlinks an ABHA number for an existing RAYA user profile.
    """
    conn = get_connection(RAYA_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE raya_users SET abha_number = ? WHERE id = ?", (abha_number, user_id))
    conn.commit()
    conn.close()

def update_user_checkin(user_id: int) -> None:
    """
    Updates the last check-in timestamp of a user to the current time.
    """
    conn = get_connection(RAYA_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE raya_users SET last_checkin = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def delete_inactive_users(inactive_days: int) -> int:
    """
    Removes user profiles who haven't checked in (scanned face) for more than the specified days.
    Returns the number of profiles deleted.
    """
    conn = get_connection(RAYA_DB_PATH)
    cursor = conn.cursor()
    # In SQLite, datetime('now', '-X days') yields the cutoff point
    cursor.execute(
        "DELETE FROM raya_users WHERE last_checkin < datetime('now', ?)",
        (f"-{inactive_days} days",)
    )
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted_count

def find_nearest_neighbor(
    probe_encoding: List[float]
) -> Optional[Tuple[Dict[str, Any], float]]:
    """
    Searches the RAYA database for the closest biometric match.
    Uses the custom SQLite 'euclidean_distance' function.
    Returns a tuple containing the user's record and the Euclidean distance,
    or None if the database is empty.
    """
    conn = get_connection(RAYA_DB_PATH)
    cursor = conn.cursor()
    
    probe_blob = serialize_vector(probe_encoding)
    
    # Query sorting by euclidean distance to the probe BLOB
    cursor.execute(
        """
        SELECT id, full_name, abha_number, face_encoding, last_checkin, created_at,
               euclidean_distance(face_encoding, ?) AS distance
        FROM raya_users
        ORDER BY distance ASC
        LIMIT 1
        """,
        (probe_blob,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        record = dict(row)
        distance = record.pop("distance")
        # Deserialise the stored vector before returning
        record["face_encoding"] = deserialize_vector(record["face_encoding"])
        return record, distance
        
    return None

def get_all_raya_users() -> List[Dict[str, Any]]:
    """
    Retrieves all RAYA database users.
    """
    conn = get_connection(RAYA_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, abha_number, face_encoding, last_checkin, created_at FROM raya_users")
    rows = cursor.fetchall()
    conn.close()
    
    users = []
    for row in rows:
        user = dict(row)
        user["face_encoding"] = deserialize_vector(user["face_encoding"])
        users.append(user)
    return users
