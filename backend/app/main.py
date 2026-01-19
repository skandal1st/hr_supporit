import threading
import time
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.routes import (
    audit,
    auth,
    birthdays,
    departments,
    employees,
    equipment,
    hr_requests,
    integrations,
    org,
    phonebook,
    positions,
    zup,
)
from app.api.routes import (
    settings as settings_routes,
)
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.hr_request import HRRequest
from app.models.system_settings import SystemSettings
from app.models.user import User
from app.services.hr_requests import process_hr_request

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(employees.router, prefix=settings.api_v1_prefix)
app.include_router(departments.router, prefix=settings.api_v1_prefix)
app.include_router(positions.router, prefix=settings.api_v1_prefix)
app.include_router(hr_requests.router, prefix=settings.api_v1_prefix)
app.include_router(phonebook.router, prefix=settings.api_v1_prefix)
app.include_router(birthdays.router, prefix=settings.api_v1_prefix)
app.include_router(org.router, prefix=settings.api_v1_prefix)
app.include_router(equipment.router, prefix=settings.api_v1_prefix)
app.include_router(audit.router, prefix=settings.api_v1_prefix)
app.include_router(integrations.router, prefix=settings.api_v1_prefix)
app.include_router(zup.router, prefix=settings.api_v1_prefix)
app.include_router(settings_routes.router, prefix=settings.api_v1_prefix)

# Mount static files for uploads
UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


@app.get("/health")
def health_check():
    """Health check endpoint для Docker и мониторинга"""
    return {"status": "ok"}


@app.on_event("startup")
def seed_admin_user() -> None:
    if not settings.seed_admin_enabled:
        return
    db = SessionLocal()
    try:
        existing = (
            db.query(User).filter(User.username == settings.seed_admin_email).first()
        )
        if existing:
            return
        user = User(
            username=settings.seed_admin_email,
            hashed_password=get_password_hash(settings.seed_admin_password),
            role=settings.seed_admin_role,
        )
        db.add(user)
        db.commit()
    finally:
        db.close()


def ensure_schema() -> None:
    with engine.begin() as connection:
        # Departments
        result = connection.execute(text("PRAGMA table_info(departments)"))
        columns = {row[1] for row in result.fetchall()}
        if "manager_id" not in columns:
            try:
                connection.execute(
                    text("ALTER TABLE departments ADD COLUMN manager_id INTEGER")
                )
            except Exception:
                pass
        if "external_id" not in columns:
            try:
                connection.execute(
                    text("ALTER TABLE departments ADD COLUMN external_id VARCHAR(128)")
                )
            except Exception:
                pass

        # Positions
        result = connection.execute(text("PRAGMA table_info(positions)"))
        position_columns = {row[1] for row in result.fetchall()}
        if "department_id" not in position_columns:
            try:
                connection.execute(
                    text("ALTER TABLE positions ADD COLUMN department_id INTEGER")
                )
            except Exception:
                pass
        if "external_id" not in position_columns:
            try:
                connection.execute(
                    text("ALTER TABLE positions ADD COLUMN external_id VARCHAR(128)")
                )
            except Exception:
                pass

        # Employees
        result = connection.execute(text("PRAGMA table_info(employees)"))
        employee_columns = {row[1] for row in result.fetchall()}
        if "external_id" not in employee_columns:
            try:
                connection.execute(
                    text("ALTER TABLE employees ADD COLUMN external_id VARCHAR(128)")
                )
            except Exception:
                pass


def start_due_requests_worker() -> None:
    def _worker() -> None:
        while True:
            db = SessionLocal()
            try:
                today = date.today()
                requests = (
                    db.query(HRRequest)
                    .filter(HRRequest.status != "done")
                    .filter(HRRequest.effective_date.isnot(None))
                    .filter(HRRequest.effective_date <= today)
                    .all()
                )
                for req in requests:
                    process_hr_request(db, req)
            finally:
                db.close()
            time.sleep(60)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()


@app.on_event("startup")
def start_background_workers() -> None:
    ensure_schema()
    start_due_requests_worker()
