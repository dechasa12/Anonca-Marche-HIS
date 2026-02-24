"""
Patient database model
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database.database import Base
import uuid

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(String, primary_key=True, default=lambda: f"P{uuid.uuid4().hex[:8].upper()}")
    codice_fiscale = Column(String(16), unique=True, nullable=False, index=True)
    tessera_sanitaria = Column(String(20), unique=True)
    
    # Personal information
    cognome = Column(String(50), nullable=False)
    nome = Column(String(50), nullable=False)
    sesso = Column(String(1), nullable=False)
    data_nascita = Column(String(10), nullable=False)
    comune_nascita = Column(String(50), nullable=False)
    provincia_nascita = Column(String(2))
    
    # Contact information
    email = Column(String(100))
    telefono = Column(String(20), nullable=False)
    indirizzo = Column(String(200))
    cap = Column(String(5))
    comune = Column(String(50))
    provincia = Column(String(2))
    asl = Column(String(20))
    
    # Medical information
    gruppo_sanguigno = Column(String(3))
    medico_base = Column(String(50))
    allergie = Column(Text)
    farmaci = Column(Text)
    patologie = Column(JSON, default=list)
    note = Column(Text)
    
    # Consents
    consenso_telemedicina = Column(Boolean, default=False)
    consenso_fse = Column(Boolean, default=False)
    consenso_ricerca = Column(Boolean, default=False)
    consenso_notifiche = Column(Boolean, default=False)
    consenso_privacy = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_visit = Column(DateTime(timezone=True))
    
    # Relationships
    visits = relationship("Visit", back_populates="patient", cascade="all, delete-orphan")
    vital_signs = relationship("VitalSigns", back_populates="patient", cascade="all, delete-orphan")
    prescriptions = relationship("Prescription", back_populates="patient", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Patient {self.cognome} {self.nome}>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "codice_fiscale": self.codice_fiscale,
            "cognome": self.cognome,
            "nome": self.nome,
            "sesso": self.sesso,
            "data_nascita": self.data_nascita,
            "email": self.email,
            "telefono": self.telefono,
            "consensi": {
                "telemedicina": self.consenso_telemedicina,
                "fse": self.consenso_fse,
                "ricerca": self.consenso_ricerca
            }
        }