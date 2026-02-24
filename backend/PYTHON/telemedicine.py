"""
Telemedicine Service for AOU Marche
Handles video consultations, patient management, and vital signs monitoring
"""

import uuid
import datetime
import json
from typing import Dict, List, Optional
import hashlib
import base64
from cryptography.fernet import Fernet

class TelemedicineService:
    """Core telemedicine service"""
    
    def __init__(self):
        self.patients = {}
        self.visits = {}
        self.vital_signs_history = []
        self.doctors = self._initialize_doctors()
        self.services = self._initialize_services()
        
    def _initialize_doctors(self) -> Dict:
        """Initialize doctor database"""
        return {
            'DR-CARDIO-001': {
                'id': 'DR-CARDIO-001',
                'nome': 'Mario',
                'cognome': 'Bianchi',
                'specializzazione': 'Cardiologia',
                'struttura': 'LANCISI',
                'disponibile': True
            },
            'DR-PED-001': {
                'id': 'DR-PED-001',
                'nome': 'Anna',
                'cognome': 'Verdi',
                'specializzazione': 'Pediatria',
                'struttura': 'SALESI',
                'disponibile': True
            }
        }
    
    def _initialize_services(self) -> Dict:
        """Initialize telemedicine services"""
        return {
            "TV-CARDIO": {
                'code': 'TV-CARDIO',
                'name': 'Visita Cardiologica a Distanza',
                'specialty': 'Cardiologia',
                'tariff': 85.00,
                'duration': 30,
                'location': 'LANCISI'
            },
            "TV-PED": {
                'code': 'TV-PED',
                'name': 'Visita Pediatrica a Distanza',
                'specialty': 'Pediatria',
                'tariff': 75.00,
                'duration': 30,
                'location': 'SALESI'
            }
        }
    
    def register_patient(self, patient_data: Dict) -> str:
        """Register new patient"""
        patient_id = f"P{datetime.datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8]}"
        
        self.patients[patient_id] = {
            'id': patient_id,
            'codice_fiscale': patient_data.get('codice_fiscale', ''),
            'cognome': patient_data['cognome'],
            'nome': patient_data['nome'],
            'data_nascita': patient_data['data_nascita'],
            'sesso': patient_data['sesso'],
            'comune_nascita': patient_data['comune_nascita'],
            'email': patient_data.get('email'),
            'telefono': patient_data.get('telefono'),
            'consensi': {
                'telemedicina': patient_data.get('consenso_telemedicina', False),
                'fse': patient_data.get('consenso_fse', False)
            },
            'patologie_croniche': [],
            'farmaci_attuali': [],
            'allergie': [],
            'registrazione': datetime.datetime.now().isoformat()
        }
        
        return patient_id
    
    def get_patient(self, patient_id: str) -> Optional[Dict]:
        """Get patient by ID"""
        return self.patients.get(patient_id)
    
    def schedule_televisita(self, patient_id: str, doctor_id: str, 
                           service_code: str, scheduled_time: str,
                           priority: str = 'PROGRAMMATO') -> Dict:
        """Schedule a televisita"""
        
        # Check patient consent
        if not self.patients[patient_id]['consensi']['telemedicina']:
            raise Exception("Paziente non ha dato consenso per telemedicina")
        
        service = self.services.get(service_code)
        if not service:
            raise Exception(f"Servizio {service_code} non trovato")
        
        # Calculate end time
        start = datetime.datetime.fromisoformat(scheduled_time)
        end = start + datetime.timedelta(minutes=service['duration'])
        
        visit_id = f"TV-{datetime.datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
        
        # Generate video session
        session_id = self._create_video_session(visit_id, [patient_id, doctor_id])
        
        visit = {
            'id': visit_id,
            'type': 'televisita',
            'service_code': service_code,
            'service_name': service['name'],
            'patient_id': patient_id,
            'doctor_id': doctor_id,
            'doctor_name': self.doctors[doctor_id]['cognome'],
            'scheduled_time': scheduled_time,
            'end_time': end.isoformat(),
            'duration': service['duration'],
            'status': 'PROGRAMMATO',
            'priority': priority,
            'video_session': session_id,
            'clinical_notes': None,
            'prescriptions': [],
            'created_at': datetime.datetime.now().isoformat()
        }
        
        self.visits[visit_id] = visit
        return visit
    
    def _create_video_session(self, visit_id: str, participants: List[str]) -> str:
        """Create WebRTC video session"""
        session_id = str(uuid.uuid4())
        
        # Generate TURN credentials
        turn_cred = self._generate_turn_credential()
        
        return session_id
    
    def _generate_turn_credential(self) -> str:
        """Generate TURN server credential"""
        timestamp = int(datetime.datetime.now().timestamp()) + 86400
        credential = f"{timestamp}:aoumarche"
        return base64.b64encode(credential.encode()).decode()
    
    def get_televisita_join_info(self, visit_id: str, patient_id: str) -> Optional[Dict]:
        """Get video session join information"""
        visit = self.visits.get(visit_id)
        
        if not visit or visit['patient_id'] != patient_id:
            return None
        
        # Generate secure token
        token = hashlib.sha256(f"{visit_id}{patient_id}{datetime.datetime.now().date()}".encode()).hexdigest()[:20]
        
        return {
            'visit_id': visit_id,
            'session_id': visit['video_session'],
            'join_url': f"https://telemedicina.aoumarche.it/join/{visit_id}?token={token}",
            'turn_servers': [
                {
                    'urls': 'turn:turn.aoumarche.it:3478',
                    'username': patient_id,
                    'credential': self._generate_turn_credential()
                }
            ],
            'stun_servers': ['stun:stun.aoumarche.it:3478']
        }
    
    def complete_televisita(self, visit_id: str, clinical_notes: str, 
                           prescriptions: List[Dict] = None) -> Dict:
        """Complete televisita"""
        visit = self.visits.get(visit_id)
        
        if not visit:
            raise Exception("Visita non trovata")
        
        visit['status'] = 'COMPLETATO'
        visit['actual_end'] = datetime.datetime.now().isoformat()
        visit['clinical_notes'] = clinical_notes
        visit['prescriptions'] = prescriptions or []
        
        # Generate report
        report = self._generate_televisita_report(visit_id)
        visit['report'] = report
        
        return visit
    
    def _generate_televisita_report(self, visit_id: str) -> str:
        """Generate PDF report (simplified)"""
        visit = self.visits[visit_id]
        patient = self.patients[visit['patient_id']]
        
        report = f"""
        AZIENDA OSPEDALIERO UNIVERSITARIA DELLE MARCHE
        REPORT DI TELEVISITA
        
        Data: {visit['actual_end']}
        ID Visita: {visit_id}
        
        PAZIENTE:
        Nome: {patient['cognome']} {patient['nome']}
        CF: {patient['codice_fiscale']}
        
        TELEVISITA:
        Servizio: {visit['service_name']}
        Medico: {visit['doctor_name']}
        Durata: {visit['duration']} minuti
        
        NOTE CLINICHE:
        {visit['clinical_notes']}
        
        PRESCRIZIONI:
        {visit['prescriptions']}
        
        Firma digitale: {hashlib.sha256(visit_id.encode()).hexdigest()}
        """
        
        return report
    
    def record_vital_signs(self, vitals: Dict) -> Dict:
        """Record patient vital signs"""
        record = {
            'id': str(uuid.uuid4()),
            'patient_id': vitals['patient_id'],
            'timestamp': datetime.datetime.now().isoformat(),
            'data': {
                'heart_rate': vitals.get('heart_rate'),
                'blood_pressure': {
                    'systolic': vitals.get('blood_pressure_systolic'),
                    'diastolic': vitals.get('blood_pressure_diastolic')
                },
                'oxygen_saturation': vitals.get('oxygen_saturation'),
                'temperature': vitals.get('temperature'),
                'glucose': vitals.get('glucose')
            },
            'device_id': vitals.get('device_id', 'manual_entry')
        }
        
        self.vital_signs_history.append(record)
        
        # Check for alerts
        alerts = self._check_vital_alerts(record['data'])
        if alerts:
            record['alerts'] = alerts
        
        return record
    
    def _check_vital_alerts(self, data: Dict) -> List[Dict]:
        """Check vital signs for alerts"""
        alerts = []
        
        thresholds = {
            'heart_rate': {'min': 50, 'max': 120},
            'blood_pressure_systolic': {'min': 90, 'max': 180},
            'oxygen_saturation': {'min': 92, 'max': 100},
            'temperature': {'min': 35.5, 'max': 38.0}
        }
        
        if data.get('heart_rate'):
            hr = data['heart_rate']
            if hr < thresholds['heart_rate']['min']:
                alerts.append({
                    'type': 'BRADICARDIA',
                    'value': hr,
                    'severity': 'high'
                })
            elif hr > thresholds['heart_rate']['max']:
                alerts.append({
                    'type': 'TACHICARDIA',
                    'value': hr,
                    'severity': 'high'
                })
        
        if data.get('oxygen_saturation'):
            spo2 = data['oxygen_saturation']
            if spo2 < thresholds['oxygen_saturation']['min']:
                alerts.append({
                    'type': 'IPOSSIA',
                    'value': spo2,
                    'severity': 'critical'
                })
        
        return alerts
    
    def get_vital_signs_history(self, patient_id: str, days: int = 7) -> List[Dict]:
        """Get patient vital signs history"""
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        
        history = []
        for record in self.vital_signs_history:
            if record['patient_id'] == patient_id:
                record_time = datetime.datetime.fromisoformat(record['timestamp'])
                if record_time >= cutoff:
                    history.append(record)
        
        return history
    
    def get_latest_vitals(self, patient_id: str) -> Optional[Dict]:
        """Get latest vital signs for patient"""
        patient_records = [r for r in self.vital_signs_history if r['patient_id'] == patient_id]
        if patient_records:
            return sorted(patient_records, key=lambda x: x['timestamp'], reverse=True)[0]
        return None
    
    def get_active_patients(self) -> List[Dict]:
        """Get list of active patients for doctor dashboard"""
        active = []
        for patient_id, patient in self.patients.items():
            # Get latest vital signs
            latest_vitals = self.get_latest_vitals(patient_id)
            
            # Get upcoming visits
            upcoming = [v for v in self.visits.values() 
                       if v['patient_id'] == patient_id and v['status'] == 'PROGRAMMATO']
            
            active.append({
                'id': patient_id,
                'nome': f"{patient['cognome']} {patient['nome']}",
                'codice_fiscale': patient['codice_fiscale'],
                'latest_vitals': latest_vitals,
                'upcoming_visits': len(upcoming),
                'has_alerts': latest_vitals.get('alerts') if latest_vitals else False
            })
        
        return active