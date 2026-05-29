import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_raya_db, get_abha_db
from app.models import domain
from app.services.biometrics import biometrics

router = APIRouter()

class FaceMatchRequest(BaseModel):
    image_base64: str

class FaceRegisterRequest(BaseModel):
    abha_number: str
    image_base64: str

class FaceMatchResponse(BaseModel):
    match_found: bool
    confidence: float
    patient_name: Optional[str] = None
    abha_number: Optional[str] = None

@router.post("/match", response_model=FaceMatchResponse)
def match_face(req: FaceMatchRequest, db: Session = Depends(get_raya_db)):
    # 1. Extract embedding
    try:
        img = biometrics.base64_to_image(req.image_base64)
        target_emb = biometrics.extract_embedding(img)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")
        
    if not target_emb:
        return FaceMatchResponse(match_found=False, confidence=0.0)
        
    # 2. Query DB and find nearest neighbor
    users = db.query(domain.RayaUserModel).all()
    best_match = None
    min_dist = 100.0 # High initial distance
    
    # Threshold for accepting a match (tuning required based on actual env)
    MATCH_THRESHOLD = 0.5 
    
    for user in users:
        if user.face_encoding:
            try:
                db_emb = json.loads(user.face_encoding)
                dist = biometrics.calculate_distance(target_emb, db_emb)
                if dist < min_dist:
                    min_dist = dist
                    best_match = user
            except:
                continue
                
    if best_match and min_dist < MATCH_THRESHOLD:
        # Confidence score (inverse of distance roughly mapped to 0-1)
        conf = max(0.0, 1.0 - min_dist)
        return FaceMatchResponse(
            match_found=True,
            confidence=conf,
            patient_name=best_match.full_name,
            abha_number=best_match.abha_number
        )
        
    return FaceMatchResponse(match_found=False, confidence=0.0)

@router.post("/register")
def register_face(req: FaceRegisterRequest, 
                 raya_db: Session = Depends(get_raya_db),
                 abha_db: Session = Depends(get_abha_db)):
    
    # Verify ABHA exists
    patient = abha_db.query(domain.ABHAPatientModel).filter(domain.ABHAPatientModel.abha_number == req.abha_number).first()
    if not patient:
        raise HTTPException(status_code=404, detail="ABHA Number not found")
        
    # Extract Embedding
    try:
        img = biometrics.base64_to_image(req.image_base64)
        emb = biometrics.extract_embedding(img)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")
        
    if not emb:
        raise HTTPException(status_code=400, detail="No face detected in image")
        
    # Check if already registered in RAYA
    existing = raya_db.query(domain.RayaUserModel).filter(domain.RayaUserModel.abha_number == req.abha_number).first()
    
    encoded_emb = json.dumps(emb).encode('utf-8')
    
    if existing:
        existing.face_encoding = encoded_emb
        raya_db.commit()
        return {"message": "Biometric profile updated successfully"}
    else:
        new_user = domain.RayaUserModel(
            abha_number=req.abha_number,
            full_name=patient.full_name,
            face_encoding=encoded_emb
        )
        raya_db.add(new_user)
        raya_db.commit()
        return {"message": "Biometric profile created successfully"}
