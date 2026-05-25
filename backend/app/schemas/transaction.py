from pydantic import BaseModel, Field


class TransactionItemCreate(BaseModel):
    sample_type: str
    total_count: int
    valid_count: int
    damaged_count: int
    rejected_count: int
    nonconforming_count: int
    transport_condition: str
    notes: str = ""


class TransactionCreate(BaseModel):
    transaction_type: str
    sender_organization_id: str
    receiver_organization_id: str
    sender_name: str
    receiver_name: str
    authorization_no: str
    authorization_date: str
    transaction_date: str
    notes: str = ""
    status: str = Field(default="draft")
    items: list[TransactionItemCreate]
