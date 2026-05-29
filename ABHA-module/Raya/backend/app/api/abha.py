import random
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_abha_db
from app.models import domain
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

router = APIRouter()

class ABHARegisterRequest(BaseModel):
    full_name: str
    aadhaar_number: str
    gender: str
    mobile_number: str
    preferred_address_prefix: str

class ABHAProfileResponse(BaseModel):
    abha_number: str
    abha_address: str
    full_name: str
    aadhaar_number: str
    gender: str
    mobile_number: str
    
class ConsentRequest(BaseModel):
    abha_number: str
    consent_id: str

@router.get("/profile/{abha_number}", response_model=ABHAProfileResponse)
def get_patient_profile(abha_number: str, db: Session = Depends(get_abha_db)):
    clean_num = abha_number.replace("-", "").strip()
    if len(clean_num) != 14 or not clean_num.isdigit():
        raise HTTPException(status_code=400, detail="ABHA number must be exactly 14 digits.")
        
    patient = db.query(domain.ABHAPatientModel).filter(domain.ABHAPatientModel.abha_number == abha_number).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    return patient

@router.get("/profile/address/{abha_address}", response_model=ABHAProfileResponse)
def get_patient_profile_by_address(abha_address: str, db: Session = Depends(get_abha_db)):
    if "@" not in abha_address:
        raise HTTPException(status_code=400, detail="Invalid ABHA address format.")
        
    patient = db.query(domain.ABHAPatientModel).filter(domain.ABHAPatientModel.abha_address == abha_address).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    return patient

@router.post("/register", response_model=ABHAProfileResponse)
def register_new_abha(req: ABHARegisterRequest, db: Session = Depends(get_abha_db)):
    part1 = f"{random.randint(10, 99)}"
    part2 = f"{random.randint(1000, 9999)}"
    part3 = f"{random.randint(1000, 9999)}"
    part4 = f"{random.randint(1000, 9999)}"
    
    abha_number = f"{part1}-{part2}-{part3}-{part4}"
    base_address = req.preferred_address_prefix.lower().replace(' ', '_')
    abha_address = f"{base_address}@abdm"
    
    existing = db.query(domain.ABHAPatientModel).filter(domain.ABHAPatientModel.abha_address == abha_address).first()
    if existing:
        abha_address = f"{base_address}{random.randint(100, 999)}@abdm"

    new_patient = domain.ABHAPatientModel(
        abha_number=abha_number,
        abha_address=abha_address,
        full_name=req.full_name,
        aadhaar_number=req.aadhaar_number,
        gender=req.gender,
        mobile_number=req.mobile_number,
        health_records=json.dumps([])
    )
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return new_patient

@router.post("/consent")
def verify_consent_and_fetch_records(req: ConsentRequest, db: Session = Depends(get_abha_db)):
    patient = db.query(domain.ABHAPatientModel).filter(domain.ABHAPatientModel.abha_number == req.abha_number).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Simulate consent approval
    records = json.loads(patient.health_records) if patient.health_records else []
    return {"status": "CONSENT_GRANTED", "records": records}
