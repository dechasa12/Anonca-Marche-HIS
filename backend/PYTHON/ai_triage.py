"""
AI-Powered Triage and Clinical Decision Support System
Uses machine learning for symptom analysis and risk prediction
"""

import numpy as np
import json
import datetime
import uuid
from typing import Dict, List, Optional, Tuple
from sklearn.ensemble import RandomForestClassifier
import joblib

class AITriageSystem:
    """AI-powered triage and clinical decision support"""
    
    def __init__(self):
        self.triage_sessions = []
        self.decisions = []
        
        # Italian triage levels
        self.triage_levels = {
            'CODICE_ROSSO': {
                'priority': 1,
                'max_wait': 0,
                'color': '#ff0000',
                'description': 'Emergenza - Pericolo di vita immediato'
            },
            'CODICE_GIALLO': {
                'priority': 2,
                'max_wait': 15,
                'color': '#ffff00',
                'description': 'Urgenza - Potenziale pericolo di vita'
            },
            'CODICE_VERDE': {
                'priority': 3,
                'max_wait': 60,
                'color': '#00ff00',
                'description': 'Urgenza minore - Non pericolo di vita'
            },
            'CODICE_BIANCO': {
                'priority': 4,
                'max_wait': 240,
                'color': '#ffffff',
                'description': 'Non urgente - Visita ambulatoriale'
            }
        }
        
        # Symptom risk database
        self.symptom_risk = {
            'chest_pain': 95,
            'difficulty_breathing': 90,
            'severe_headache': 75,
            'loss_of_consciousness': 100,
            'seizure': 95,
            'severe_bleeding': 95,
            'abdominal_pain': 50,
            'fever': 40,
            'cough': 30,
            'fatigue': 20,
            'nausea': 25,
            'vomiting': 35,
            'dizziness': 45,
            'palpitations': 60
        }
        
        # Load pre-trained ML model (simulated)
        self.model = self._load_model()
        
    def _load_model(self):
        """Load pre-trained ML model for triage"""
        # In production: load actual trained model
        # model = joblib.load('models/triage_model.pkl')
        
        # Simulated model for demonstration
        class SimulatedModel:
            def predict_proba(self, features):
                # Simplified prediction logic
                risk_score = sum(features) / len(features)
                return [[risk_score / 100]]
        
        return SimulatedModel()
    
    def perform_triage(self, patient_id: str, symptoms: List[str],
                      vital_signs: Dict, medical_history: List[str] = None) -> Dict:
        """
        Perform AI-powered triage
        Returns triage level and recommendations
        """
        session_id = str(uuid.uuid4())
        
        # Extract features for ML model
        features = self._extract_features(symptoms, vital_signs, medical_history)
        
        # Get ML prediction
        risk_score = self._predict_risk(features)
        
        # Determine triage level
        triage_level = self._determine_triage_level(risk_score, vital_signs, symptoms)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            triage_level, symptoms, vital_signs, medical_history
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(symptoms, vital_signs)
        
        result = {
            'session_id': session_id,
            'patient_id': patient_id,
            'timestamp': datetime.datetime.now().isoformat(),
            'triage_level': triage_level,
            'triage_details': self.triage_levels[triage_level],
            'risk_score': risk_score,
            'symptoms_analyzed': symptoms,
            'vital_signs': vital_signs,
            'recommendations': recommendations,
            'confidence': confidence,
            'requires_immediate_action': triage_level in ['CODICE_ROSSO', 'CODICE_GIALLO']
        }
        
        self.triage_sessions.append(result)
        return result
    
    def _extract_features(self, symptoms: List[str], vital_signs: Dict,
                         medical_history: List[str] = None) -> List[float]:
        """Extract numerical features for ML model"""
        features = []
        
        # Symptom features (one-hot encoding for top symptoms)
        top_symptoms = list(self.symptom_risk.keys())[:10]
        for symptom in top_symptoms:
            features.append(1.0 if symptom in symptoms else 0.0)
        
        # Vital signs features
        features.append(vital_signs.get('heart_rate', 70) / 200)  # Normalize
        features.append(vital_signs.get('blood_pressure_systolic', 120) / 200)
        features.append(vital_signs.get('oxygen_saturation', 98) / 100)
        features.append(vital_signs.get('temperature', 36.5) / 40)
        
        # Medical history features
        if medical_history:
            risk_factors = ['diabetes', 'hypertension', 'heart_disease', 'copd', 'cancer']
            for factor in risk_factors:
                features.append(1.0 if factor in str(medical_history).lower() else 0.0)
        else:
            features.extend([0.0] * 5)
        
        return features
    
    def _predict_risk(self, features: List[float]) -> float:
        """Predict risk score using ML model"""
        # Use ML model for prediction
        features_array = np.array(features).reshape(1, -1)
        risk_score = self.model.predict_proba(features_array)[0][0] * 100
        
        return round(risk_score, 1)
    
    def _determine_triage_level(self, risk_score: float, vital_signs: Dict,
                                symptoms: List[str]) -> str:
        """Determine triage level based on risk score and clinical criteria"""
        
        # Check for critical symptoms
        critical_symptoms = ['loss_of_consciousness', 'seizure', 'severe_bleeding']
        if any(s in critical_symptoms for s in symptoms):
            return 'CODICE_ROSSO'
        
        # Check vital signs for critical values
        if vital_signs:
            spo2 = vital_signs.get('oxygen_saturation', 100)
            if spo2 < 85:
                return 'CODICE_ROSSO'
            
            hr = vital_signs.get('heart_rate', 0)
            if hr > 140 or hr < 40:
                return 'CODICE_ROSSO'
            
            bp_sys = vital_signs.get('blood_pressure_systolic', 0)
            if bp_sys > 200 or bp_sys < 80:
                return 'CODICE_ROSSO'
        
        # Risk score based triage
        if risk_score >= 80:
            return 'CODICE_ROSSO'
        elif risk_score >= 60:
            return 'CODICE_GIALLO'
        elif risk_score >= 30:
            return 'CODICE_VERDE'
        else:
            return 'CODICE_BIANCO'
    
    def _generate_recommendations(self, triage_level: str, symptoms: List[str],
                                  vital_signs: Dict, medical_history: List[str]) -> List[str]:
        """Generate clinical recommendations"""
        recommendations = []
        
        # Base recommendations by triage level
        level_recs = {
            'CODICE_ROSSO': [
                "🚨 Attivare immediatamente codice emergenza",
                "Chiamare 118 per trasporto urgente",
                "Monitoraggio continuo parametri vitali",
                "Preparare materiale per rianimazione"
            ],
            'CODICE_GIALLO': [
                "🚑 Trasporto in Pronto Soccorso entro 15 minuti",
                "Monitoraggio parametri ogni 5 minuti",
                "Contattare medico di base per riferimento"
            ],
            'CODICE_VERDE': [
                "Visita ambulatoriale entro 60 minuti",
                "Controllare parametri vitali ogni 30 minuti",
                "Considerare terapia sintomatica"
            ],
            'CODICE_BIANCO': [
                "Visita ambulatoriale programmabile",
                "Consigliare terapia domiciliare",
                "Fornire istruzioni per monitoraggio"
            ]
        }
        
        recommendations.extend(level_recs.get(triage_level, []))
        
        # Symptom-specific recommendations
        if 'chest_pain' in symptoms:
            recommendations.append("Eseguire ECG appena possibile")
            recommendations.append("Considerare aspirina se non controindicata")
        
        if 'difficulty_breathing' in symptoms:
            recommendations.append("Somministrare ossigeno se saturazione < 94%")
            recommendations.append("Posizione semi-seduta")
        
        if 'fever' in symptoms and vital_signs.get('temperature', 0) > 38.5:
            recommendations.append("Somministrare antipiretico")
            recommendations.append("Controllare temperatura ogni 4 ore")
        
        # Medical history based recommendations
        if medical_history:
            if 'diabetes' in str(medical_history).lower():
                recommendations.append("Controllare glicemia")
            if 'hypertension' in str(medical_history).lower():
                recommendations.append("Monitorare pressione arteriosa")
        
        return recommendations
    
    def _calculate_confidence(self, symptoms: List[str], vital_signs: Dict) -> float:
        """Calculate AI confidence in triage decision"""
        confidence = 0.7  # Base confidence
        
        # More symptoms = higher confidence
        confidence += min(len(symptoms) * 0.05, 0.15)
        
        # Complete vital signs = higher confidence
        if vital_signs:
            vital_count = len([v for v in vital_signs.values() if v is not None])
            confidence += vital_count * 0.03
        
        return min(confidence, 0.95)
    
    def clinical_decision_support(self, patient_id: str, diagnosis: str,
                                  vital_signs: Dict, lab_results: Dict = None) -> Dict:
        """Provide clinical decision support for doctors"""
        decision_id = str(uuid.uuid4())
        
        # Check for drug interactions
        drug_interactions = self._check_drug_interactions(
            diagnosis,
            lab_results.get('current_medications', []) if lab_results else []
        )
        
        # Suggest treatment pathways
        treatment_pathways = self._suggest_treatment_pathways(
            diagnosis, vital_signs, lab_results
        )
        
        # Generate alerts
        alerts = self._generate_clinical_alerts(diagnosis, vital_signs, lab_results)
        
        # Get relevant guidelines
        guidelines = self._get_relevant_guidelines(diagnosis)
        
        decision = {
            'id': decision_id,
            'patient_id': patient_id,
            'timestamp': datetime.datetime.now().isoformat(),
            'diagnosis': diagnosis,
            'vital_signs': vital_signs,
            'lab_results': lab_results,
            'drug_interactions': drug_interactions,
            'treatment_pathways': treatment_pathways,
            'alerts': alerts,
            'guidelines': guidelines,
            'evidence_level': self._determine_evidence_level(diagnosis)
        }
        
        self.decisions.append(decision)
        return decision
    
    def _check_drug_interactions(self, diagnosis: str, current_meds: List[str]) -> List[Dict]:
        """Check for drug-drug interactions"""
        # Simplified drug interaction database
        interactions_db = {
            ('warfarin', 'aspirin'): {
                'severity': 'high',
                'description': 'Aumentato rischio di sanguinamento',
                'recommendation': 'Evitare combinazione se possibile'
            },
            ('ramipril', 'ibuprofen'): {
                'severity': 'moderate',
                'description': 'Rischio di insufficienza renale acuta',
                'recommendation': 'Monitorare funzione renale'
            }
        }
        
        interactions = []
        # In production: query actual drug database
        return interactions
    
    def _suggest_treatment_pathways(self, diagnosis: str, vital_signs: Dict,
                                    lab_results: Dict) -> List[Dict]:
        """Suggest treatment pathways based on Italian guidelines"""
        pathways = []
        
        # Common Italian diagnoses
        if 'ipertensione' in diagnosis.lower() or 'hypertension' in diagnosis.lower():
            pathways = [
                {
                    'step': 1,
                    'treatment': 'ACE-inibitore (Ramipril 2.5-5mg/die)',
                    'evidence': 'Linee Guida SIAP 2024',
                    'monitoring': 'PA settimanale, creatinina a 1 mese'
                },
                {
                    'step': 2,
                    'treatment': 'Aggiungere calcio-antagonista se non controllata',
                    'evidence': 'Linee Guida ESC/ESH',
                    'monitoring': 'PA giornaliera, ECG annuale'
                }
            ]
        elif 'diabete' in diagnosis.lower() or 'diabetes' in diagnosis.lower():
            pathways = [
                {
                    'step': 1,
                    'treatment': 'Metformina 500-1000mg/die',
                    'evidence': 'Linee Guida AMD-SID 2024',
                    'monitoring': 'HbA1c a 3 mesi, microalbuminuria annuale'
                },
                {
                    'step': 2,
                    'treatment': 'Aggiungere SGLT2-inibitore se alto rischio CV',
                    'evidence': 'Linee Guida ESC/EASD',
                    'monitoring': 'Glicemia capillare, funzionalità renale'
                }
            ]
        elif 'scompenso' in diagnosis.lower() or 'heart failure' in diagnosis.lower():
            pathways = [
                {
                    'step': 1,
                    'treatment': 'Diuretico dell\'ansa (Furosemide)',
                    'evidence': 'Linee Guida ANMCO 2023',
                    'monitoring': 'Peso giornaliero, diuresi'
                },
                {
                    'step': 2,
                    'treatment': 'Terapia con ACE-inibitore + beta-bloccante',
                    'evidence': 'Linee Guida ESC',
                    'monitoring': 'Funzionalità renale, ECG, ecocardiogramma'
                }
            ]
        
        return pathways
    
    def _generate_clinical_alerts(self, diagnosis: str, vital_signs: Dict,
                                   lab_results: Dict) -> List[Dict]:
        """Generate clinical alerts based on guidelines"""
        alerts = []
        
        # Check vital signs
        if vital_signs:
            bp_sys = vital_signs.get('blood_pressure_systolic', 0)
            if bp_sys > 180:
                alerts.append({
                    'type': 'CRISI_IPERTENSIVA',
                    'severity': 'high',
                    'message': 'Pressione arteriosa > 180 mmHg - Richiede intervento immediato',
                    'action': 'Considerare terapia antipertensiva ev'
                })
            
            hr = vital_signs.get('heart_rate', 0)
            if hr < 50:
                alerts.append({
                    'type': 'BRADICARDIA',
                    'severity': 'moderate',
                    'message': 'Frequenza cardiaca < 50 bpm',
                    'action': 'Valutare ECG e cause di bradicardia'
                })
        
        # Check lab results
        if lab_results:
            potassium = lab_results.get('potassium', 0)
            if potassium > 5.5:
                alerts.append({
                    'type': 'IPERKALIEMIA',
                    'severity': 'high',
                    'message': 'Potassio > 5.5 mEq/L - Rischio aritmie',
                    'action': 'Sospendere ACE-inibitori, valutare terapia'
                })
        
        return alerts
    
    def _get_relevant_guidelines(self, diagnosis: str) -> List[str]:
        """Get relevant Italian clinical guidelines"""
        guidelines = {
            'ipertensione': [
                'Linee Guida SIAP 2024 per il trattamento dell\'ipertensione',
                'Linee Guida ESC/ESH 2023',
                'Documento di consenso SIIA 2024'
            ],
            'diabete': [
                'Standard Italiani per la cura del diabete mellito 2024',
                'Linee Guida AMD-SID 2024',
                'Position Statement AMD 2023'
            ],
            'scompenso': [
                'Linee Guida ANMCO 2023 per lo scompenso cardiaco',
                'Linee Guida ESC 2023',
                'Raccomandazioni SIGOT 2024'
            ]
        }
        
        for key, value in guidelines.items():
            if key in diagnosis.lower():
                return value
        
        return ['Linee Guida Nazionali Italiane']
    
    def _determine_evidence_level(self, diagnosis: str) -> str:
        """Determine evidence level for recommendations"""
        evidence_levels = {
            'ipertensione': 'A (Raccomandazione forte)',
            'diabete': 'A (Raccomandazione forte)',
            'scompenso': 'B (Raccomandazione moderata)'
        }
        
        for key, value in evidence_levels.items():
            if key in diagnosis.lower():
                return value
        
        return 'C (Raccomandazione debole)'