"""
Main entry point for AOU Marche HIS Backend
FastAPI-based REST API server - DEVELOPMENT VERSION (SSL disabled)
"""

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
from typing import List, Dict, Optional
import jwt
import datetime
from pydantic import BaseModel, Field
import asyncio
import json
import os

# Import our modules
from telemedicine import TelemedicineService
from ai_triage import AITriageSystem
from emergency_integration import EmergencyService

# ============================================================================
# DATA MODELS (Pydantic)
# ============================================================================

class PatientRegistration(BaseModel):
    cognome: str
    nome: str
    sesso: str
    data_nascita: str
    comune_nascita: str
    codice_fiscale: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    consenso_telemedicina: bool = False
    consenso_fse: bool = False

class TelevisitaRequest(BaseModel):
    patient_id: str
    doctor_id: str
    service_code: str
    scheduled_time: str
    priority: str = "PROGRAMMATO"

class VitalSignsRecord(BaseModel):
    patient_id: str
    heart_rate: Optional[int] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    oxygen_saturation: Optional[float] = None
    temperature: Optional[float] = None
    glucose: Optional[float] = None
    device_id: Optional[str] = None

class EmergencyRequest(BaseModel):
    patient_id: str
    location: Dict[str, float]
    symptoms: List[str]
    caller_phone: Optional[str] = None

# ============================================================================
# FASTAPI APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title="AOU Marche HIS - Telemedicine Platform",
    description="Integrated Hospital Information System for AOU Marche, Ancona",
    version="2.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware - Updated for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)  # Don't auto-error for development
JWT_SECRET = "aou_marche_super_secret_key_2026"
JWT_ALGORITHM = "HS256"

# Initialize services
telemedicine = TelemedicineService()
ai_triage = AITriageSystem()
emergency = EmergencyService()

# Active WebSocket connections
active_connections: Dict[str, List[WebSocket]] = {
    "doctors": [],
    "emergency": [],
    "patients": {}
}

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/auth/spid")
async def auth_with_spid(spid_token: str):
    """Authenticate with SPID (Italian Public Digital Identity)"""
    try:
        # For development, return mock data
        user_data = {
            "codice_fiscale": "RSSMRA80A01A271X",
            "nome": "Mario",
            "cognome": "Rossi",
            "email": "mario.rossi@email.it"
        }
        
        # Generate JWT
        token = jwt.encode({
            "user": user_data,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        }, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        return {"access_token": token, "token_type": "bearer", "user": user_data}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"SPID authentication failed: {str(e)}")

@app.post("/api/auth/cie")
async def auth_with_cie(cie_data: Dict):
    """Authenticate with CIE (Electronic Identity Card)"""
    # For development, return mock success
    return {"message": "CIE authentication successful (development mode)"}

# ============================================================================
# PATIENT MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/patients/register")
async def register_patient(patient: PatientRegistration):
    """Register new patient in the system"""
    try:
        patient_id = telemedicine.register_patient(patient.dict())
        return {"patient_id": patient_id, "status": "registered", "message": "Patient registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/patients/{patient_id}")
async def get_patient(patient_id: str):
    """Get patient information"""
    patient = telemedicine.get_patient(patient_id)
    if not patient:
        # Return mock data for development
        return {
            "id": patient_id,
            "nome": "Mario",
            "cognome": "Rossi",
            "codice_fiscale": "RSSMRA80A01A271X",
            "data_nascita": "1980-01-01",
            "message": "Mock patient data (development mode)"
        }
    return patient

@app.get("/api/patients")
async def get_all_patients():
    """Get all patients (for testing)"""
    patients = telemedicine.get_active_patients()
    if not patients:
        # Return mock data for development
        return {
            "patients": [
                {"id": "1", "nome": "Mario Rossi", "triage": "ROSSO", "hr": 115, "spo2": 91},
                {"id": "2", "nome": "Giuseppe Verdi", "triage": "GIALLO", "hr": 98, "spo2": 94},
                {"id": "3", "nome": "Anna Bianchi", "triage": "VERDE", "hr": 72, "spo2": 98}
            ]
        }
    return {"patients": patients}

