from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_raya_db
from app.models import domain, schemas
from typing import List

router = APIRouter()

@router.post("/", response_model=schemas.RayaUserResponse)
def create_user(user: schemas.RayaUserCreate, db: Session = Depends(get_raya_db)):
    # Face encoding is placeholder for now (128 zeros as a byte string)
    import numpy as np
    placeholder_encoding = np.zeros(128, dtype=np.float32).tobytes()
    
    db_user = domain.RayaUserModel(
        full_name=user.full_name,
        abha_number=user.abha_number,
        face_encoding=placeholder_encoding
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/", response_model=List[schemas.RayaUserResponse])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_raya_db)):
    users = db.query(domain.RayaUserModel).offset(skip).limit(limit).all()
    return users

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_raya_db)):
    user = db.query(domain.RayaUserModel).filter(domain.RayaUserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}
