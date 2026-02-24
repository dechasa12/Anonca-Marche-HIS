"""
Visit database model
"""

from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database.database import Base
import uuid

class Visit(Base):
    __tablename__ = "visits"
    
    id = Column(String, primary_key=True, default=lambda: f"V{uuid.uuid4().hex[:8].upper()}")
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(String, nullable=False)
    doctor_name = Column(String)
    
    # Visit details
    type = Column(String)  # televisita, ambulatoriale, emergenza, controllo
    status = Column(String, default="scheduled")  # scheduled, completed, cancelled
    priority = Column(String, default="normal")
    
    # Scheduling
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    actual_start = Column(DateTime(timezone=True))
    actual_end = Column(DateTime(timezone=True))
    duration = Column(Integer)  # minutes
    
    # Clinical data
    service_code = Column(String)
    service_name = Column(String)
    clinical_notes = Column(Text)
    diagnosis = Column(JSON, default=list)
    
    # Video session
    video_session = Column(String)
    
    # Relationships
    patient = relationship("Patient", back_populates="visits")
    prescriptions = relationship("Prescription", back_populates="visit", cascade="all, delete-orphan")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Visit {self.id} for patient {self.patient_id}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "type": self.type,
            "status": self.status,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "doctor_name": self.doctor_name,
            "clinical_notes": self.clinical_notes
        }