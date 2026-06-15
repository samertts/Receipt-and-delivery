import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.audit import log_audit
from app.core.exceptions import NotFoundError, ValidationError
from app.core.response_envelope import paginated_response
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
        if hasattr(item, "valid_count"):
            valid = item.valid_count
            damaged = item.damaged_count
            rejected = item.rejected_count
            nonconf = item.nonconforming_count
            total = item.total_count
        else:
            valid = item.get("valid_count", 0)
            damaged = item.get("damaged_count", 0)
            rejected = item.get("rejected_count", 0)
            nonconf = item.get("nonconforming_count", 0)
            total = item.get("total_count", 0)
        total_sub = valid + damaged + rejected + nonconf
        if total != total_sub:
            raise ValidationError(
                f"مجاميع العينة غير متطابقة في البند {i + 1}: "
                f"المجموع ({total}) != "
                f"صالح ({valid}) + تالف ({damaged}) + "
                f"مرفوض ({rejected}) + غير مطابق ({nonconf})",
            )


def _build_changes_dict(txn: Transaction, update_data: dict) -> dict:
    changes = {}
    for key, value in update_data.items():
        old = getattr(txn, key, None)
        if old != value:
            changes[key] = {"old": str(old) if old else "", "new": str(value) if value else ""}
    return changes


@router.get("")
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
    total_count = query.count()
    items = (
        query.order_by(Transaction.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return paginated_response(
        items=[TransactionResponse.model_validate(item).model_dump(mode="json") for item in items],
        total=total_count,
        page=page,
        per_page=limit,
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
        sender_job_title=payload.sender_job_title,
        receiver_job_title=payload.receiver_job_title,
        authorization_no=payload.authorization_no,
        authorization_date=payload.authorization_date,
        transaction_date=payload.transaction_date,
        notes=payload.notes,
        transport_info=payload.transport_info,
        status=payload.status,
        created_by=str(current_user.id),
    )
    db.add(txn)
    db.flush()

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

    db.commit()
    db.refresh(txn)

    log_audit(
        user_id=str(current_user.id),
        action_type="transaction_created",
        request=request,
        details=f"إنشاء معاملة: {txn.transaction_no} ({payload.transaction_type})",
        db=db,
        changes_json=json.dumps({"transaction_no": txn.transaction_no, "type": payload.transaction_type}),
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
    items_data = update_data.pop("items", None)

    changes = _build_changes_dict(txn, update_data)

    for key, value in update_data.items():
        setattr(txn, key, value)

    if items_data is not None:
        _validate_item_counts(
            [item for item in items_data if not item.get("delete")]
        )
        existing_ids = {str(item.id) for item in txn.items}

        for item_data in items_data:
            item_id = item_data.get("id")
            if item_id and item_id in existing_ids:
                item = db.query(TransactionItem).filter(TransactionItem.id == item_id).first()
                if item:
                    if item_data.get("delete"):
                        db.delete(item)
                        changes.setdefault("items_deleted", []).append(item_id)
                    else:
                        for k, v in item_data.items():
                            if k not in ("id", "delete") and v is not None:
                                setattr(item, k, v)
                        changes.setdefault("items_updated", []).append(item_id)
            elif not item_id and not item_data.get("delete"):
                item = TransactionItem(
                    transaction_id=str(txn.id),
                    sample_type=item_data.get("sample_type", ""),
                    total_count=item_data.get("total_count", 1),
                    valid_count=item_data.get("valid_count", 0),
                    damaged_count=item_data.get("damaged_count", 0),
                    rejected_count=item_data.get("rejected_count", 0),
                    nonconforming_count=item_data.get("nonconforming_count", 0),
                    transport_condition=item_data.get("transport_condition", ""),
                    notes=item_data.get("notes", ""),
                )
                db.add(item)
                changes.setdefault("items_added", []).append(1)

    db.commit()
    db.refresh(txn, ["items"])

    log_audit(
        user_id=str(current_user.id),
        action_type="transaction_updated",
        request=request,
        details=f"تحديث معاملة: {txn.transaction_no}",
        db=db,
        changes_json=json.dumps(changes) if changes else "",
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
        changes_json=json.dumps({"transaction_no": txn.transaction_no}),
    )
