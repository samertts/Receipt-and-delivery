from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.container_deps import get_transaction_service
from app.api.deps import require_permission
from app.core.response_envelope import paginated_response
from app.db.session import get_db
from app.models.user import User
from app.services.notification_service import build_transaction_notification, notification_manager
from app.schemas.transaction import (
    CustodyEventResponse,
    CustodyTransitionRequest,
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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("create_transaction")),
):
    svc = get_transaction_service(db)
    transaction = svc.create_transaction(
        payload=payload.model_dump(),
        request=request,
        current_user=current_user,
    )
    background_tasks.add_task(
        notification_manager.publish,
        build_transaction_notification(
            event="created",
            transaction_id=str(transaction.id),
            transaction_no=transaction.transaction_no,
            status=transaction.status,
            actor_username=current_user.username,
        ),
    )
    return transaction


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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("edit_transaction")),
):
    svc = get_transaction_service(db)
    update_data = payload.model_dump(exclude_unset=True)
    transaction = svc.update_transaction(
        txn_id,
        update_data=update_data,
        request=request,
        current_user=current_user,
    )
    background_tasks.add_task(
        notification_manager.publish,
        build_transaction_notification(
            event="status_changed" if "status" in update_data else "updated",
            transaction_id=str(transaction.id),
            transaction_no=transaction.transaction_no,
            status=transaction.status,
            actor_username=current_user.username,
        ),
    )
    return transaction


@router.post("/{txn_id}/custody", response_model=CustodyEventResponse, status_code=201)
def transition_custody(
    txn_id: str,
    payload: CustodyTransitionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("edit_transaction")),
):
    svc = get_transaction_service(db)
    event = svc.transition_custody(
        txn_id,
        payload=payload.model_dump(exclude_none=True),
        request=request,
        current_user=current_user,
    )
    transaction = svc.get_transaction(txn_id)
    background_tasks.add_task(
        notification_manager.publish,
        build_transaction_notification(
            event="status_changed",
            transaction_id=str(transaction.id),
            transaction_no=transaction.transaction_no,
            status=event.to_state,
            actor_username=current_user.username,
        ),
    )
    return event


@router.delete("/{txn_id}", status_code=204)
def delete_transaction(
    txn_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("delete_transaction")),
):
    svc = get_transaction_service(db)
    transaction = svc.get_transaction(txn_id)
    svc.delete_transaction(txn_id, request=request, current_user=current_user)
    background_tasks.add_task(
        notification_manager.publish,
        build_transaction_notification(
            event="deleted",
            transaction_id=str(transaction.id),
            transaction_no=transaction.transaction_no,
            status=transaction.status,
            actor_username=current_user.username,
        ),
    )
