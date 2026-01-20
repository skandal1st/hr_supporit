from typing import Optional

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str
    role: str


class UserOut(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    role: Optional[str] = None


class PasswordReset(BaseModel):
    new_password: str
