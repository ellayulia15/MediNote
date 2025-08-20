import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import firebase_admin
from firebase_admin import credentials, auth
from . import models, schemas, crud
from .database import SessionLocal, engine

# Load environment variables
load_dotenv()

# --- Init Firebase Admin ---
cred_path = os.getenv("FIREBASE_CRED", "secrets/serviceAccountKey.json")
firebase_initialized = False

if not firebase_admin._apps:
    try:
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            firebase_initialized = True
            print("✅ Firebase Admin SDK initialized successfully")
        else:
            print(f"⚠️  Warning: Firebase service account file not found at {cred_path}")
            print("   Protected routes will not work without Firebase authentication")
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        print("   Protected routes will not work without Firebase authentication")

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="MediNote API", description="Medical Records Management System")
templates = Jinja2Templates(directory="medinote/templates")

# Setup CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173", 
        "http://127.0.0.1:5500",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="medinote/static"), name="static")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Firebase Authentication Dependency ---
async def verify_firebase_token(request: Request):
    """Verify Firebase ID token from Authorization header"""
    # Development bypass when Firebase is not configured
    if not firebase_initialized:
        # Check for development bypass (only in DEBUG mode)
        if os.getenv("DEBUG", "False").lower() == "true":
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer dev-bypass"):
                return {"uid": "dev-user", "email": "dev@example.com", "name": "Development User"}
        
        raise HTTPException(
            status_code=503, 
            detail="Firebase authentication not configured. Service account key missing. See /secrets/README.md for setup instructions."
        )
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")

    id_token = auth_header.split(" ", 1)[1].strip()
    try:
        decoded = auth.verify_id_token(id_token)  # verify with Firebase
        return decoded  # contains uid, email, etc
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")

# --- Optional: dependency for web routes (check if user is logged in via session/cookie) ---
async def get_current_user_optional(request: Request):
    """Optional authentication for web routes"""
    # For now, we'll skip web authentication and focus on API
    # You can implement session-based auth here later if needed
    return None

# --- Session Management Functions ---
def get_current_user_from_session(request: Request, db: Session):
    """Get current logged in user from session cookie or header"""
    # Check for session token in cookie or header
    session_token = request.cookies.get("session_token") or request.headers.get("X-Session-Token")
    
    if not session_token:
        return None
    
    # Validate session in database
    session = crud.get_valid_session(db, session_token)
    if not session:
        return None
        
    return session.user

