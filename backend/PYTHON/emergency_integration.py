"""
Emergency Integration Service for 118/EMS
Handles emergency calls, ambulance dispatch, and real-time tracking
"""

import uuid
import datetime
import requests
import json
from typing import Dict, List, Optional
import math

class EmergencyService:
    """Emergency integration with 118/EMS system"""
    
    def __init__(self):
        self.emergency_calls = []
        self.ambulance_dispatches = []
        self.active_ambulances = self._initialize_ambulances()
        
        # Emergency contact points
        self.emergency_contacts = {
            '118_ancona': {
                'name': 'Centrale Operativa 118 Ancona',
                'phone': '118',
                'api_url': 'https://api.118ancona.it/v1',
                'coordinates': {'lat': 43.6158, 'lon': 13.5189}
            },
            'ps_torrette': {
                'name': 'Pronto Soccorso - Ospedali Riuniti Torrette',
                'phone': '071596111',
                'api_url': 'https://api.aoumarche.it/emergency',
                'coordinates': {'lat': 43.5901, 'lon': 13.5302}
            }
        }
        
    def _initialize_ambulances(self) -> Dict:
        """Initialize ambulance fleet"""
        return {
            'AMB-001': {
                'id': 'AMB-001',
                'type': 'medicalizzata',
                'crew': ['autista', 'infermiere', 'rianimatore'],
                'location': {'lat': 43.6100, 'lon': 13.5200},
                'status': 'available',
                'equipment': ['defibrillatore', 'ventilatore', 'farmaci_emergenza']
            },
            'AMB-002': {
                'id': 'AMB-002',
                'type': 'basica',
                'crew': ['autista', 'soccorritore'],
                'location': {'lat': 43.6200, 'lon': 13.5300},
                'status': 'available',
                'equipment': ['barella', 'ossigeno', 'presidi_base']
            },
            'AMB-003': {
                'id': 'AMB-003',
                'type': 'medicalizzata',
                'crew': ['autista', 'infermiere', 'medico'],
                'location': {'lat': 43.6000, 'lon': 13.5100},
                'status': 'available',
                'equipment': ['ecografo', 'defibrillatore', 'farmaci']
            }
        }
    
    def initiate_emergency_call(self, patient_id: str, location: Dict,
                                 emergency_type: str, triage_level: str,
                                 patient_data: Dict = None) -> Dict:
        """
        Initiate emergency call to 118
        """
        call_id = f"EMS-{datetime.datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
        
        # Get nearest hospital
        nearest_hospital = self._find_nearest_hospital(location)
        
        # Determine required resources
        resources = self._determine_resources(emergency_type, triage_level)
        
        emergency_call = {
            'id': call_id,
            'patient_id': patient_id,
            'patient_name': f"{patient_data.get('cognome', '')} {patient_data.get('nome', '')}" if patient_data else 'Sconosciuto',
            'patient_cf': patient_data.get('codice_fiscale', '') if patient_data else '',
            'emergency_type': emergency_type,
            'triage_level': triage_level,
            'location': location,
            'nearest_hospital': nearest_hospital,
            'resources_needed': resources,
            'status': 'initiated',
            'timestamp': datetime.datetime.now().isoformat(),
            'ambulance_dispatched': False,
            'call_history': [{
                'action': 'call_initiated',
                'timestamp': datetime.datetime.now().isoformat()
            }]
        }
        
        self.emergency_calls.append(emergency_call)
        
        # Send to 118 central operations
        self._notify_118_central(emergency_call)
        
        # Auto-dispatch for red codes
        if triage_level == 'CODICE_ROSSO':
            dispatch = self.dispatch_ambulance(call_id)
            emergency_call['ambulance_dispatched'] = True
            emergency_call['dispatch_id'] = dispatch['id']
        
        return emergency_call
    
    def _find_nearest_hospital(self, location: Dict) -> Dict:
        """Find nearest hospital to location"""
        # Hospital coordinates
        hospitals = [
            {
                'id': 'torrette',
                'name': 'Ospedali Riuniti Torrette',
                'coordinates': {'lat': 43.5901, 'lon': 13.5302},
                'phone': '071596111'
            },
            {
                'id': 'salesi',
                'name': 'Ospedale Pediatrico Salesi',
                'coordinates': {'lat': 43.5905, 'lon': 13.5305},
                'phone': '071596211'
            },
            {
                'id': 'inrca',
                'name': 'INRCA Ancona',
                'coordinates': {'lat': 43.5850, 'lon': 13.5250},
                'phone': '0718003711'
            }
        ]
        
        # Calculate distances
        for hospital in hospitals:
            distance = self._calculate_distance(
                location['lat'], location['lon'],
                hospital['coordinates']['lat'], hospital['coordinates']['lon']
            )
            hospital['distance_km'] = round(distance, 1)
            hospital['eta_minutes'] = round(distance / 0.5)  # Assuming 30 km/h average
        
        # Return nearest
        nearest = min(hospitals, key=lambda x: x['distance_km'])
        return nearest
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates (Haversine formula)"""
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _determine_resources(self, emergency_type: str, triage_level: str) -> List[str]:
        """Determine required emergency resources"""
        resources = []
        
        # Resources by emergency type
        emergency_resources = {
            'CARDIAC_ARREST': ['ambulanza_con_rianimatore', 'defibrillatore', 'farmaci_emergenza'],
            'STROKE': ['ambulanza_con_neurologo', 'tac_prenotata', 'team_ictus'],
            'SEVERE_TRAUMA': ['elisoccorso', 'sala_operatoria', 'team_trauma'],
            'RESPIRATORY_FAILURE': ['ambulanza_con_ventilatore', 'pneumologo', 'emogasanalisi'],
            'ACUTE_ABDOMEN': ['ambulanza', 'chirurgo', 'ecografo'],
            'CONVULSIONS': ['ambulanza', 'neurologo', 'farmaci_antiepilettici']
        }
        
        resources.extend(emergency_resources.get(emergency_type, ['ambulanza']))
        
        # Additional resources by triage level
        if triage_level == 'CODICE_ROSSO':
            resources.append('preallarme_ps')
            resources.append('team_rianimazione')
        
        return list(set(resources))  # Remove duplicates
    
    def _notify_118_central(self, emergency_call: Dict):
        """Notify 118 central operations"""
        # In production: API call to 118 system
        print(f"📞 118 Central notified: {emergency_call['id']}")
        
        # Log notification
        emergency_call['call_history'].append({
            'action': '118_notified',
            'timestamp': datetime.datetime.now().isoformat()
        })
    
    def dispatch_ambulance(self, emergency_call_id: str) -> Dict:
        """
        Dispatch ambulance to emergency location
        """
        emergency_call = next((c for c in self.emergency_calls if c['id'] == emergency_call_id), None)
        
        if not emergency_call:
            raise Exception("Emergency call not found")
        
        dispatch_id = f"DSP-{datetime.datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
        
        # Find nearest available ambulance
        ambulance = self._find_nearest_ambulance(emergency_call['location'])
        
        # Calculate ETA
        eta = self._calculate_eta(ambulance['location'], emergency_call['location'])
        
        # Update ambulance status
        ambulance['status'] = 'dispatched'
        ambulance['current_mission'] = dispatch_id
        
        dispatch = {
            'id': dispatch_id,
            'emergency_call_id': emergency_call_id,
            'ambulance_id': ambulance['id'],
            'ambulance_type': ambulance['type'],
            'crew': ambulance['crew'],
            'equipment': ambulance['equipment'],
            'dispatch_time': datetime.datetime.now().isoformat(),
            'estimated_arrival': eta['estimated'],
            'eta_minutes': eta['minutes'],
            'location_from': ambulance['location'],
            'location_to': emergency_call['location'],
            'destination_hospital': emergency_call['nearest_hospital'],
            'status': 'dispatched',
            'route': self._calculate_route(ambulance['location'], emergency_call['location']),
            'updates': [{
                'timestamp': datetime.datetime.now().isoformat(),
                'status': 'dispatched',
                'location': ambulance['location']
            }]
        }
        
        self.ambulance_dispatches.append(dispatch)
        
        # Update emergency call
        emergency_call['ambulance_dispatched'] = True
        emergency_call['dispatch_id'] = dispatch_id
        emergency_call['status'] = 'ambulance_dispatched'
        emergency_call['call_history'].append({
            'action': 'ambulance_dispatched',
            'dispatch_id': dispatch_id,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
        # Send patient data to ambulance
        self._send_patient_data_to_ambulance(emergency_call, dispatch)
        
        return dispatch
    
    def _find_nearest_ambulance(self, location: Dict) -> Dict:
        """Find nearest available ambulance"""
        available = [a for a in self.active_ambulances.values() if a['status'] == 'available']
        
        if not available:
            # If no available ambulances, use any
            available = list(self.active_ambulances.values())
        
        # Calculate distances
        for ambulance in available:
            distance = self._calculate_distance(
                location['lat'], location['lon'],
                ambulance['location']['lat'], ambulance['location']['lon']
            )
            ambulance['distance_km'] = distance
        
        # Return nearest
        return min(available, key=lambda x: x['distance_km'])
    
    def _calculate_eta(self, from_loc: Dict, to_loc: Dict) -> Dict:
        """Calculate estimated time of arrival"""
        distance = self._calculate_distance(
            from_loc['lat'], from_loc['lon'],
            to_loc['lat'], to_loc['lon']
        )
        
        # Assume average speed 40 km/h with traffic
        minutes = round(distance / 40 * 60)
        
        return {
            'minutes': max(1, minutes),
            'estimated': (datetime.datetime.now() + datetime.timedelta(minutes=minutes)).isoformat()
        }
    
    def _calculate_route(self, from_loc: Dict, to_loc: Dict) -> List[str]:
        """Calculate route (simplified)"""
        # In production: use routing API
        return ['Via Flaminia', 'SS16', 'Via Torrette']
    
    def _send_patient_data_to_ambulance(self, emergency_call: Dict, dispatch: Dict):
        """Send patient data to ambulance crew"""
        patient_data = {
            'patient_id': emergency_call['patient_id'],
            'patient_name': emergency_call['patient_name'],
            'emergency_type': emergency_call['emergency_type'],
            'triage_level': emergency_call['triage_level'],
            'location': emergency_call['location'],
            'clinical_notes': emergency_call.get('clinical_notes', '')
        }
        
        # In production: send to ambulance tablet
        dispatch['patient_data_sent'] = True
        dispatch['patient_data'] = patient_data
        
        print(f"📱 Patient data sent to ambulance {dispatch['ambulance_id']}")
    
    def track_ambulance(self, dispatch_id: str) -> Dict:
        """Get real-time ambulance tracking"""
        dispatch = next((d for d in self.ambulance_dispatches if d['id'] == dispatch_id), None)
        
        if not dispatch:
            raise Exception("Dispatch not found")
        
        # Simulate movement (in production: get from GPS)
        progress = self._calculate_trip_progress(dispatch)
        
        tracking = {
            'dispatch_id': dispatch_id,
            'ambulance_id': dispatch['ambulance_id'],
            'current_location': progress['current_location'],
            'progress_percentage': progress['percentage'],
            'remaining_minutes': progress['remaining_minutes'],
            'estimated_arrival': progress['estimated_arrival'],
            'status': dispatch['status'],
            'speed_kmh': progress['speed'],
            'next_waypoint': progress['next_waypoint'],
            'last_update': datetime.datetime.now().isoformat()
        }
        
        return tracking
    
    def _calculate_trip_progress(self, dispatch: Dict) -> Dict:
        """Calculate trip progress (simulated)"""
        # Simulate movement
        start_time = datetime.datetime.fromisoformat(dispatch['dispatch_time'])
        elapsed = (datetime.datetime.now() - start_time).total_seconds() / 60  # minutes
        
        total_eta = dispatch['eta_minutes']
        progress_percentage = min((elapsed / total_eta) * 100, 100)
        
        # Simulated current location
        current_location = {
            'lat': dispatch['location_from']['lat'] + 
                   (dispatch['location_to']['lat'] - dispatch['location_from']['lat']) * (progress_percentage/100),
            'lon': dispatch['location_from']['lon'] + 
                   (dispatch['location_to']['lon'] - dispatch['location_from']['lon']) * (progress_percentage/100)
        }
        
        remaining_minutes = max(0, total_eta - elapsed)
        
        return {
            'current_location': current_location,
            'percentage': round(progress_percentage, 1),
            'remaining_minutes': round(remaining_minutes),
            'estimated_arrival': (datetime.datetime.now() + datetime.timedelta(minutes=remaining_minutes)).isoformat(),
            'speed': round(40 + (progress_percentage/100 * 10)),  # Variable speed
            'next_waypoint': 'Ospedale Regionale Torrette' if progress_percentage > 50 else 'Centro città'
        }
    
    def update_ambulance_status(self, dispatch_id: str, status: str,
                                 clinical_update: Dict = None) -> Dict:
        """Update ambulance status during transport"""
        dispatch = next((d for d in self.ambulance_dispatches if d['id'] == dispatch_id), None)
        
        if not dispatch:
            raise Exception("Dispatch not found")
        
        dispatch['status'] = status
        dispatch['updates'].append({
            'timestamp': datetime.datetime.now().isoformat(),
            'status': status,
            'clinical_update': clinical_update
        })
        
        # Update ambulance status in fleet
        ambulance = self.active_ambulances.get(dispatch['ambulance_id'])
        if ambulance:
            ambulance['status'] = self._map_dispatch_status_to_ambulance(status)
        
        # If patient on board, notify hospital
        if status == 'patient_on_board' and clinical_update:
            self._notify_hospital_of_incoming(dispatch, clinical_update)
        
        return dispatch
    
    def _map_dispatch_status_to_ambulance(self, status: str) -> str:
        """Map dispatch status to ambulance status"""
        mapping = {
            'dispatched': 'en_route',
            'arrived_at_patient': 'on_scene',
            'patient_on_board': 'transporting',
            'arrived_at_hospital': 'at_hospital',
            'completed': 'available'
        }
        return mapping.get(status, 'en_route')
    
    def _notify_hospital_of_incoming(self, dispatch: Dict, clinical_update: Dict):
        """Notify hospital of incoming patient"""
        hospital = dispatch['destination_hospital']
        
        notification = {
            'hospital_id': hospital['id'],
            'hospital_name': hospital['name'],
            'dispatch_id': dispatch['id'],
            'ambulance_id': dispatch['ambulance_id'],
            'eta_minutes': dispatch['eta_minutes'],
            'patient_id': dispatch.get('patient_data', {}).get('patient_id'),
            'clinical_update': clinical_update,
            'resources_needed': self._determine_hospital_resources(clinical_update)
        }
        
        # In production: send to hospital EMR
        print(f"🏥 Hospital {hospital['name']} notified of incoming patient")
        
        return notification
    
    def _determine_hospital_resources(self, clinical_update: Dict) -> List[str]:
        """Determine hospital resources needed"""
        resources = []
        
        if clinical_update:
            if clinical_update.get('ventilation_needed'):
                resources.append('ventilatore')
            if clinical_update.get('cardiac_monitoring'):
                resources.append('monitor_cardiaco')
            if clinical_update.get('stroke_symptoms'):
                resources.append('team_ictus')
                resources.append('tac_prenotata')
            if clinical_update.get('trauma'):
                resources.append('team_trauma')
                resources.append('sala_operatoria')
        
        return resources
    
    def complete_emergency_mission(self, dispatch_id: str, outcome: Dict) -> Dict:
        """Complete emergency mission and return ambulance to available"""
        dispatch = next((d for d in self.ambulance_dispatches if d['id'] == dispatch_id), None)
        
        if not dispatch:
            raise Exception("Dispatch not found")
        
        dispatch['status'] = 'completed'
        dispatch['completed_at'] = datetime.datetime.now().isoformat()
        dispatch['outcome'] = outcome
        
        # Update ambulance status
        ambulance = self.active_ambulances.get(dispatch['ambulance_id'])
        if ambulance:
            ambulance['status'] = 'available'
            ambulance['location'] = dispatch['location_to']  # Now at hospital
            ambulance['current_mission'] = None
        
        # Update emergency call
        emergency_call = next((c for c in self.emergency_calls if c['id'] == dispatch['emergency_call_id']), None)
        if emergency_call:
            emergency_call['status'] = 'completed'
            emergency_call['completed_at'] = dispatch['completed_at']
        
        return dispatch
    
    def get_emergency_statistics(self, date: str = None) -> Dict:
        """Get emergency statistics"""
        if date:
            calls = [c for c in self.emergency_calls if c['timestamp'].startswith(date)]
            dispatches = [d for d in self.ambulance_dispatches if d['dispatch_time'].startswith(date)]
        else:
            calls = self.emergency_calls
            dispatches = self.ambulance_dispatches
        
        stats = {
            'total_emergency_calls': len(calls),
            'total_dispatches': len(dispatches),
            'average_response_time': self._calculate_average_response_time(dispatches),
            'calls_by_type': self._group_calls_by_type(calls),
            'calls_by_triage': self._group_calls_by_triage(calls),
            'ambulance_utilization': self._calculate_ambulance_utilization()
        }
        
        return stats
    
    def _calculate_average_response_time(self, dispatches: List[Dict]) -> float:
        """Calculate average response time"""
        if not dispatches:
            return 0
        
        total_time = 0
        count = 0
        
        for d in dispatches:
            if 'updates' in d and len(d['updates']) > 1:
                dispatch_time = datetime.datetime.fromisoformat(d['dispatch_time'])
                arrival_time = None
                
                for update in d['updates']:
                    if update['status'] == 'arrived_at_patient':
                        arrival_time = datetime.datetime.fromisoformat(update['timestamp'])
                        break
                
                if arrival_time:
                    response_time = (arrival_time - dispatch_time).total_seconds() / 60
                    total_time += response_time
                    count += 1
        
        return round(total_time / count, 1) if count > 0 else 0
    
    def _group_calls_by_type(self, calls: List[Dict]) -> Dict:
        """Group emergency calls by type"""
        groups = {}
        for call in calls:
            etype = call.get('emergency_type', 'OTHER')
            groups[etype] = groups.get(etype, 0) + 1
        return groups
    
    def _group_calls_by_triage(self, calls: List[Dict]) -> Dict:
        """Group emergency calls by triage level"""
        groups = {}
        for call in calls:
            triage = call.get('triage_level', 'UNKNOWN')
            groups[triage] = groups.get(triage, 0) + 1
        return groups
    
    def _calculate_ambulance_utilization(self) -> Dict:
        """Calculate ambulance fleet utilization"""
        total = len(self.active_ambulances)
        available = len([a for a in self.active_ambulances.values() if a['status'] == 'available'])
        en_route = len([a for a in self.active_ambulances.values() if a['status'] in ['en_route', 'transporting']])
        
        return {
            'total': total,
            'available': available,
            'en_route': en_route,
            'utilization_rate': round((total - available) / total * 100, 1) if total > 0 else 0
        }