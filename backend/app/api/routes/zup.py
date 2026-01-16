"""
API endpoints для интеграции с 1С ЗУП.

Поддерживает:
- Ручную синхронизацию данных
- Webhook для событий приёма/увольнения
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.config import settings
from app.services.zup import (
    process_zup_fire_event,
    process_zup_hire_event,
    sync_all_from_zup,
    sync_departments_from_zup,
    sync_employees_from_zup,
    sync_positions_from_zup,
)


router = APIRouter(prefix="/zup", tags=["zup"])


# === Схемы для webhook ===

class ZupHireEvent(BaseModel):
    """Событие приёма на работу из 1С ЗУП"""
    employee_id: str  # external_id сотрудника в ЗУП
    full_name: str
    department: Optional[str] = None
    position: Optional[str] = None
    effective_date: Optional[date] = None
    needs_it_equipment: bool = True


class ZupFireEvent(BaseModel):
    """Событие увольнения из 1С ЗУП"""
    employee_id: str  # external_id сотрудника в ЗУП
    effective_date: Optional[date] = None


class ZupWebhookPayload(BaseModel):
    """Payload для webhook от 1С ЗУП"""
    event_type: str  # "hire" или "fire"
    data: dict


# === Ручная синхронизация ===

@router.post("/sync/all", dependencies=[Depends(require_roles(["hr", "it", "admin"]))])
def sync_all(db: Session = Depends(get_db)) -> dict:
    """
    Полная синхронизация всех данных из 1С ЗУП.
    Порядок: отделы → должности → сотрудники
    """
    if not settings.zup_api_url:
        raise HTTPException(status_code=400, detail="ZUP_API_URL не настроен")
    
    return sync_all_from_zup(db)


@router.post("/sync/departments", dependencies=[Depends(require_roles(["hr", "it", "admin"]))])
def sync_departments(db: Session = Depends(get_db)) -> dict:
    """Синхронизация подразделений из 1С ЗУП"""
    if not settings.zup_api_url:
        raise HTTPException(status_code=400, detail="ZUP_API_URL не настроен")
    
    result = sync_departments_from_zup(db)
    return {
        "created": result.created,
        "updated": result.updated,
        "errors": result.errors,
    }


@router.post("/sync/positions", dependencies=[Depends(require_roles(["hr", "it", "admin"]))])
def sync_positions(db: Session = Depends(get_db)) -> dict:
    """Синхронизация должностей из 1С ЗУП"""
    if not settings.zup_api_url:
        raise HTTPException(status_code=400, detail="ZUP_API_URL не настроен")
    
    result = sync_positions_from_zup(db)
    return {
        "created": result.created,
        "updated": result.updated,
        "errors": result.errors,
    }


@router.post("/sync/employees", dependencies=[Depends(require_roles(["hr", "it", "admin"]))])
def sync_employees(db: Session = Depends(get_db)) -> dict:
    """Синхронизация сотрудников из 1С ЗУП"""
    if not settings.zup_api_url:
        raise HTTPException(status_code=400, detail="ZUP_API_URL не настроен")
    
    result = sync_employees_from_zup(db)
    return {
        "created": result.created,
        "updated": result.updated,
        "errors": result.errors,
    }


# === Webhook для событий из 1С ЗУП ===

def verify_zup_webhook_token(x_zup_token: Optional[str] = Header(None)) -> bool:
    """Проверяет токен webhook от 1С ЗУП"""
    if not settings.zup_webhook_token:
        # Если токен не настроен, пропускаем проверку (для тестирования)
        return True
    
    if not x_zup_token or x_zup_token != settings.zup_webhook_token:
        raise HTTPException(status_code=401, detail="Неверный токен webhook")
    
    return True


@router.post("/webhook")
def zup_webhook(
    payload: ZupWebhookPayload,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_zup_webhook_token),
) -> dict:
    """
    Webhook для получения событий из 1С ЗУП.
    
    Поддерживаемые типы событий:
    - hire: приём на работу
    - fire: увольнение
    
    Пример payload:
    ```json
    {
        "event_type": "hire",
        "data": {
            "employee_id": "12345-guid",
            "full_name": "Иванов Иван Иванович",
            "department": "Отдел продаж",
            "position": "Менеджер",
            "effective_date": "2024-01-15",
            "needs_it_equipment": true
        }
    }
    ```
    """
    event_type = payload.event_type.lower()
    data = payload.data
    
    if event_type == "hire":
        # Приём на работу
        effective_date = None
        if data.get("effective_date"):
            try:
                effective_date = date.fromisoformat(str(data["effective_date"]))
            except ValueError:
                pass
        
        result = process_zup_hire_event(
            db=db,
            employee_external_id=data.get("employee_id", ""),
            full_name=data.get("full_name", ""),
            department_name=data.get("department"),
            position_name=data.get("position"),
            effective_date=effective_date,
            needs_it_equipment=data.get("needs_it_equipment", True),
        )
        return {"status": "ok", "event": "hire", "result": result}
    
    elif event_type == "fire":
        # Увольнение
        effective_date = None
        if data.get("effective_date"):
            try:
                effective_date = date.fromisoformat(str(data["effective_date"]))
            except ValueError:
                pass
        
        result = process_zup_fire_event(
            db=db,
            employee_external_id=data.get("employee_id", ""),
            effective_date=effective_date,
        )
        return {"status": "ok", "event": "fire", "result": result}
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Неизвестный тип события: {event_type}. Поддерживаются: hire, fire"
        )


# === Отдельные endpoints для событий (альтернатива webhook) ===

@router.post("/event/hire", dependencies=[Depends(require_roles(["hr", "admin"]))])
def handle_hire_event(
    event: ZupHireEvent,
    db: Session = Depends(get_db),
) -> dict:
    """
    Обработка события приёма на работу.
    Можно вызывать из 1С ЗУП или вручную.
    """
    result = process_zup_hire_event(
        db=db,
        employee_external_id=event.employee_id,
        full_name=event.full_name,
        department_name=event.department,
        position_name=event.position,
        effective_date=event.effective_date,
        needs_it_equipment=event.needs_it_equipment,
    )
    return {"status": "ok", "result": result}


@router.post("/event/fire", dependencies=[Depends(require_roles(["hr", "admin"]))])
def handle_fire_event(
    event: ZupFireEvent,
    db: Session = Depends(get_db),
) -> dict:
    """
    Обработка события увольнения.
    Можно вызывать из 1С ЗУП или вручную.
    """
    result = process_zup_fire_event(
        db=db,
        employee_external_id=event.employee_id,
        effective_date=event.effective_date,
    )
    return {"status": "ok", "result": result}