def require_authenticated_user(request: Request, db: Session = Depends(get_db)):
    """Dependency to require authenticated user"""
    user = get_current_user_from_session(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

def require_doctor_role(request: Request, db: Session = Depends(get_db)):
    """Dependency to require doctor role for add/edit/delete operations"""
    user = require_authenticated_user(request, db)
    crud.require_permission(user, "add")  # Will check if user can add/edit/delete
    return user

def require_view_permission(request: Request, db: Session = Depends(get_db)):
    """Dependency to require view permission (both doctor and admin)"""
    user = require_authenticated_user(request, db)
    crud.require_permission(user, "view")  # Both roles can view
    return user

@app.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    """Home page - redirect to login if not authenticated"""
    current_user = get_current_user_from_session(request, db)
    if not current_user:
        # User not logged in, redirect to login
        return RedirectResponse("/login", status_code=302)
    
    # User is logged in, show patients page
    patients = crud.get_patients(db)
    return templates.TemplateResponse("patients.html", {
        "request": request, 
        "patients": patients,
        "current_user": current_user
    })

@app.get("/login")
def login_page(request: Request, db: Session = Depends(get_db)):
    """Display login page - redirect if already logged in"""
    current_user = get_current_user_from_session(request, db)
    if current_user:
        # User already logged in, redirect to home
        return RedirectResponse("/", status_code=302)
    
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register")
def register_page(request: Request, db: Session = Depends(get_db)):
    """Display registration page - redirect if already logged in"""
    current_user = get_current_user_from_session(request, db)
    if current_user:
        # User already logged in, redirect to home
        return RedirectResponse("/", status_code=302)
    
    return templates.TemplateResponse("register.html", {"request": request})

# --- Authentication Routes ---
@app.post("/auth/register", response_model=schemas.UserOut)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register new user in database"""
    db_user = crud.create_user(db, user)
    if not db_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    return db_user

# Quick test user creation endpoint (for development)
@app.post("/auth/create-test-user")
def create_test_user(db: Session = Depends(get_db)):
    """Create test user for development"""
    try:
        # Check if test user already exists
        existing_user = crud.get_user_by_username(db, "testuser")
        if existing_user:
            return {"message": "Test user already exists", "user": existing_user.username}
        
        # Create test user
        user_data = schemas.UserCreate(
            username="testuser",
            email="test@medinote.com", 
            full_name="Test User",
            password="password123"
        )
        
        user = crud.create_user(db, user_data)
        if user:
            return {"message": "Test user created successfully", "user": user.username}
        else:
            raise HTTPException(status_code=400, detail="Failed to create test user")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating test user: {str(e)}")

@app.post("/auth/login", response_model=schemas.UserOut)  
def login_user(user_login: schemas.UserLogin, db: Session = Depends(get_db)):
    """Authenticate user with username and password"""
    user = crud.authenticate_user(db, user_login.username, user_login.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return user

@app.post("/auth/link-firebase/{user_id}")
def link_firebase_uid(user_id: int, firebase_data: dict, db: Session = Depends(get_db)):
    """Link Firebase UID to existing user"""
    user = crud.update_user_firebase_uid(db, user_id, firebase_data["firebase_uid"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Firebase UID linked successfully"}

@app.post("/auth/create-session", response_model=schemas.SessionOut)
def create_user_session(
    session_data: schemas.SessionCreate,
    db: Session = Depends(get_db)
):
    """Create user session after successful authentication (Simplified)"""
    # Validate user exists
    user = crud.get_user(db, session_data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    session = crud.create_session(db, session_data)
    return session

@app.post("/auth/logout")
def logout_user(request: Request, db: Session = Depends(get_db)):
    """Logout user and invalidate session"""
    session_token = request.cookies.get("session_token") or request.headers.get("X-Session-Token")
    if session_token:
        crud.invalidate_session(db, session_token)
    return {"message": "Logged out successfully"}

@app.get("/auth/logout")
def logout_user_web(request: Request, db: Session = Depends(get_db)):
    """Web logout route with redirect"""
    session_token = request.cookies.get("session_token")
    if session_token:
        crud.invalidate_session(db, session_token)
    
    # Create redirect response and clear session cookie
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("session_token")
    return response

@app.post("/add")
def add_patient(
    nama: str = Form(...),
    tanggal_lahir: str = Form(...),
    tanggal_kunjungan: str = Form(...),
    diagnosis: str = Form(""),
    tindakan: str = Form(""),
    dokter: str = Form(""),
    current_user = Depends(require_doctor_role),  # Only doctors can add
    db: Session = Depends(get_db)
):
    patient = schemas.PatientCreate(
        nama=nama,
        tanggal_lahir=tanggal_lahir,
        tanggal_kunjungan=tanggal_kunjungan,
        diagnosis=diagnosis,
        tindakan=tindakan,
        dokter=dokter
    )
    crud.create_patient(db, patient)
    return RedirectResponse("/", status_code=303)

@app.get("/edit/{patient_id}")
def edit_patient_form(
    request: Request, 
    patient_id: int, 
    current_user = Depends(require_doctor_role),  # Only doctors can edit
    db: Session = Depends(get_db)
):
    patient = crud.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return templates.TemplateResponse("edit_patient.html", {"request": request, "patient": patient})

@app.post("/edit/{patient_id}")
def update_patient(
    patient_id: int,
    nama: str = Form(...),
    tanggal_lahir: str = Form(...),
    tanggal_kunjungan: str = Form(...),
    diagnosis: str = Form(""),
    tindakan: str = Form(""),
    dokter: str = Form(""),
    current_user = Depends(require_doctor_role),  # Only doctors can edit
    db: Session = Depends(get_db)
):
    patient_data = schemas.PatientFormUpdate(
        nama=nama,
        tanggal_lahir=tanggal_lahir,
        tanggal_kunjungan=tanggal_kunjungan,
        diagnosis=diagnosis,
        tindakan=tindakan,
        dokter=dokter
    )
    # Convert to PatientUpdate for the CRUD function
    update_data = schemas.PatientUpdate(**patient_data.model_dump())
    updated_patient = crud.update_patient(db, patient_id, update_data)
    if not updated_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return RedirectResponse("/", status_code=303)

@app.post("/delete/{patient_id}")
def delete_patient(
    patient_id: int, 
    current_user = Depends(require_doctor_role),  # Only doctors can delete
    db: Session = Depends(get_db)
):
    deleted_patient = crud.delete_patient(db, patient_id)
    if not deleted_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return RedirectResponse("/", status_code=303)

# API Endpoints (JSON responses) - Protected with Firebase Auth
@app.get("/api/patients", response_model=list[schemas.PatientOut])
def get_patients_api(user=Depends(verify_firebase_token), db: Session = Depends(get_db)):
    """Get all patients as JSON (Protected route)"""
    return crud.get_patients(db)

@app.get("/api/patients/{patient_id}", response_model=schemas.PatientOut)
def get_patient_api(patient_id: int, user=Depends(verify_firebase_token), db: Session = Depends(get_db)):
    """Get single patient as JSON (Protected route)"""
    patient = crud.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@app.post("/api/patients", response_model=schemas.PatientOut)
def create_patient_api(patient: schemas.PatientCreate, user=Depends(verify_firebase_token), db: Session = Depends(get_db)):
    """Create patient via JSON API (Protected route)"""
    return crud.create_patient(db, patient)

@app.put("/api/patients/{patient_id}", response_model=schemas.PatientOut)
def update_patient_api(patient_id: int, patient: schemas.PatientUpdate, user=Depends(verify_firebase_token), db: Session = Depends(get_db)):
    """Update patient via JSON API (Protected route)"""
    updated_patient = crud.update_patient(db, patient_id, patient)
    if not updated_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return updated_patient

@app.delete("/api/patients/{patient_id}")
def delete_patient_api(patient_id: int, user=Depends(verify_firebase_token), db: Session = Depends(get_db)):
    """Delete patient via JSON API (Protected route)"""
    deleted_patient = crud.delete_patient(db, patient_id)
    if not deleted_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"message": "Patient deleted successfully"}

# --- Firebase Auth Test Routes ---
@app.get("/api/auth/protected")
async def protected_route(user=Depends(verify_firebase_token)):
    """Test protected route"""
    return {
        "message": f"Hello {user.get('email', user['uid'])}, authentication successful!",
        "user_id": user['uid'],
        "email": user.get('email'),
        "name": user.get('name')
    }

@app.get("/api/auth/user-info")
async def get_user_info(user=Depends(verify_firebase_token)):
    """Get current user information"""
    return {
        "uid": user['uid'],
        "email": user.get('email'),
        "email_verified": user.get('email_verified', False),
        "name": user.get('name'),
        "picture": user.get('picture'),
        "firebase_claims": user
    }