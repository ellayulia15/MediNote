# 🏥 MediNote

**MediNote** is a simple patient management system built with **FastAPI**, **PostgreSQL**, **HTML**, and **Tailwind CSS**.  
This project was developed as part of a candidate technical test to demonstrate backend, frontend, and database integration skills.  

## 🚀 Features
- **CRUD Patients** → Add, view, edit, and delete patient records.  
- **User Authentication** → Simple login using **Firebase**.  
- **Role-Based Access Control (RBAC)** → 
  - Doctor → can add/edit/delete patients.  
  - Admin → can only view patients.  
- **Dashboard & Reports** → Summary of patients, daily count, detailed table view, and filter by visit date.  
- **Integration Tools** →  
  - Import patient data via JSON (dummy endpoint).  
  - Export patient data to Excel.  

## 🛠️ Tech Stack
- **Backend**: FastAPI (Python)  
- **Database**: PostgreSQL (SQLAlchemy ORM)  
- **Frontend**: HTML + Tailwind CSS (Jinja2 templates)  
- **Authentication**: Firebase  
- **Other Tools**: OpenPyXL (Excel export)  

## 📂 Project Structure
medinote/
- │── main.py # FastAPI entry point
- │── database.py # Database connection (PostgreSQL)
- │── models.py # SQLAlchemy models
- │── schemas.py # Pydantic schemas
- │── crud.py # CRUD operations
- │── templates/ # HTML templates (Jinja2 + Tailwind)
- │── static/ # Static files (if needed)

## ⚙️ Installation & Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/medinote.git
   cd medinote
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/Mac
   venv\Scripts\activate      # Windows
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
4. Setup PostgreSQL database and update DATABASE_URL in database.py.
5. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload
6. Open in browser:
   ```bash
   http://127.0.0.1:8000

## ✨ Future Improvements
- Better UI design with Tailwind components.
- Deploy to VPS (AWS/IDCloudHost).
- Enhance authentication (JWT / OAuth2).
