"""
Database configuration for AOU Marche HIS
PostgreSQL connection and session management
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "aoumarche")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# Database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine with proper configuration
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    echo=False,  # Set to True for SQL logging
    connect_args={"connect_timeout": 10}
)

# Create metadata with naming convention for constraints
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models with extend_existing=True to avoid redefinition errors
Base = declarative_base(metadata=metadata)

# Dependency to get DB session
def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database
def init_db():
    """Create all tables"""
    # Import all models here to ensure they are registered with Base
    from backend.models.patient import Patient
    from backend.models.visit import Visit
    from backend.models.vitals import VitalSigns
    from backend.models.prescription import Prescription
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")

# Drop all tables (use with caution!)
def drop_db():
    """Drop all tables"""
    Base.metadata.drop_all(bind=engine)
    print("⚠️ All database tables dropped")

# Reset database (for development)
def reset_db():
    """Drop and recreate all tables"""
    drop_db()
    init_db()
    print("🔄 Database reset complete")