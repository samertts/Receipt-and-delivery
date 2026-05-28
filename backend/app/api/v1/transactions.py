from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permission
from app.core.audit import log_audit
from app.core.exceptions import NotFoundError, ValidationError
from app.db.session import get_db
from app.models.transaction import Transaction
from app.models.transaction_item import TransactionItem
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)

router = APIRouter(prefix="/transactions", tags=["المعاملات"])


def _generate_transaction_no(txn_type: str) -> str:
    return f"TXN-{txn_type[:3].upper()}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def _validate_item_counts(items: list) -> None:
    for i, item in enumerate(items):
        total = (
            item.valid_count
            + item.damaged_count
            + item.rejected_count
            + item.nonconforming_count
        )
        if item.total_count != total:
            raise ValidationError(
                f"مجاميع العينة غير متطابقة في البند {i + 1}: "
                f"المجموع ({item.total_count}) != "
                f"صالح ({item.valid_count}) + تالف ({item.damaged_count}) + "
                f"مرفوض ({item.rejected_count}) + غير مطابق ({item.nonconforming_count})"
            )


@router.get("", response_model=list[TransactionResponse])
def list_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    status: str = Query("", description="تصفية حسب الحالة"),
    search: str = Query("", description="بحث في رقم المعاملة"),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("view_transactions")),
):
    query = db.query(Transaction)
    if status:
        query = query.filter(Transaction.status == status)
    if search:
        query = query.filter(Transaction.transaction_no.ilike(f"%{search}%"))
    return (
        query.order_by(Transaction.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )


@router.post("", response_model=TransactionResponse, status_code=201)
def create_transaction(
    payload: TransactionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("create_transaction")),
):
    _validate_item_counts(payload.items)

    txn = Transaction(
        transaction_no=_generate_transaction_no(payload.transaction_type),
        transaction_type=payload.transaction_type,
        sender_organization_id=payload.sender_organization_id,
        receiver_organization_id=payload.receiver_organization_id,
        sender_name=payload.sender_name,
        receiver_name=payload.receiver_name,
        authorization_no=payload.authorization_no,
        authorization_date=payload.authorization_date,
        transaction_date=payload.transaction_date,
        notes=payload.notes,
        status=payload.status,
    )
    db.add(txn)
    db.flush()

    items = []
    for item_data in payload.items:
        item = TransactionItem(
            transaction_id=str(txn.id),
            sample_type=item_data.sample_type,
            total_count=item_data.total_count,
            valid_count=item_data.valid_count,
            damaged_count=item_data.damaged_count,
            rejected_count=item_data.rejected_count,
            nonconforming_count=item_data.nonconforming_count,
            transport_condition=item_data.transport_condition,
            notes=item_data.notes,
        )
        db.add(item)
        items.append(item)

    db.commit()
    db.refresh(txn)

    log_audit(
        user_id=str(current_user.id),
        action_type="transaction_created",
        request=request,
        details=f"إنشاء معاملة: {txn.transaction_no} ({payload.transaction_type})",
        db=db,
    )
    return txn


@router.get("/{txn_id}", response_model=TransactionResponse)
def get_transaction(
    txn_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("view_transactions")),
):
    txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
    if not txn:
        raise NotFoundError("المعاملة غير موجودة")
    return txn


@router.put("/{txn_id}", response_model=TransactionResponse)
def update_transaction(
    txn_id: str,
    payload: TransactionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("edit_transaction")),
):
    txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
    if not txn:
        raise NotFoundError("المعاملة غير موجودة")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(txn, key, value)

    db.commit()
    db.refresh(txn)

    log_audit(
        user_id=str(current_user.id),
        action_type="transaction_updated",
        request=request,
        details=f"تحديث معاملة: {txn.transaction_no}",
        db=db,
    )
    return txn


@router.delete("/{txn_id}", status_code=204)
def delete_transaction(
    txn_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("delete_transaction")),
):
    txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
    if not txn:
        raise NotFoundError("المعاملة غير موجودة")
    db.delete(txn)
    db.commit()

    log_audit(
        user_id=str(current_user.id),
        action_type="transaction_deleted",
        request=request,
        details=f"حذف معاملة: {txn.transaction_no}",
        db=db,
    )
