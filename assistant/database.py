import os
import sqlite3
import struct
import math
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RAYA_DB_PATH = os.path.join(BASE_DIR, "raya.db")
ABHA_DB_PATH = os.path.join(BASE_DIR, "abha.db")
HOSPITAL_DB_PATH = os.path.join(BASE_DIR, "hospital.db")

def euclidean_distance(blob1, blob2):
    """
    Computes Euclidean distance between two serialized 128-dimensional float32 vectors.
    """
    if blob1 is None or blob2 is None:
        return 999.0
    try:
        vec1 = struct.unpack('128f', blob1)
        vec2 = struct.unpack('128f', blob2)
        squared_diff_sum = sum((x - y) ** 2 for x, y in zip(vec1, vec2))
        return math.sqrt(squared_diff_sum)
    except Exception:
        return 999.0

def get_raya_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(RAYA_DB_PATH)
    conn.create_function("euclidean_distance", 2, euclidean_distance)
    conn.row_factory = sqlite3.Row
    return conn

def get_abha_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(ABHA_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_hospital_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(HOSPITAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def serialize_vector(vector: List[float]) -> bytes:
    if len(vector) != 128:
        raise ValueError(f"Vector must be exactly 128-dimensional, got {len(vector)}")
    return struct.pack("128f", *vector)

def deserialize_vector(blob: bytes) -> List[float]:
    if len(blob) != 512:
        raise ValueError(f"BLOB must be exactly 512 bytes, got {len(blob)}")
    return list(struct.unpack("128f", blob))

def init_databases():
    # 1. Init RAYA Database
    with get_raya_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raya_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                face_encoding BLOB NOT NULL,
                abha_number TEXT,
                last_checkin TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

    # 2. Init ABHA Database
    with get_abha_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                abha_number TEXT PRIMARY KEY,
                abha_address TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                gender TEXT NOT NULL,
                mobile_number TEXT NOT NULL,
                health_records TEXT NOT NULL
            )
        """)
        conn.commit()

    # 3. Init Hospital Database
    with get_hospital_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                abha_number TEXT UNIQUE,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                mobile TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS encounters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                token_number TEXT NOT NULL,
                department TEXT NOT NULL,
                symptoms TEXT NOT NULL,
                priority TEXT NOT NULL,
                clinical_summary TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(patient_id) REFERENCES patients(id)
            )
        """)
        conn.commit()