# ============================================================================
# TELEMEDICINE ENDPOINTS
# ============================================================================

@app.post("/api/televisita/schedule")
async def schedule_televisita(request: TelevisitaRequest):
    """Schedule a televisita (video consultation)"""
    try:
        visit = telemedicine.schedule_televisita(
            patient_id=request.patient_id,
            doctor_id=request.doctor_id,
            service_code=request.service_code,
            scheduled_time=request.scheduled_time,
            priority=request.priority
        )
        return visit
    except Exception as e:
        # Return mock data for development
        return {
            "id": f"TV-{datetime.datetime.now().strftime('%Y%m%d')}-TEST",
            "status": "PROGRAMMATO",
            "patient_id": request.patient_id,
            "doctor_id": request.doctor_id,
            "scheduled_time": request.scheduled_time,
            "message": "Televisita scheduled (development mode)",
            "join_url": f"http://localhost:3000/join?visit_id=TEST&patient_id={request.patient_id}"
        }

@app.get("/api/televisita/{visit_id}/join")
async def get_televisita_join_info(visit_id: str, patient_id: str):
    """Get video session join information"""
    join_info = telemedicine.get_televisita_join_info(visit_id, patient_id)
    if not join_info:
        # Return mock data for development
        return {
            "visit_id": visit_id,
            "session_id": "test-session-123",
            "join_url": f"http://localhost:3000/video-call?visit_id={visit_id}&patient_id={patient_id}",
            "turn_servers": [
                {
                    "urls": "turn:localhost:3478",
                    "username": "test",
                    "credential": "test"
                }
            ],
            "stun_servers": ["stun:localhost:3478"]
        }
    return join_info

@app.post("/api/televisita/{visit_id}/complete")
async def complete_televisita(visit_id: str, clinical_notes: str, prescriptions: List[Dict] = None):
    """Complete televisita and generate clinical documentation"""
    try:
        result = telemedicine.complete_televisita(visit_id, clinical_notes, prescriptions)
        return result
    except Exception as e:
        # Return mock data for development
        return {
            "id": visit_id,
            "status": "COMPLETATO",
            "clinical_notes": clinical_notes,
            "prescriptions": prescriptions or [],
            "message": "Televisita completed (development mode)"
        }

# ============================================================================
# VITAL SIGNS MONITORING ENDPOINTS
# ============================================================================

@app.post("/api/vitals/record")
async def record_vital_signs(vitals: VitalSignsRecord):
    """Record vital signs from patient (mobile app or medical devices)"""
    try:
        result = telemedicine.record_vital_signs(vitals.dict())
        
        # Check for AI triage alerts
        if result.get('alerts'):
            # Send real-time alert via WebSocket
            await notify_doctor(vitals.patient_id, result['alerts'])
        
        return result
    except Exception as e:
        # Return mock data for development
        return {
            "id": f"vital-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
            "patient_id": vitals.patient_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "data": vitals.dict(),
            "message": "Vital signs recorded (development mode)"
        }

@app.get("/api/vitals/{patient_id}/history")
async def get_vital_signs_history(patient_id: str, days: int = 7):
    """Get patient vital signs history"""
    try:
        history = telemedicine.get_vital_signs_history(patient_id, days)
        return {"patient_id": patient_id, "history": history}
    except Exception as e:
        # Return mock data for development
        return {
            "patient_id": patient_id,
            "history": [
                {
                    "timestamp": (datetime.datetime.now() - datetime.timedelta(hours=2)).isoformat(),
                    "data": {"heart_rate": 72, "blood_pressure": {"systolic": 120, "diastolic": 80}}
                },
                {
                    "timestamp": (datetime.datetime.now() - datetime.timedelta(hours=4)).isoformat(),
                    "data": {"heart_rate": 75, "blood_pressure": {"systolic": 118, "diastolic": 78}}
                }
            ]
        }

# ============================================================================
# AI TRIAGE ENDPOINTS
# ============================================================================

