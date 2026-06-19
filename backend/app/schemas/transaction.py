from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TransactionItemCreate(BaseModel):
    sample_type: str = Field(..., min_length=1, max_length=80)
    total_count: int = Field(..., ge=1)
    valid_count: int = Field(..., ge=0)
    damaged_count: int = Field(..., ge=0)
    rejected_count: int = Field(..., ge=0)
    nonconforming_count: int = Field(..., ge=0)
    transport_condition: str = Field(default="", max_length=100)
    notes: str = Field(default="", max_length=500)


class TransactionItemResponse(BaseModel):
    id: str
    sample_type: str
    total_count: int
    valid_count: int
    damaged_count: int
    rejected_count: int
    nonconforming_count: int
    transport_condition: str
    notes: str

    model_config = {"from_attributes": True}


class TransactionCreate(BaseModel):
    transaction_type: str = Field(..., min_length=1, max_length=60)
    sender_organization_id: str
    receiver_organization_id: str
    sender_name: str = Field(..., min_length=1, max_length=180)
    receiver_name: str = Field(..., min_length=1, max_length=180)
    sender_job_title: str = Field(default="", max_length=80)
    receiver_job_title: str = Field(default="", max_length=80)
    authorization_no: str = Field(default="", max_length=100)
    authorization_date: str = Field(default="", max_length=20)
    transaction_date: str = Field(..., max_length=30)
    notes: str = Field(default="", max_length=2000)
    transport_info: str = Field(default="", max_length=255)
    status: str = Field(
        default="draft", pattern="^(draft|approved|rejected|archived|cancelled)$"
    )
    items: list[TransactionItemCreate] = Field(..., min_length=1)


class TransactionItemUpdate(BaseModel):
    id: Optional[str] = None
    sample_type: Optional[str] = Field(None, min_length=1, max_length=80)
    total_count: Optional[int] = Field(None, ge=1)
    valid_count: Optional[int] = Field(None, ge=0)
    damaged_count: Optional[int] = Field(None, ge=0)
    rejected_count: Optional[int] = Field(None, ge=0)
    nonconforming_count: Optional[int] = Field(None, ge=0)
    transport_condition: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)
    delete: bool = False


class TransactionUpdate(BaseModel):
    transaction_type: Optional[str] = Field(None, min_length=1, max_length=60)
    sender_organization_id: Optional[str] = None
    receiver_organization_id: Optional[str] = None
    sender_name: Optional[str] = Field(None, min_length=1, max_length=180)
    receiver_name: Optional[str] = Field(None, min_length=1, max_length=180)
    sender_job_title: Optional[str] = Field(None, max_length=80)
    receiver_job_title: Optional[str] = Field(None, max_length=80)
    authorization_no: Optional[str] = Field(None, max_length=100)
    authorization_date: Optional[str] = Field(None, max_length=20)
    transaction_date: Optional[str] = Field(None, max_length=30)
    notes: Optional[str] = Field(None, max_length=2000)
    transport_info: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(
        None, pattern="^(draft|approved|rejected|archived|cancelled)$"
    )
    items: Optional[list[TransactionItemUpdate]] = None


class TransactionResponse(BaseModel):
    id: str
    transaction_no: str
    transaction_type: str
    sender_organization_id: str
    receiver_organization_id: str
    sender_name: str
    receiver_name: str
    sender_job_title: str = ""
    receiver_job_title: str = ""
    authorization_no: str
    authorization_date: str
    transaction_date: str
    notes: str
    transport_info: str = ""
    status: str
    created_by: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: list[TransactionItemResponse] = []

    model_config = {"from_attributes": True}


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    address: str = Field(default="", max_length=255)
    phone: str = Field(default="", max_length=50)
    email: str = Field(default="", max_length=150)
    logo_path: str = Field(default="", max_length=255)


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    address: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=150)


class OrganizationResponse(BaseModel):
    id: str
    name: str
    code: str
    address: str
    phone: str
    email: str
    logo_path: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AuditLogResponse(BaseModel):
    id: str
    user_id: str
    action_type: str
    ip_address: str
    details: str
    changes_json: str = ""
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