def seed_databases():
    # Initialize first
    init_databases()

    # Clear existing data to ensure clean seed
    with get_raya_connection() as conn:
        conn.execute("DELETE FROM raya_users")
    with get_abha_connection() as conn:
        conn.execute("DELETE FROM patients")
    with get_hospital_connection() as conn:
        conn.execute("DELETE FROM encounters")
        conn.execute("DELETE FROM patients")

    # Sample Patients
    mock_patients = [
        {
            "abha_number": "91-1111-2222-3333",
            "abha_address": "suresh.kumar@abdm",
            "full_name": "Suresh Kumar",
            "date_of_birth": "1985-05-12",
            "gender": "M",
            "mobile_number": "9876543210",
            "age": 41,
            "health_records": [
                {
                    "date": "2025-10-15",
                    "facility": "City General Hospital",
                    "doctor": "Dr. A. K. Roy",
                    "diagnosis": "Essential Hypertension",
                    "prescription": "Tab Amlodipine 5mg OD x 30 days"
                },
                {
                    "date": "2026-02-10",
                    "facility": "Metro Diagnostics",
                    "doctor": "Dr. S. Sen",
                    "diagnosis": "Routine Blood Panels",
                    "notes": "Fasting Blood Sugar: 98 mg/dL (Normal). HbA1c: 5.4% (Normal)."
                }
            ]
        },
        {
            "abha_number": "91-4444-5555-6666",
            "abha_address": "priya.sharma@abdm",
            "full_name": "Priya Sharma",
            "date_of_birth": "1990-11-23",
            "gender": "F",
            "mobile_number": "9812345678",
            "age": 35,
            "health_records": [
                {
                    "date": "2025-12-01",
                    "facility": "Apex Women Care Clinic",
                    "doctor": "Dr. Rekha Rao",
                    "diagnosis": "First Trimester Checkup",
                    "notes": "Vitals normal. Recommended prenatal vitamins."
                }
            ]
        },
        {
            "abha_number": "91-7777-8888-9999",
            "abha_address": "amit.patel@abdm",
            "full_name": "Amit Patel",
            "date_of_birth": "1978-02-28",
            "gender": "M",
            "mobile_number": "9900112233",
            "age": 48,
            "health_records": [
                {
                    "date": "2025-08-20",
                    "facility": "Orthopedic Specialty Center",
                    "doctor": "Dr. Vikas Patel",
                    "diagnosis": "Mild Osteoarthritis of the Left Knee",
                    "prescription": "Tab Paracetamol 650mg TDS PRN, Physiotherapy twice a week."
                }
            ]
        },
        {
            "abha_number": "91-1234-5678-9012",
            "abha_address": "ananya.sen@abdm",
            "full_name": "Ananya Sen",
            "date_of_birth": "1995-07-04",
            "gender": "F",
            "mobile_number": "9000111222",
            "age": 30,
            "health_records": [
                {
                    "date": "2026-01-05",
                    "facility": "Skin & Aesthetics Center",
                    "doctor": "Dr. Nivedita Das",
                    "diagnosis": "Contact Dermatitis",
                    "prescription": "Hydrocortisone cream 1% topical BD x 7 days."
                }
            ]
        },
        {
            "abha_number": "91-9876-5432-1098",
            "abha_address": "rahul.verma@abdm",
            "full_name": "Rahul Verma",
            "date_of_birth": "2001-09-18",
            "gender": "M",
            "mobile_number": "9444555666",
            "age": 24,
            "health_records": [
                {
                    "date": "2025-11-14",
                    "facility": "Apollo Clinic",
                    "doctor": "Dr. Manish Gupta",
                    "diagnosis": "Acute Viral Pharyngitis",
                    "prescription": "Syp Cough Linctus 10ml TDS, Warm saline gargles."
                }
            ]
        }
    ]

    for pat in mock_patients:
        # Seed ABHA Central Registry
        with get_abha_connection() as conn:
            conn.execute(
                "INSERT INTO patients (abha_number, abha_address, full_name, date_of_birth, gender, mobile_number, health_records) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (pat["abha_number"], pat["abha_address"], pat["full_name"], pat["date_of_birth"], pat["gender"], pat["mobile_number"], json.dumps(pat["health_records"]))
            )
        
        # Seed Local Hospital Registry
        with get_hospital_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO patients (name, abha_number, age, gender, mobile) VALUES (?, ?, ?, ?, ?)",
                (pat["full_name"], pat["abha_number"], pat["age"], pat["gender"], pat["mobile_number"])
            )
            patient_id = cursor.lastrowid
            
            # Seed an initial encounter log for testing
            for record in pat["health_records"]:
                # Map diagnosis/notes to symptoms/clinical summary
                symptoms = "Consultation for " + record["diagnosis"]
                summary = record.get("prescription", "") or record.get("notes", "")
                cursor.execute(
                    "INSERT INTO encounters (patient_id, date, token_number, department, symptoms, priority, clinical_summary) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (patient_id, record["date"], "PREV-TOK", "Outpatient", symptoms, "NORMAL", summary)
                )

        # Seed Biometric RAYA Database with a mock 128-D L2-normalized vector
        vec = np.random.randn(128)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        blob = serialize_vector(vec.tolist())
        with get_raya_connection() as conn:
            conn.execute(
                "INSERT INTO raya_users (full_name, face_encoding, abha_number) VALUES (?, ?, ?)",
                (pat["full_name"], blob, pat["abha_number"])
            )

    print("Databases initialized and seeded successfully.")

if __name__ == "__main__":
    seed_databases()
