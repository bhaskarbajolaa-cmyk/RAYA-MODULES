import sys
import os

# Add the parent directory to sys.path so we can import 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocalABHA
from app.models.domain import ABHAPatientModel

def seed_data():
    db: Session = SessionLocalABHA()
    try:
        # Check if already seeded
        if db.query(ABHAPatientModel).count() > 0:
            print("Database already seeded.")
            return

        dummy_patients = [
            ABHAPatientModel(
                abha_number="37-8075-1567-1144",
                abha_address="bhaskar@abdm",
                full_name="bhaskar",
                aadhaar_number="123412341234",
                gender="M",
                mobile_number="9876543210",
                health_records="[]"
            ),
            ABHAPatientModel(
                abha_number="90-2833-5978-3226",
                abha_address="john_doe@abdm",
                full_name="John Doe",
                aadhaar_number="987698769876",
                gender="M",
                mobile_number="8765432109",
                health_records="[]"
            )
        ]
        
        db.add_all(dummy_patients)
        db.commit()
        print("Successfully seeded dummy data.")
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
