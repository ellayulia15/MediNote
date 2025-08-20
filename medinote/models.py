from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base

# Role Enum for RBAC
class UserRole(str, enum.Enum):
    DOCTOR = "doctor"
    ADMIN = "admin"

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String, nullable=False)
    tanggal_lahir = Column(Date, nullable=False)
    tanggal_kunjungan = Column(Date, nullable=False)
    diagnosis = Column(String, nullable=True)
    tindakan = Column(String, nullable=True)
    dokter = Column(String, nullable=True)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)  # Hashed password
    role = Column(Enum(UserRole), default=UserRole.DOCTOR, nullable=False)  # RBAC Role
    firebase_uid = Column(String, unique=True, index=True, nullable=True)  # Firebase UID
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user")

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    firebase_token = Column(Text, nullable=False)  # Firebase ID token
    session_token = Column(String, unique=True, index=True, nullable=False)  # Local session token
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")