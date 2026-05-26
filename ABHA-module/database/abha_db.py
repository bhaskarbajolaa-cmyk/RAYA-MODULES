import json
from typing import Dict, Any, Optional, List
from database.connection import get_connection

# Path to the simulated central ABHA database
ABHA_DB_PATH = "abha.db"

def init_abha_db() -> None:
    """
    Initializes the ABHA database schema.
    """
    conn = get_connection(ABHA_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            abha_number TEXT PRIMARY KEY,
            abha_address TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            date_of_birth TEXT NOT NULL,
            gender TEXT NOT NULL,
            mobile_number TEXT NOT NULL,
            health_records TEXT NOT NULL -- Stores health records as JSON string
        )
    """)
    
    conn.commit()
    conn.close()

def clear_abha_db() -> None:
    """
    Clears all records from the ABHA database.
    """
    conn = get_connection(ABHA_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS patients")
    conn.commit()
    conn.close()

def insert_patient(
    abha_number: str,
    abha_address: str,
    full_name: str,
    date_of_birth: str,
    gender: str,
    mobile_number: str,
    health_records: List[Dict[str, Any]]
) -> None:
    """
    Inserts a new patient record into the ABHA database.
    """
    conn = get_connection(ABHA_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        """
        INSERT OR REPLACE INTO patients (
            abha_number, abha_address, full_name, date_of_birth, gender, mobile_number, health_records
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            abha_number,
            abha_address,
            full_name,
            date_of_birth,
            gender,
            mobile_number,
            json.dumps(health_records)
        )
    )
    
    conn.commit()
    conn.close()

def get_patient_by_abha_number(abha_number: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a patient record by their 14-digit ABHA number.
    """
    conn = get_connection(ABHA_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM patients WHERE abha_number = ?", (abha_number,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        record = dict(row)
        record["health_records"] = json.loads(record["health_records"])
        return record
    return None

def get_patient_by_abha_address(abha_address: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a patient record by their virtual ABHA address (e.g. name@abdm).
    """
    conn = get_connection(ABHA_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM patients WHERE abha_address = ?", (abha_address,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        record = dict(row)
        record["health_records"] = json.loads(record["health_records"])
        return record
    return None

def seed_abha_db() -> None:
    """
    Seeds the ABHA database with sample patient profiles.
    """
    init_abha_db()
    
    # 5 Mock Patient Records
    patients = [
        {
            "abha_number": "91-1111-2222-3333",
            "abha_address": "suresh.kumar@abdm",
            "full_name": "Suresh Kumar",
            "date_of_birth": "1985-05-12",
            "gender": "M",
            "mobile_number": "9876543210",
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
    
    for pat in patients:
        insert_patient(
            pat["abha_number"],
            pat["abha_address"],
            pat["full_name"],
            pat["date_of_birth"],
            pat["gender"],
            pat["mobile_number"],
            pat["health_records"]
        )