@app.post("/api/triage/analyze")
async def analyze_symptoms(patient_id: str, symptoms: List[str], vital_signs: Dict = None):
    """AI-powered symptom analysis and triage"""
    try:
        # Get patient medical history
        patient = telemedicine.get_patient(patient_id)
        medical_history = patient.get('patologie_croniche', []) if patient else []
        
        # Perform AI triage
        triage_result = ai_triage.perform_triage(
            patient_id=patient_id,
            symptoms=symptoms,
            vital_signs=vital_signs or {},
            medical_history=medical_history
        )
        
        # If critical, automatically notify emergency
        if triage_result['triage_level'] in ['CODICE_ROSSO', 'CODICE_GIALLO']:
            await notify_emergency(patient_id, triage_result)
        
        return triage_result
    except Exception as e:
        # Return mock triage for development
        risk_score = 85 if 'chest_pain' in symptoms else 45
        triage_level = 'CODICE_ROSSO' if risk_score > 80 else 'CODICE_GIALLO' if risk_score > 60 else 'CODICE_VERDE'
        
        return {
            "session_id": f"triage-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
            "patient_id": patient_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "triage_level": triage_level,
            "triage_details": {
                "priority": 1 if triage_level == 'CODICE_ROSSO' else 2,
                "color": "#ff0000" if triage_level == 'CODICE_ROSSO' else "#ffff00",
                "description": "Emergenza - Pericolo di vita immediato" if triage_level == 'CODICE_ROSSO' else "Urgenza - Potenziale pericolo di vita"
            },
            "risk_score": risk_score,
            "symptoms_analyzed": symptoms,
            "vital_signs": vital_signs or {},
            "recommendations": [
                "🚨 Attivare immediatamente codice emergenza" if triage_level == 'CODICE_ROSSO' else "🚑 Trasporto in Pronto Soccorso entro 15 minuti",
                "Monitoraggio continuo parametri vitali",
                "Eseguire ECG appena possibile" if 'chest_pain' in symptoms else "Controllare parametri ogni 5 minuti"
            ],
            "requires_immediate_action": triage_level in ['CODICE_ROSSO', 'CODICE_GIALLO']
        }

@app.post("/api/triage/decision-support")
async def clinical_decision_support(patient_id: str, diagnosis: str, vital_signs: Dict, lab_results: Dict = None):
    """Get clinical decision support for doctors"""
    try:
        decision = ai_triage.clinical_decision_support(
            patient_id=patient_id,
            diagnosis=diagnosis,
            vital_signs=vital_signs,
            lab_results=lab_results
        )
        return decision
    except Exception as e:
        # Return mock decision support for development
        return {
            "id": f"decision-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
            "patient_id": patient_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "diagnosis": diagnosis,
            "vital_signs": vital_signs,
            "lab_results": lab_results or {},
            "alerts": [
                {
                    "type": "INFO",
                    "severity": "low",
                    "message": "Clinical decision support in development mode"
                }
            ],
            "guidelines": ["Linee Guida Nazionali Italiane (Development Mode)"]
        }

# ============================================================================
# EMERGENCY INTEGRATION ENDPOINTS
# ============================================================================

