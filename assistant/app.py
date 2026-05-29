import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Add current directory to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from database import init_databases, seed_databases, get_hospital_connection
from abha_client import ABHAClient
from biometric_matcher import BiometricMatcher
from triage_processor import TriageProcessor

# Create FastAPI app
app = FastAPI(title="RAYA AI Receptionist Kiosk")

# Initialize modules
matcher = BiometricMatcher(threshold=0.5)
abha_client = ABHAClient()
triage_processor = TriageProcessor()

# Pydantic Request Models
class FaceScanRequest(BaseModel):
    image: str  # Base64 data URL

class RegisterFaceRequest(BaseModel):
    full_name: str
    face_encoding: List[float]
    abha_number: Optional[str] = None

class ABHASearchRequest(BaseModel):
    abha_id: str  # Can be 14-digit number or name@abdm

class ABHARegisterRequest(BaseModel):
    full_name: str
    date_of_birth: str
    gender: str
    mobile_number: str
    preferred_prefix: str

class TriageRequest(BaseModel):
    abha_number: Optional[str] = None
    patient_name: str
    age: int
    gender: str
    mobile: str
    symptoms: str

# Database helper functions
def get_patient_history(abha_number: str) -> List[Dict[str, Any]]:
    with get_hospital_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT e.date, e.token_number, e.department, e.symptoms, e.priority, e.clinical_summary
            FROM encounters e
            JOIN patients p ON e.patient_id = p.id
            WHERE p.abha_number = ?
            ORDER BY e.id DESC
            """,
            (abha_number,)
        )
        return [dict(row) for row in cursor.fetchall()]

# API Endpoints
@app.post("/api/init-db")
def init_db():
    try:
        seed_databases()
        return {"status": "success", "message": "Databases initialized and seeded successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/face-scan")
def face_scan(payload: FaceScanRequest):
    try:
        image_np = matcher.base64_to_image(payload.image)
        encoding = matcher.extract_face_encoding(image_np)
        
        if encoding is None:
            return {"status": "no_face", "message": "No face detected in snapshot."}
            
        matched_user, distance = matcher.identify_user(encoding)
        
        if matched_user:
            # User recognized! Look up their ABHA number
            abha_num = matched_user["abha_number"]
            profile = None
            history = []
            
            if abha_num:
                profile = abha_client.get_patient_profile(abha_num)
                history = get_patient_history(abha_num)
                
            return {
                "status": "recognized",
                "distance": distance,
                "user": matched_user,
                "abha_profile": profile,
                "history": history
            }
        else:
            return {
                "status": "unrecognized",
                "message": "Face unrecognized.",
                "face_encoding": encoding
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/register-face")
def register_face(payload: RegisterFaceRequest):
    try:
        user_id = matcher.register_user(payload.full_name, payload.face_encoding, payload.abha_number)
        return {"status": "success", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/abha/search")
def search_abha(payload: ABHASearchRequest):
    try:
        # Search by number or address
        if "@" in payload.abha_id:
            profile = abha_client.get_patient_profile_by_address(payload.abha_id)
        else:
            profile = abha_client.get_patient_profile(payload.abha_id)
            
        if profile:
            # Check if this profile has a biometric face registered in raya_users
            is_linked_biometrically = False
            with get_hospital_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM patients WHERE abha_number = ?", (profile["abha_number"],))
                patient_row = cursor.fetchone()
                
            history = []
            if profile["abha_number"]:
                history = get_patient_history(profile["abha_number"])
                
            return {
                "status": "success",
                "found": True,
                "profile": profile,
                "history": history
            }
        else:
            return {"status": "success", "found": False, "message": "ABHA profile not found."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/abha/register")
def register_abha(payload: ABHARegisterRequest):
    try:
        profile = abha_client.register_new_abha(
            full_name=payload.full_name,
            date_of_birth=payload.date_of_birth,
            gender=payload.gender,
            mobile_number=payload.mobile_number,
            preferred_address_prefix=payload.preferred_prefix
        )
        return {"status": "success", "profile": profile}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/triage")
def triage_patient(payload: TriageRequest):
    try:
        result = triage_processor.process_encounter(
            abha_number=payload.abha_number,
            patient_name=payload.patient_name,
            age=payload.age,
            gender=payload.gender,
            mobile=payload.mobile,
            symptoms=payload.symptoms
        )
        return {"status": "success", "triage": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/{abha_number}")
def fetch_history(abha_number: str):
    try:
        history = get_patient_history(abha_number)
        return {"status": "success", "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serving Static Kiosk Files
@app.get("/")
def read_root():
    return RedirectResponse(url="/static/index.html")

# Create static directories if they don't exist
static_path = os.path.join(BASE_DIR, "static")
os.makedirs(static_path, exist_ok=True)
os.makedirs(os.path.join(static_path, "css"), exist_ok=True)
os.makedirs(os.path.join(static_path, "js"), exist_ok=True)

# Mount static folder
app.mount("/static", StaticFiles(directory=static_path), name="static")

if __name__ == "__main__":
    # Initialize databases on start
    init_databases()
    # Run server
    uvicorn.run(app, host="127.0.0.1", port=8000)
