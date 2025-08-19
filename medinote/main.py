from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from . import models, schemas, crud
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="medinote/templates")

# Mount static files
app.mount("/static", StaticFiles(directory="medinote/static"), name="static")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_patients(request: Request, db: Session = Depends(get_db)):
    patients = crud.get_patients(db)
    return templates.TemplateResponse("patients.html", {"request": request, "patients": patients})

@app.post("/add")
def add_patient(
    nama: str = Form(...),
    tanggal_lahir: str = Form(...),
    tanggal_kunjungan: str = Form(...),
    diagnosis: str = Form(""),
    tindakan: str = Form(""),
    dokter: str = Form(""),
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
def edit_patient_form(request: Request, patient_id: int, db: Session = Depends(get_db)):
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
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    deleted_patient = crud.delete_patient(db, patient_id)
    if not deleted_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return RedirectResponse("/", status_code=303)

# API Endpoints (JSON responses)
@app.get("/api/patients", response_model=list[schemas.PatientOut])
def get_patients_api(db: Session = Depends(get_db)):
    """Get all patients as JSON"""
    return crud.get_patients(db)

@app.get("/api/patients/{patient_id}", response_model=schemas.PatientOut)
def get_patient_api(patient_id: int, db: Session = Depends(get_db)):
    """Get single patient as JSON"""
    patient = crud.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@app.post("/api/patients", response_model=schemas.PatientOut)
def create_patient_api(patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    """Create patient via JSON API"""
    return crud.create_patient(db, patient)

@app.put("/api/patients/{patient_id}", response_model=schemas.PatientOut)
def update_patient_api(patient_id: int, patient: schemas.PatientUpdate, db: Session = Depends(get_db)):
    """Update patient via JSON API"""
    updated_patient = crud.update_patient(db, patient_id, patient)
    if not updated_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return updated_patient

@app.delete("/api/patients/{patient_id}")
def delete_patient_api(patient_id: int, db: Session = Depends(get_db)):
    """Delete patient via JSON API"""
    deleted_patient = crud.delete_patient(db, patient_id)
    if not deleted_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"message": "Patient deleted successfully"}