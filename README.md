# MediNote - Sistem Manajemen Data Pasien

## Deskripsi
MediNote adalah aplikasi web untuk mengelola data pasien dengan fitur lengkap termasuk dashboard, filter, import/export, dan role-based access control.

## Fitur Utama

### Level 4 - Dashboard & CRUD
- ✅ Dashboard dengan statistik pasien
- ✅ CRUD operations (Create, Read, Update, Delete)
- ✅ Role-based access (Doctor vs Admin)
- ✅ Filter data berdasarkan tanggal kunjungan
- ✅ Responsive UI dengan Tailwind CSS

### Level 5 - Import/Export
- ✅ Import data pasien dari file JSON
- ✅ Export data pasien ke Excel (.xlsx)
- ✅ Validasi data import
- ✅ Filter berlaku pada export

## Struktur Project

```
medinote/
├── main.py          # FastAPI application & routes
├── models.py        # SQLAlchemy database models
├── schemas.py       # Pydantic schemas untuk API
├── crud.py          # Database operations
├── database.py      # Database configuration
├── requirements.txt # Python dependencies
├── templates/       # Jinja2 HTML templates
│   ├── dashboard.html
│   ├── edit_patient.html
│   ├── login.html
│   └── register.html
└── static/          # Static files (CSS, JS, images)
```

## Instalasi & Menjalankan

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Jalankan Server**
   ```bash
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Akses Aplikasi**
   - URL: `http://localhost:8000`
   - Default user: `admin` / `admin123` (role: Admin)
   - Default user: `doctor` / `doctor123` (role: Doctor)

## Teknologi yang Digunakan

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Frontend**: Jinja2 Templates, Tailwind CSS
- **Export**: pandas, openpyxl (Excel)
- **Authentication**: Session-based auth
- **Database**: SQLite (development)

## API Endpoints

### Auth
- `GET /` - Halaman utama (redirect ke dashboard jika login)
- `GET /login` - Halaman login
- `POST /auth/login` - Login user
- `GET /register` - Halaman register
- `POST /auth/register` - Register user baru
- `POST /auth/logout` - Logout user

### Dashboard & Data
- `GET /dashboard` - Dashboard utama dengan statistik dan data
- `GET /patients` - Redirect ke dashboard (unified interface)

### CRUD Operations
- `POST /add` - Tambah pasien baru
- `GET /edit/{patient_id}` - Form edit pasien
- `POST /update/{patient_id}` - Update data pasien
- `POST /delete/{patient_id}` - Hapus pasien

### Import/Export
- `POST /api/import/patients/json` - Import data dari JSON
- `GET /export/patients/excel` - Export data ke Excel

## Database Schema

### Users Table
- `id`: Integer (Primary Key)
- `username`: String (Unique)
- `hashed_password`: String
- `role`: Enum (doctor, admin)

### Patients Table
- `id`: Integer (Primary Key)
- `nama`: String (required)
- `tanggal_lahir`: Date (required)
- `tanggal_kunjungan`: Date (required)
- `diagnosis`: String (optional)
- `tindakan`: String (optional)
- `dokter`: String (optional)

## Role Permissions

### Doctor
- ✅ View dashboard & statistics
- ✅ Add new patients
- ✅ Edit existing patients
- ✅ Delete patients
- ✅ Import data from JSON
- ✅ Export data to Excel
- ✅ Filter data by date range

### Admin
- ✅ View dashboard & statistics
- ❌ Add/Edit/Delete patients
- ✅ Export data to Excel
- ✅ Filter data by date range

## Development Notes

- Clean code structure dengan separation of concerns
- Responsive design untuk mobile dan desktop
- Error handling dan validasi data
- Session-based authentication
- SQL injection protection dengan SQLAlchemy ORM