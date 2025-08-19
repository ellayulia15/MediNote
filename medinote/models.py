from sqlalchemy import Column, Integer, String, Date
from .database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String, nullable=False)
    tanggal_lahir = Column(Date, nullable=False)
    tanggal_kunjungan = Column(Date, nullable=False)
    diagnosis = Column(String, nullable=True)
    tindakan = Column(String, nullable=True)
    dokter = Column(String, nullable=True)