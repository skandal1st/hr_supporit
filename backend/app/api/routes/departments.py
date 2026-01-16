from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.department import Department
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentOut, DepartmentUpdate
from app.services.audit import log_action


router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("/", response_model=List[DepartmentOut], dependencies=[Depends(require_roles(["hr", "it", "manager", "auditor"]))])
def list_departments(db: Session = Depends(get_db)) -> List[Department]:
    return db.query(Department).all()


@router.post("/", response_model=DepartmentOut, dependencies=[Depends(require_roles(["hr"]))])
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Department:
    department = Department(**payload.model_dump())
    db.add(department)
    db.commit()
    db.refresh(department)
    log_action(db, user.username, "create", "department", f"id={department.id}")
    return department


@router.patch("/{department_id}", response_model=DepartmentOut, dependencies=[Depends(require_roles(["hr"]))])
def update_department(
    department_id: int,
    payload: DepartmentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Department:
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Отдел не найден")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(department, field, value)
    db.commit()
    db.refresh(department)
    log_action(db, user.username, "update", "department", f"id={department.id}")
    return department
