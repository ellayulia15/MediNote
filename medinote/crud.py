from sqlalchemy.orm import Session
from sqlalchemy import or_, func, and_
from datetime import datetime, timedelta, date
import hashlib
import secrets
from . import models, schemas

# Patient CRUD Operations
def get_patients(db: Session):
    return db.query(models.Patient).all()

def get_patients_by_date_range(db: Session, start_date: date = None, end_date: date = None):
    """Get patients filtered by date range"""
    query = db.query(models.Patient)
    
    if start_date:
        query = query.filter(models.Patient.tanggal_kunjungan >= start_date)
    if end_date:
        query = query.filter(models.Patient.tanggal_kunjungan <= end_date)
    
    return query.order_by(models.Patient.tanggal_kunjungan.desc()).all()

def get_dashboard_statistics(db: Session):
    """Get dashboard statistics for Level 4 requirements"""
    today = date.today()
    
    # Total patients
    total_patients = db.query(func.count(models.Patient.id)).scalar()
    
    # Patients today
    patients_today = db.query(func.count(models.Patient.id)).filter(
        models.Patient.tanggal_kunjungan == today
    ).scalar()
    
    return {
        "total_patients": total_patients or 0,
        "patients_today": patients_today or 0
    }

def get_patient(db: Session, patient_id: int):
    return db.query(models.Patient).filter(models.Patient.id == patient_id).first()

def create_patient(db: Session, patient: schemas.PatientCreate):
    db_patient = models.Patient(**patient.model_dump())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

def update_patient(db: Session, patient_id: int, patient: schemas.PatientUpdate):
    db_patient = get_patient(db, patient_id)
    if db_patient:
        update_data = patient.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_patient, key, value)
        db.commit()
        db.refresh(db_patient)
    return db_patient

def delete_patient(db: Session, patient_id: int):
    db_patient = get_patient(db, patient_id)
    if db_patient:
        db.delete(db_patient)
        db.commit()
    return db_patient

# User CRUD Operations
def get_password_hash(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return get_password_hash(plain_password) == hashed_password

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_firebase_uid(db: Session, firebase_uid: str):
    return db.query(models.User).filter(models.User.firebase_uid == firebase_uid).first()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, user: schemas.UserCreate):
    # Check if username or email already exists
    existing_user = db.query(models.User).filter(
        or_(models.User.username == user.username, models.User.email == user.email)
    ).first()
    
    if existing_user:
        return None  # User already exists
    
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        role=user.role,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    """Authenticate user with username and password"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user

def update_user_firebase_uid(db: Session, user_id: int, firebase_uid: str):
    """Update user's Firebase UID after successful Firebase registration"""
    user = get_user(db, user_id)
    if user:
        user.firebase_uid = firebase_uid
        db.commit()
        db.refresh(user)
    return user

# Session CRUD Operations
def create_session(db: Session, session: schemas.SessionCreate) -> models.UserSession:
    """Create new user session"""
    session_token = secrets.token_urlsafe(32)
    
    # Deactivate old sessions for this user
    db.query(models.UserSession).filter(
        models.UserSession.user_id == session.user_id,
        models.UserSession.is_active == True
    ).update({"is_active": False})
    
    db_session = models.UserSession(
        user_id=session.user_id,
        firebase_token=session.firebase_token,
        session_token=session_token,
        expires_at=session.expires_at,
        is_active=True
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_session_by_token(db: Session, session_token: str):
    """Get active session by token"""
    return db.query(models.UserSession).filter(
        models.UserSession.session_token == session_token,
        models.UserSession.is_active == True,
        models.UserSession.expires_at > datetime.utcnow()
    ).first()

def get_valid_session(db: Session, session_token: str):
    """Get valid session with user details"""
    from sqlalchemy.orm import joinedload
    
    session = db.query(models.UserSession).options(
        joinedload(models.UserSession.user)
    ).filter(
        models.UserSession.session_token == session_token,
        models.UserSession.is_active == True,
        models.UserSession.expires_at > datetime.utcnow()
    ).first()
    return session

def invalidate_session(db: Session, session_token: str):
    """Invalidate a session (logout)"""
    session = get_session_by_token(db, session_token)
    if session:
        session.is_active = False
        db.commit()
    return session

# Role-Based Access Control (RBAC) Functions
def check_user_permission(user, required_permission: str) -> bool:
    """Check if user has required permission based on role"""
    if user.role == models.UserRole.DOCTOR:
        # Doctor can do everything
        return True
    elif user.role == models.UserRole.ADMIN:
        # Admin can only view
        return required_permission == "view"
    return False

def require_permission(user, permission: str):
    """Raise exception if user doesn't have required permission"""
    if not check_user_permission(user, permission):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403, 
            detail=f"Access denied. {user.role.value.title()} role cannot {permission} patients."
        )