from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ABHAPatient(BaseModel):
    abha_number: str
    abha_address: str
    full_name: str
    date_of_birth: str
    gender: str
    mobile_number: str
    health_records: str

    class Config:
        from_attributes = True

class RayaUserBase(BaseModel):
    full_name: str
    abha_number: Optional[str] = None

class RayaUserCreate(RayaUserBase):
    pass

class RayaUserResponse(RayaUserBase):
    id: int
    last_checkin: Optional[datetime]
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
