from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=80, description="اسم المستخدم")
    full_name: str = Field(..., min_length=1, max_length=180, description="الاسم الكامل")
    password: str = Field(..., min_length=8, max_length=128, description="كلمة المرور")
    role: str = Field(
        default="user",
        pattern="^(admin|supervisor|user|auditor)$",
        description="الصلاحية: admin, supervisor, user, auditor",
    )


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=180)
    role: Optional[str] = Field(None, pattern="^(admin|supervisor|user|auditor)$")
    password: Optional[str] = Field(None, min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: str
    username: str
    full_name: str
    role: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
