import random
import json
from typing import Dict, Any, Optional, List
from database import get_abha_connection

class ABHAClient:
    """
    Simulates the ABDM (Ayushman Bharat Digital Mission) health registry API client.
    """
    def __init__(self):
        pass

    def get_patient_profile(self, abha_number: str) -> Optional[Dict[str, Any]]:
        """
        Fetches patient demographics from central registry using 14-digit ABHA ID.
        """
        # Remove dashes for simple length validation
        clean_num = abha_number.replace("-", "").strip()
        if len(clean_num) != 14 or not clean_num.isdigit():
            raise ValueError("ABHA number must be exactly 14 digits (format: XX-XXXX-XXXX-XXXX).")
        
        with get_abha_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patients WHERE abha_number = ?", (abha_number,))
            row = cursor.fetchone()
            if row:
                record = dict(row)
                record["health_records"] = json.loads(record["health_records"])
                return record
        return None

    def get_patient_profile_by_address(self, abha_address: str) -> Optional[Dict[str, Any]]:
        """
        Fetches patient profile using virtual health address (e.g. name@abdm).
        """
        if "@" not in abha_address:
            raise ValueError("ABHA address must contain '@' (e.g. username@abdm).")
        
        with get_abha_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patients WHERE abha_address = ?", (abha_address,))
            row = cursor.fetchone()
            if row:
                record = dict(row)
                record["health_records"] = json.loads(record["health_records"])
                return record
        return None

    def register_new_abha(
        self,
        full_name: str,
        date_of_birth: str,
        gender: str,
        mobile_number: str,
        preferred_address_prefix: str
    ) -> Dict[str, Any]:
        """
        Registers a new profile on the simulated central ABHA registry.
        """
        # Generate random 14-digit ABHA number
        part1 = f"{random.randint(10, 99)}"
        part2 = f"{random.randint(1000, 9999)}"
        part3 = f"{random.randint(1000, 9999)}"
        part4 = f"{random.randint(1000, 9999)}"
        abha_number = f"{part1}-{part2}-{part3}-{part4}"
        
        prefix = preferred_address_prefix.lower().replace(" ", "_")
        abha_address = f"{prefix}@abdm"
        
        # Verify unique address
        existing = self.get_patient_profile_by_address(abha_address)
        if existing:
            abha_address = f"{prefix}{random.randint(100, 999)}@abdm"
            
        with get_abha_connection() as conn:
            conn.execute(
                """
                INSERT INTO patients (abha_number, abha_address, full_name, date_of_birth, gender, mobile_number, health_records)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (abha_number, abha_address, full_name, date_of_birth, gender, mobile_number, json.dumps([]))
            )
            conn.commit()
            
        return {
            "abha_number": abha_number,
            "abha_address": abha_address,
            "full_name": full_name,
            "date_of_birth": date_of_birth,
            "gender": gender,
            "mobile_number": mobile_number
        }
