"""
Vital signs database model
"""

from sqlalchemy import Column, String, DateTime, Float, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database.database import Base
import uuid

class VitalSigns(Base):
    __tablename__ = "vital_signs"
    
    id = Column(String, primary_key=True, default=lambda: f"VS{uuid.uuid4().hex[:8].upper()}")
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    
    # Vital signs
    heart_rate = Column(Integer)
    bp_systolic = Column(Integer)
    bp_diastolic = Column(Integer)
    oxygen_saturation = Column(Float)
    temperature = Column(Float)
    glucose = Column(Float)
    weight = Column(Float)
    respiratory_rate = Column(Integer)
    
    # Device info
    device_id = Column(String)
    device_type = Column(String)  # manual, bluetooth, medical_device
    
    # Alerts
    has_alerts = Column(Boolean, default=False)
    alerts = Column(JSON, default=list)
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="vital_signs")
    
    def __repr__(self):
        return f"<VitalSigns for patient {self.patient_id} at {self.timestamp}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "data": {
                "heart_rate": self.heart_rate,
                "blood_pressure": {
                    "systolic": self.bp_systolic,
                    "diastolic": self.bp_diastolic
                },
                "oxygen_saturation": self.oxygen_saturation,
                "temperature": self.temperature,
                "glucose": self.glucose
            },
            "alerts": self.alerts if self.alerts else []
        }