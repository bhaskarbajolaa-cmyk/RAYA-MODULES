import random
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.core.database import get_raya_db
from sqlalchemy import Column, Integer, String, DateTime
from app.models.domain import Base

router = APIRouter()

# --- Define the Model dynamically here for simplicity, or we can move it to domain.py ---
class TokenModel(Base):
    __tablename__ = "hospital_tokens"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    token_number = Column(String, unique=True, index=True)
    department = Column(String, nullable=False)
    patient_name = Column(String, nullable=False)
    abha_number = Column(String, nullable=True)
    status = Column(String, default="WAITING") # WAITING, IN_PROGRESS, COMPLETED
    created_at = Column(DateTime, default=datetime.utcnow)

# Ensure the table is created
from app.core.database import raya_engine
Base.metadata.create_all(bind=raya_engine)

class TokenCreateRequest(BaseModel):
    patient_name: str
    symptoms: str
    abha_number: Optional[str] = None

class TokenResponse(BaseModel):
    token_number: str
    department: str
    patient_name: str
    queue_position: int
    estimated_wait_minutes: int
    status: str

def classify_symptoms(symptoms: str) -> str:
    symptoms = symptoms.lower()
    
    # Direct Department matches (e.g. when passed from Touch UI)
    valid_depts = ["cardiology", "orthopaedics", "ophthalmology", "dermatology", "pediatrics", "general medicine"]
    for dept in valid_depts:
        if dept in symptoms:
            return dept.title() if dept != "general medicine" else "General Medicine"

    # Symptom-based matches
    if any(word in symptoms for word in ['heart', 'chest pain', 'bp', 'blood pressure']):
        return "Cardiology"
    if any(word in symptoms for word in ['bone', 'fracture', 'joint', 'knee', 'back pain']):
        return "Orthopaedics"
    if any(word in symptoms for word in ['eye', 'vision', 'blur']):
        return "Ophthalmology"
    if any(word in symptoms for word in ['skin', 'rash', 'itch', 'acne']):
        return "Dermatology"
    if any(word in symptoms for word in ['child', 'baby', 'fever child']):
        return "Pediatrics"
        
    return "General Medicine"

def check_emergency(symptoms: str) -> bool:
    symptoms = symptoms.lower()
    emergencies = ['heart attack', 'breath', 'unconscious', 'stroke', 'severe bleeding', 'accident']
    return any(word in symptoms for word in emergencies)

@router.post("/generate", response_model=TokenResponse)
def generate_token(req: TokenCreateRequest, db: Session = Depends(get_raya_db)):
    if check_emergency(req.symptoms):
        raise HTTPException(
            status_code=400, 
            detail="EMERGENCY_DETECTED: Please proceed immediately to the Emergency Room."
        )
        
    department = classify_symptoms(req.symptoms)
    
    token_num = f"TK-{department[:3].upper()}-{random.randint(1000, 9999)}"
    
    new_token = TokenModel(
        token_number=token_num,
        department=department,
        patient_name=req.patient_name,
        abha_number=req.abha_number
    )
    
    db.add(new_token)
    db.commit()
    db.refresh(new_token)
    
    # Calculate queue position
    queue_pos = db.query(TokenModel).filter(
        TokenModel.department == department,
        TokenModel.status == "WAITING"
    ).count()
    
    return TokenResponse(
        token_number=token_num,
        department=department,
        patient_name=req.patient_name,
        queue_position=queue_pos,
        estimated_wait_minutes=queue_pos * 15, # 15 mins per patient
        status="WAITING"
    )

@router.get("/queue", response_model=List[TokenResponse])
def get_queue(db: Session = Depends(get_raya_db)):
    tokens = db.query(TokenModel).filter(TokenModel.status == "WAITING").all()
    res = []
    for t in tokens:
        res.append(TokenResponse(
            token_number=t.token_number,
            department=t.department,
            patient_name=t.patient_name,
            queue_position=0,
            estimated_wait_minutes=0,
            status=t.status
        ))
    return res

@router.put("/queue/{token_number}/complete", response_model=TokenResponse)
def complete_token(token_number: str, db: Session = Depends(get_raya_db)):
    token = db.query(TokenModel).filter(TokenModel.token_number == token_number).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    token.status = "COMPLETED"
    db.commit()
    db.refresh(token)
    
    return TokenResponse(
        token_number=token.token_number,
        department=token.department,
        patient_name=token.patient_name,
        queue_position=0,
        estimated_wait_minutes=0,
        status=token.status
    )

@router.delete("/queue/{token_number}")
def delete_token(token_number: str, db: Session = Depends(get_raya_db)):
    token = db.query(TokenModel).filter(TokenModel.token_number == token_number).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    db.delete(token)
    db.commit()
    return {"message": "Token deleted successfully"}
