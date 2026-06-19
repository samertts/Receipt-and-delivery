from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.container_deps import get_transaction_service
from app.api.deps import require_permission
from app.core.response_envelope import paginated_response
from app.db.session import get_db
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)

router = APIRouter(prefix="/transactions", tags=["المعاملات"])


@router.get("")
def list_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    status: str = Query("", description="تصفية حسب الحالة"),
    search: str = Query("", description="بحث في رقم المعاملة"),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("view_transactions")),
):
    svc = get_transaction_service(db)
    items, total = svc.list_transactions(
        page=page, limit=limit, status=status, search=search
    )
    return paginated_response(
        items=[
            TransactionResponse.model_validate(item).model_dump(mode="json")
            for item in items
        ],
        total=total,
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
    svc = get_transaction_service(db)
    return svc.create_transaction(
        payload=payload.model_dump(),
        request=request,
        current_user=current_user,
    )


@router.get("/{txn_id}", response_model=TransactionResponse)
def get_transaction(
    txn_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("view_transactions")),
):
    svc = get_transaction_service(db)
    return svc.get_transaction(txn_id)


@router.put("/{txn_id}", response_model=TransactionResponse)
def update_transaction(
    txn_id: str,
    payload: TransactionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("edit_transaction")),
):
    svc = get_transaction_service(db)
    return svc.update_transaction(
        txn_id,
        update_data=payload.model_dump(exclude_unset=True),
        request=request,
        current_user=current_user,
    )


@router.delete("/{txn_id}", status_code=204)
def delete_transaction(
    txn_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("delete_transaction")),
):
    svc = get_transaction_service(db)
    svc.delete_transaction(txn_id, request=request, current_user=current_user)
