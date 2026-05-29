from sqlalchemy import Column, Integer, String, LargeBinary, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class ABHAPatientModel(Base):
    __tablename__ = "patients"
    
    abha_number = Column(String, primary_key=True, index=True)
    abha_address = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    aadhaar_number = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    mobile_number = Column(String, nullable=False)
    health_records = Column(String, nullable=False) # JSON string

class RayaUserModel(Base):
    __tablename__ = "raya_users"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    full_name = Column(String, nullable=False)
    face_encoding = Column(LargeBinary, nullable=False) # 128-d float vector
    abha_number = Column(String, nullable=True)
    last_checkin = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())
