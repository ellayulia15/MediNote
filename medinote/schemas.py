from pydantic import BaseModel
from datetime import date

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