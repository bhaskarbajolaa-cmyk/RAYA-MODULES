import random
from typing import Dict, Any, Optional, List
from database.abha_db import (
    get_patient_by_abha_number,
    get_patient_by_abha_address,
    insert_patient
)

class ABHAClient:
    """
    Simulates the interface client used by hospitals and applications (like RAYA) 
    to interact with the Central ABHA (Ayushman Bharat Health Account) system.
    In production, this would make secure REST API requests to the ABDM gateway.
    """

    def __init__(self):
        pass

    def get_patient_profile(self, abha_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a patient's demographic profile using their 14-digit ABHA number.
        """
        # Validate format (e.g., 91-XXXX-XXXX-XXXX)
        clean_num = abha_number.replace("-", "").strip()
        if len(clean_num) != 14 or not clean_num.isdigit():
            raise ValueError("ABHA number must be exactly 14 digits.")
            
        return get_patient_by_abha_number(abha_number)

    def get_patient_profile_by_address(self, abha_address: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a patient's demographic profile using their virtual ABHA address (e.g. name@abdm).
        """
        if "@" not in abha_address:
            raise ValueError("Invalid ABHA address format. Must contain '@'.")
        return get_patient_by_abha_address(abha_address)

    def verify_consent_and_fetch_records(self, abha_number: str, consent_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Simulates the ABDM consent flow. If consent is valid (simulated here), 
        fetches the clinical health records for the patient.
        """
        patient = self.get_patient_profile(abha_number)
        if not patient:
            return None
        
        # In a real environment, we would check if consent_id is active and approved.
        # Here we simulate a successful consent check and return the clinical records.
        return patient.get("health_records", [])

    def register_new_abha(
        self,
        full_name: str,
        date_of_birth: str,
        gender: str,
        mobile_number: str,
        preferred_address_prefix: str
    ) -> Dict[str, Any]:
        """
        Simulates registering a new patient into the central ABHA database,
        generating a new 14-digit ABHA number and ABHA address.
        """
        # Generate a random 14-digit number formatted as XX-XXXX-XXXX-XXXX
        part1 = f"{random.randint(10, 99)}"
        part2 = f"{random.randint(1000, 9999)}"
        part3 = f"{random.randint(1000, 9999)}"
        part4 = f"{random.randint(1000, 9999)}"
        
        abha_number = f"{part1}-{part2}-{part3}-{part4}"
        abha_address = f"{preferred_address_prefix.lower().replace(' ', '_')}@abdm"
        
        # Verify uniqueness of address prefix
        existing = get_patient_by_abha_address(abha_address)
        if existing:
            # Add some random numbers to ensure uniqueness
            abha_address = f"{preferred_address_prefix.lower().replace(' ', '_')}{random.randint(100, 999)}@abdm"

        # Initialize with empty health records
        empty_records: List[Dict[str, Any]] = []
        
        insert_patient(
            abha_number=abha_number,
            abha_address=abha_address,
            full_name=full_name,
            date_of_birth=date_of_birth,
            gender=gender,
            mobile_number=mobile_number,
            health_records=empty_records
        )
        
        return {
            "abha_number": abha_number,
            "abha_address": abha_address,
            "full_name": full_name,
            "date_of_birth": date_of_birth,
            "gender": gender,
            "mobile_number": mobile_number
        }
