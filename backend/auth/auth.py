"""
Authentication system for AOU Marche HIS
Handles user registration, login, JWT tokens, and role-based access
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import os
from dotenv import load_dotenv

load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

# Password hashing - Use bcrypt with explicit backend to avoid detection issues
# We'll create the context but not use it at module load time
pwd_context = None

def get_password_context():
    """Lazy initialization of password context to avoid bcrypt detection at module load"""
    global pwd_context
    if pwd_context is None:
        pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12
        )
    return pwd_context

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# User database with pre-computed hashes (computed safely)
# We'll compute these at module load but with a safe method
import bcrypt as bcrypt_lib

def safe_bcrypt_hash(password: str) -> str:
    """Safely hash a password with bcrypt, truncating if necessary"""
    # Truncate password to 72 bytes if needed
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Generate salt and hash
    salt = bcrypt_lib.gensalt(rounds=12)
    hashed = bcrypt_lib.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

# Pre-compute hashes safely
ADMIN_HASH = safe_bcrypt_hash("Admin@2024")
DOCTOR_HASH = safe_bcrypt_hash("Medico@2024")
NURSE_HASH = safe_bcrypt_hash("Infermiere@2024")

users_db = {
    "admin@aoumarche.it": {
        "username": "admin",
        "email": "admin@aoumarche.it",
        "full_name": "Amministratore Sistema",
        "hashed_password": ADMIN_HASH,
        "disabled": False,
        "role": "admin",
        "hospital": "AOU Marche",
        "department": "Amministrazione"
    },
    "dott.rossi@aoumarche.it": {
        "username": "dott.rossi",
        "email": "dott.rossi@aoumarche.it",
        "full_name": "Mario Rossi",
        "hashed_password": DOCTOR_HASH,
        "disabled": False,
        "role": "doctor",
        "hospital": "Ospedale Lancisi",
        "department": "Cardiologia",
        "doctor_id": "DR-CARDIO-001"
    },
    "dott.verdi@aoumarche.it": {
        "username": "dott.verdi",
        "email": "dott.verdi@aoumarche.it",
        "full_name": "Giuseppe Verdi",
        "hashed_password": DOCTOR_HASH,
        "disabled": False,
        "role": "doctor",
        "hospital": "Ospedale Salesi",
        "department": "Pediatria",
        "doctor_id": "DR-PED-001"
    },
    "infermiere.bianchi@aoumarche.it": {
        "username": "inf.bianchi",
        "email": "infermiere.bianchi@aoumarche.it",
        "full_name": "Anna Bianchi",
        "hashed_password": NURSE_HASH,
        "disabled": False,
        "role": "nurse",
        "hospital": "Ospedali Riuniti",
        "department": "Pronto Soccorso"
    }
}

class User:
    """User model"""
    def __init__(self, username: str, email: str, full_name: str, 
                 hashed_password: str, disabled: bool, role: str, 
                 hospital: str, department: str, doctor_id: str = None):
        self.username = username
        self.email = email
        self.full_name = full_name
        self.hashed_password = hashed_password
        self.disabled = disabled
        self.role = role
        self.hospital = hospital
        self.department = department
        self.doctor_id = doctor_id

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using bcrypt directly (bypass passlib issues)"""
    try:
        # Use bcrypt directly instead of passlib
        import bcrypt as bcrypt_lib
        
        # Truncate password if needed
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        # Verify
        return bcrypt_lib.checkpw(password_bytes, hashed_password.encode('utf-8'))
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Hash password using bcrypt directly"""
    import bcrypt as bcrypt_lib
    
    # Truncate password if needed
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Hash
    salt = bcrypt_lib.gensalt(rounds=12)
    hashed = bcrypt_lib.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def get_user(db, username: str):
    """Get user by username"""
    if username in users_db:
        user_data = users_db[username]
        return User(
            username=user_data["username"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            hashed_password=user_data["hashed_password"],
            disabled=user_data["disabled"],
            role=user_data["role"],
            hospital=user_data["hospital"],
            department=user_data["department"],
            doctor_id=user_data.get("doctor_id")
        )
    return None

def authenticate_user(db, username: str, password: str):
    """Authenticate user"""
    user = get_user(db, username)
    if not user:
        return False
    
    if not verify_password(password, user.hashed_password):
        return False
    
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user(None, username=username)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user = Depends(get_current_user)):
    """Get current active user"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(required_role: str):
    """Decorator to require specific role"""
    async def role_checker(current_user = Depends(get_current_active_user)):
        if current_user.role != required_role and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {required_role} required"
            )
        return current_user
    return role_checker

# Role-based access helpers
require_admin = require_role("admin")
require_doctor = require_role("doctor")
require_nurse = require_role("nurse")

def get_current_doctor_id(current_user = Depends(get_current_active_user)) -> str:
    """Get current doctor ID"""
    if current_user.role not in ["doctor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor access required"
        )
    return getattr(current_user, "doctor_id", "DR-DEV-001")