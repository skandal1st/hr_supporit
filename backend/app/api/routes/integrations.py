from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.equipment import Equipment
from app.models.employee import Employee
from app.services.integrations import (
    ad_sync_users,
    fetch_equipment_for_employee,
    fetch_supporit_users,
    fetch_zup_employees,
    provision_it_accounts,
    update_supporit_user,
)


router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/supporit/{employee_id}", dependencies=[Depends(require_roles(["it"]))])
def get_supporit_equipment(
    employee_id: int,
    db: Session = Depends(get_db),
    email: str | None = Query(default=None),
) -> list[dict]:
    equipment = fetch_equipment_for_employee(employee_id, email)
    if equipment:
        for item in equipment:
            db.add(Equipment(**item))
        db.commit()
    return equipment


@router.get("/supporit/health", dependencies=[Depends(require_roles(["it"]))])
def supporit_healthcheck() -> dict:
    users = fetch_supporit_users()
    return {"status": "ok", "users_count": len(users)}


@router.post("/ad/provision", dependencies=[Depends(require_roles(["it"]))])
def provision_accounts(full_name: str) -> dict:
    accounts = provision_it_accounts(full_name)
    return {
        "ad_account": accounts.ad_account,
        "mailcow_account": accounts.mailcow_account,
        "messenger_account": accounts.messenger_account,
    }


@router.post("/ad/pull-users", dependencies=[Depends(require_roles(["it"]))])
def pull_users_from_ad(db: Session = Depends(get_db)) -> dict:
    users = ad_sync_users()
    created = 0
    updated = 0
    for user in users:
        email = user.get("email")
        if not email:
            continue
        employee = db.query(Employee).filter(Employee.email == email).first()
        if employee:
            employee.full_name = user.get("full_name") or employee.full_name
            employee.internal_phone = user.get("phone") or employee.internal_phone
            updated += 1
        else:
            db.add(
                Employee(
                    full_name=user.get("full_name") or email,
                    email=email,
                    internal_phone=user.get("phone"),
                    status="active",
                )
            )
            created += 1
    db.commit()
    return {"created": created, "updated": updated}


@router.post("/supporit/pull-users", dependencies=[Depends(require_roles(["it"]))])
def pull_users_from_supporit(db: Session = Depends(get_db)) -> dict:
    users = fetch_supporit_users()
    created = 0
    updated = 0
    for user in users:
        email = user.get("email")
        full_name = user.get("full_name") or user.get("fullName") or ""
        if not email:
            continue
        employee = db.query(Employee).filter(Employee.email == email).first()
        if employee:
            employee.full_name = full_name or employee.full_name
            employee.department_id = employee.department_id
            employee.internal_phone = user.get("phone") or employee.internal_phone
            updated += 1
        else:
            employee = Employee(
                full_name=full_name or email,
                email=email,
                internal_phone=user.get("phone"),
                status="active",
            )
            db.add(employee)
            created += 1
    db.commit()
    return {"created": created, "updated": updated}


@router.post("/supporit/push-contacts", dependencies=[Depends(require_roles(["it", "hr"]))])
def push_contacts_to_supporit(
    db: Session = Depends(get_db),
    create_missing: bool = False,
) -> dict:
    users = fetch_supporit_users()
    users_by_email = {user.get("email"): user for user in users if user.get("email")}
    updated = 0
    skipped = 0
    for employee in db.query(Employee).all():
        if not employee.email:
            skipped += 1
            continue
        supporit_user = users_by_email.get(employee.email)
        if not supporit_user:
            skipped += 1
            continue
        payload = {
            "full_name": employee.full_name,
            "department": None,
            "position": None,
            "phone": employee.internal_phone or employee.external_phone,
        }
        if update_supporit_user(supporit_user.get("id"), payload):
            updated += 1
    return {"updated": updated, "skipped": skipped, "create_missing": create_missing}


@router.post("/zup/pull-users", dependencies=[Depends(require_roles(["hr", "it"]))])
def pull_users_from_zup(db: Session = Depends(get_db)) -> dict:
    users = fetch_zup_employees()
    created = 0
    updated = 0
    for user in users:
        external_id = user.get("id") or user.get("external_id")
        email = user.get("email")
        full_name = user.get("full_name") or user.get("fio") or ""
        employee = None
        if external_id:
            employee = db.query(Employee).filter(Employee.external_id == external_id).first()
        if not employee and email:
            employee = db.query(Employee).filter(Employee.email == email).first()
        if employee:
            employee.full_name = full_name or employee.full_name
            employee.external_id = external_id or employee.external_id
            employee.internal_phone = user.get("phone") or employee.internal_phone
            updated += 1
        else:
            db.add(
                Employee(
                    full_name=full_name or email or "Сотрудник",
                    email=email,
                    internal_phone=user.get("phone"),
                    status="active",
                    external_id=external_id,
                )
            )
            created += 1
    db.commit()
    return {"created": created, "updated": updated}
