"""
AOU Marche HIS - Complete Integrated System
With Database, Authentication, and Frontend Integration
"""

# Add the project root to Python path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from typing import List, Optional
import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import local modules
from backend.database.database import engine, get_db, Base
from backend.models.patient import Patient
from backend.models.visit import Visit
from backend.models.vitals import VitalSigns
from backend.auth.auth import (
    authenticate_user, create_access_token, get_current_active_user,
    require_admin, require_doctor, require_nurse, get_current_doctor_id,
    ACCESS_TOKEN_EXPIRE_MINUTES, User
)
from telemedicine import TelemedicineService
from ai_triage import AITriageSystem
from emergency_integration import EmergencyService

# Initialize database
print("📊 Initializing database...")
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables ready")
except Exception as e:
    print(f"⚠️ Database initialization warning: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="AOU Marche HIS - Complete System",
    description="Integrated Hospital Information System with Database & Auth",
    version="3.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
telemedicine = TelemedicineService()
ai_triage = AITriageSystem()
emergency = EmergencyService()

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/auth/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token"""
    user = authenticate_user(None, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "hospital": user.hospital,
            "department": user.department
        }
    }

@app.get("/api/auth/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user info"""
    return {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "hospital": current_user.hospital,
        "department": current_user.department,
        "doctor_id": getattr(current_user, "doctor_id", None)
    }

# ============================================================================
# PATIENT MANAGEMENT ENDPOINTS
# ============================================================================

class PatientCreate(BaseModel):
    cognome: str
    nome: str
    sesso: str
    data_nascita: str
    comune_nascita: str
    codice_fiscale: str
    email: Optional[str] = None
    telefono: str
    consenso_privacy: bool = False

@app.post("/api/patients/register")
async def register_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """Register new patient (doctor only)"""
    try:
        # Check if patient already exists
        existing = db.query(Patient).filter(
            Patient.codice_fiscale == patient.codice_fiscale
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Patient already exists")
        
        # Create new patient
        db_patient = Patient(
            cognome=patient.cognome,
            nome=patient.nome,
            sesso=patient.sesso,
            data_nascita=patient.data_nascita,
            comune_nascita=patient.comune_nascita,
            codice_fiscale=patient.codice_fiscale,
            email=patient.email,
            telefono=patient.telefono,
            consenso_privacy=patient.consenso_privacy
        )
        
        db.add(db_patient)
        db.commit()
        db.refresh(db_patient)
        
        return {
            "id": db_patient.id,
            "cognome": db_patient.cognome,
            "nome": db_patient.nome,
            "codice_fiscale": db_patient.codice_fiscale,
            "message": "Patient registered successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/patients/search")
async def search_patients(
    query: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Search patients by name or CF"""
    try:
        patients = db.query(Patient).filter(
            (Patient.cognome.ilike(f"%{query}%")) |
            (Patient.nome.ilike(f"%{query}%")) |
            (Patient.codice_fiscale.ilike(f"%{query}%"))
        ).limit(20).all()
        
        return [{
            "id": p.id,
            "cognome": p.cognome,
            "nome": p.nome,
            "codice_fiscale": p.codice_fiscale,
            "data_nascita": p.data_nascita,
            "telefono": p.telefono
        } for p in patients]
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get dashboard statistics"""
    total_patients = db.query(Patient).count()
    
    today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0)
    today_end = today_start + datetime.timedelta(days=1)
    today_visits = db.query(Visit).filter(
        Visit.scheduled_time >= today_start,
        Visit.scheduled_time < today_end
    ).count()
    
    return {
        "total_patients": total_patients,
        "today_visits": today_visits,
        "timestamp": datetime.datetime.now().isoformat()
    }

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        db.execute("SELECT 1").first()
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    
    return {
        "status": "healthy",
        "version": "3.0.0",
        "database": db_status,
        "timestamp": datetime.datetime.now().isoformat()
    }

# ============================================================================
# FRONTEND PAGES
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main dashboard"""
    dashboard_path = os.path.abspath("frontend/web/doctor-dashboard.html")
    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r") as f:
            return f.read()
    return HTMLResponse(content=f"<h1>Dashboard not found</h1>")

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🏥 AOU Marche HIS - Complete Integrated System")
    print("=" * 60)
    print("\n📡 Starting server...")
    print("   API: http://localhost:8000")
    print("   Docs: http://localhost:8000/docs")
    print("\n📊 Database: PostgreSQL")
    print("   Database: aoumarche")
    print("\n🔐 Authentication:")
    print("   Admin:    admin@aoumarche.it / Admin@2024")
    print("   Doctor:   dott.rossi@aoumarche.it / Medico@2024")
    print("   Nurse:    infermiere.bianchi@aoumarche.it / Infermiere@2024")
    print("\n" + "=" * 60)
    
    uvicorn.run(
        "main_integrated_fixed:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )