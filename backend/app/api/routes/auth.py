from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserOut
from app.services.audit import log_action


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль")
    token = create_access_token(subject=user.username, role=user.role)
    return Token(access_token=token)


@router.post("/bootstrap", response_model=UserOut)
def bootstrap_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    existing = db.query(User).count()
    if existing > 0:
        raise HTTPException(status_code=403, detail="Bootstrap уже выполнен")
    user = User(
        username=payload.username,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_action(db, user.username, "bootstrap", "user", f"role={user.role}")
    return user


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return current_user
