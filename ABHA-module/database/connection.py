import sqlite3
import struct
import math

def euclidean_distance(blob1, blob2):
    """
    Computes Euclidean distance between two serialized 128-dimensional float32 vectors.
    Each vector is expected to be a 512-byte BLOB.
    """
    if blob1 is None or blob2 is None:
        return 999.0
    
    try:
        # Each float32 is 4 bytes. 128 * 4 = 512 bytes.
        # Format '128f' represents 128 single-precision floats.
        vec1 = struct.unpack('128f', blob1)
        vec2 = struct.unpack('128f', blob2)
        
        # Calculate sum of squared differences
        squared_diff_sum = sum((x - y) ** 2 for x, y in zip(vec1, vec2))
        return math.sqrt(squared_diff_sum)
    except Exception:
        # Return a high distance in case of parsing/unpacking failure
        return 999.0

def get_connection(db_path: str) -> sqlite3.Connection:
    """
    Creates a sqlite3 connection, registers the custom 'euclidean_distance' function,
    and configures the connection to return sqlite3.Row objects.
    """
    conn = sqlite3.connect(db_path)
    # Register custom function (name, num_params, function_pointer)
    conn.create_function("euclidean_distance", 2, euclidean_distance)
    conn.row_factory = sqlite3.Row
    return conn