@app.post("/api/emergency/call")
async def initiate_emergency(request: EmergencyRequest):
    """Initiate emergency call to 118"""
    try:
        # Get patient data
        patient = telemedicine.get_patient(request.patient_id)
        
        # Perform AI triage first
        triage = ai_triage.perform_triage(
            patient_id=request.patient_id,
            symptoms=request.symptoms,
            vital_signs={},
            medical_history=patient.get('patologie_croniche', []) if patient else []
        )
        
        # Initiate emergency call
        emergency_call = emergency.initiate_emergency_call(
            patient_id=request.patient_id,
            location=request.location,
            emergency_type=determine_emergency_type(request.symptoms),
            triage_level=triage['triage_level'],
            patient_data=patient
        )
        
        # Dispatch ambulance automatically for red codes
        if triage['triage_level'] == 'CODICE_ROSSO':
            dispatch = emergency.dispatch_ambulance(emergency_call['id'])
            emergency_call['dispatch'] = dispatch
            
            # Notify patient via WebSocket if connected
            await notify_patient(request.patient_id, {
                'type': 'ambulance_dispatched',
                'eta': dispatch['eta_minutes'],
                'dispatch_id': dispatch['id']
            })
        
        return emergency_call
    except Exception as e:
        # Return mock emergency response for development
        return {
            "id": f"EMS-{datetime.datetime.now().strftime('%Y%m%d')}-TEST",
            "patient_id": request.patient_id,
            "emergency_type": determine_emergency_type(request.symptoms),
            "triage_level": "CODICE_ROSSO" if 'chest_pain' in request.symptoms else "CODICE_GIALLO",
            "location": request.location,
            "status": "initiated",
            "timestamp": datetime.datetime.now().isoformat(),
            "ambulance_dispatched": True,
            "dispatch": {
                "id": f"DSP-{datetime.datetime.now().strftime('%Y%m%d')}-TEST",
                "eta_minutes": 8,
                "ambulance_id": "AMB-001",
                "crew": ["autista", "infermiere", "rianimatore"]
            },
            "message": "Emergency call initiated (development mode)"
        }

@app.get("/api/emergency/track/{dispatch_id}")
async def track_ambulance(dispatch_id: str):
    """Track ambulance in real-time"""
    try:
        tracking = emergency.track_ambulance(dispatch_id)
        return tracking
    except Exception as e:
        # Return mock tracking for development
        return {
            "dispatch_id": dispatch_id,
            "ambulance_id": "AMB-001",
            "current_location": {"lat": 43.6050, "lon": 13.5250},
            "progress_percentage": 45,
            "remaining_minutes": 4,
            "estimated_arrival": (datetime.datetime.now() + datetime.timedelta(minutes=4)).isoformat(),
            "status": "en_route",
            "speed_kmh": 65
        }

@app.post("/api/emergency/ambulance/{dispatch_id}/status")
async def update_ambulance_status(dispatch_id: str, status: str, clinical_update: Dict = None):
    """Update ambulance status during transport"""
    try:
        updated = emergency.update_ambulance_status(dispatch_id, status, clinical_update)
        return updated
    except Exception as e:
        return {
            "dispatch_id": dispatch_id,
            "status": status,
            "updated": True,
            "timestamp": datetime.datetime.now().isoformat(),
            "message": "Ambulance status updated (development mode)"
        }

# ============================================================================
# WEBSOCKET CONNECTIONS (Real-time updates)
# ============================================================================

@app.websocket("/ws/doctor/{doctor_id}")
async def doctor_websocket_endpoint(websocket: WebSocket, doctor_id: str):
    """WebSocket connection for doctors (real-time patient updates)"""
    await websocket.accept()
    active_connections["doctors"].append(websocket)
    
    try:
        # Send initial data
        await websocket.send_json({
            'type': 'connection_established',
            'message': f'Connected as doctor {doctor_id}',
            'timestamp': datetime.datetime.now().isoformat()
        })
        
        while True:
            # Receive messages from doctor
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message['type'] == 'request_patient_list':
                patients = telemedicine.get_active_patients()
                if not patients:
                    # Mock data for development
                    patients = [
                        {"id": "1", "nome": "Mario Rossi", "triage": "ROSSO", "hr": 115, "spo2": 91},
                        {"id": "2", "nome": "Giuseppe Verdi", "triage": "GIALLO", "hr": 98, "spo2": 94}
                    ]
                await websocket.send_json({
                    'type': 'patient_list',
                    'data': patients
                })
            elif message['type'] == 'ping':
                await websocket.send_json({'type': 'pong'})
                
    except WebSocketDisconnect:
        active_connections["doctors"].remove(websocket)

@app.websocket("/ws/patient/{patient_id}")
async def patient_websocket_endpoint(websocket: WebSocket, patient_id: str):
    """WebSocket connection for patients (real-time notifications)"""
    await websocket.accept()
    active_connections["patients"][patient_id] = websocket
    
    try:
        await websocket.send_json({
            'type': 'connection_established',
            'message': f'Connected as patient {patient_id}',
            'timestamp': datetime.datetime.now().isoformat()
        })
        
        while True:
            data = await websocket.receive_text()
            # Handle patient messages
            message = json.loads(data)
            if message['type'] == 'ping':
                await websocket.send_json({'type': 'pong'})
                
    except WebSocketDisconnect:
        del active_connections["patients"][patient_id]

