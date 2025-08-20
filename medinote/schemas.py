from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

# Patient Schemas
class PatientBase(BaseModel):
    nama: str
    tanggal_lahir: date
    tanggal_kunjungan: date
    diagnosis: str | None = None
    tindakan: str | None = None
    dokter: str | None = None

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    nama: str | None = None
    tanggal_lahir: date | None = None
    tanggal_kunjungan: date | None = None
    diagnosis: str | None = None
    tindakan: str | None = None
    dokter: str | None = None

class PatientFormUpdate(PatientBase):
    """Schema untuk form HTML update (semua field required)"""
    pass

class PatientOut(PatientBase):
    id: int

    class Config:
        from_attributes = True

# User Schemas
class UserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str  # Plain password, will be hashed
    
class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

class UserOut(UserBase):
    id: int
    firebase_uid: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserInDB(UserOut):
    password_hash: str

# Session Schemas
class SessionCreate(BaseModel):
    user_id: int
    firebase_token: str
    expires_at: datetime

class SessionOut(BaseModel):
    id: int
    user_id: int
    session_token: str
    expires_at: datetime
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True