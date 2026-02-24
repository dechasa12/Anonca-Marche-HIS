"""
Prescription database model
"""

from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database.database import Base
import uuid

class Prescription(Base):
    __tablename__ = "prescriptions"
    
    id = Column(String, primary_key=True, default=lambda: f"RX{uuid.uuid4().hex[:8].upper()}")
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    visit_id = Column(String, ForeignKey("visits.id"), nullable=False)
    doctor_id = Column(String, nullable=False)
    
    # Prescription details
    drug_name = Column(String, nullable=False)
    dosage = Column(String)
    frequency = Column(String)
    duration = Column(String)
    instructions = Column(Text)
    
    # Status
    status = Column(String, default="active")  # active, completed, cancelled
    refills = Column(Integer, default=0)
    refills_used = Column(Integer, default=0)
    
    # Timestamps
    prescribed_date = Column(DateTime(timezone=True), server_default=func.now())
    expires_date = Column(DateTime(timezone=True))
    
    # Relationships
    patient = relationship("Patient", back_populates="prescriptions")
    visit = relationship("Visit", back_populates="prescriptions")
    
    def __repr__(self):
        return f"<Prescription {self.drug_name} for patient {self.patient_id}>"