@app.websocket("/ws/emergency")
async def emergency_websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for emergency services"""
    await websocket.accept()
    active_connections["emergency"].append(websocket)
    
    try:
        await websocket.send_json({
            'type': 'connection_established',
            'message': 'Connected to emergency services',
            'timestamp': datetime.datetime.now().isoformat()
        })
        
        while True:
            data = await websocket.receive_text()
            # Handle emergency updates
    except WebSocketDisconnect:
        active_connections["emergency"].remove(websocket)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def notify_doctor(patient_id: str, alert: Dict):
    """Send real-time alert to doctors via WebSocket"""
    message = {
        'type': 'patient_alert',
        'patient_id': patient_id,
        'alert': alert,
        'timestamp': datetime.datetime.now().isoformat()
    }
    
    for connection in active_connections["doctors"]:
        try:
            await connection.send_json(message)
        except:
            pass

async def notify_patient(patient_id: str, notification: Dict):
    """Send real-time notification to patient via WebSocket"""
    if patient_id in active_connections["patients"]:
        try:
            await active_connections["patients"][patient_id].send_json(notification)
        except:
            pass

async def notify_emergency(patient_id: str, triage_result: Dict):
    """Notify emergency services of critical patient"""
    message = {
        'type': 'critical_triage',
        'patient_id': patient_id,
        'triage': triage_result,
        'timestamp': datetime.datetime.now().isoformat()
    }
    
    for connection in active_connections["emergency"]:
        try:
            await connection.send_json(message)
        except:
            pass

async def send_patient_vitals(websocket: WebSocket, patient_id: str):
    """Stream patient vital signs in real-time"""
    try:
        while True:
            vitals = telemedicine.get_latest_vitals(patient_id)
            if vitals:
                await websocket.send_json({
                    'type': 'vitals_update',
                    'patient_id': patient_id,
                    'data': vitals
                })
            else:
                # Send mock vitals for development
                await websocket.send_json({
                    'type': 'vitals_update',
                    'patient_id': patient_id,
                    'data': {
                        'heart_rate': 72,
                        'blood_pressure': {'systolic': 120, 'diastolic': 80},
                        'oxygen_saturation': 98
                    }
                })
            await asyncio.sleep(5)  # Update every 5 seconds
    except:
        pass

def determine_emergency_type(symptoms: List[str]) -> str:
    """Determine emergency type from symptoms"""
    emergency_map = {
        'chest_pain': 'CARDIAC_ARREST',
        'difficulty_breathing': 'RESPIRATORY_FAILURE',
        'severe_headache': 'STROKE',
        'abdominal_pain': 'ACUTE_ABDOMEN',
        'seizure': 'CONVULSIONS',
        'severe_bleeding': 'HEMORRHAGE',
        'loss_of_consciousness': 'UNCONSCIOUS'
    }
    
    for symptom in symptoms:
        if symptom in emergency_map:
            return emergency_map[symptom]
    
    return 'GENERIC_EMERGENCY'

# ============================================================================
# ADDITIONAL DEVELOPMENT ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "🏥 AOU Marche HIS is running!",
        "version": "2.1.0",
        "status": "development",
        "endpoints": {
            "docs": "/api/docs",
            "redoc": "/api/redoc",
            "health": "/health",
            "patients": "/api/patients"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.1.0",
        "timestamp": datetime.datetime.now().isoformat(),
        "services": {
            "database": "not connected (development mode)",
            "redis": "not connected (development mode)",
            "websocket": "available"
        }
    }

# ============================================================================
# MAIN ENTRY POINT - FIXED FOR DEVELOPMENT
# ============================================================================

if __name__ == "__main__":
    print("🏥 Starting AOU Marche HIS - Development Mode")
    print("📡 API will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/api/docs")
    print("⚠️  SSL is DISABLED for development")
    print("-" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )