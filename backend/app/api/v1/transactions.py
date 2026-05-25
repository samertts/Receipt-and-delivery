from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.transaction import Transaction
from app.models.transaction_item import TransactionItem
from app.schemas.transaction import TransactionCreate

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("")
def list_transactions(page: int = Query(1, ge=1), limit: int = Query(20, le=100), db: Session = Depends(get_db), _=Depends(get_current_user)):
    query = db.query(Transaction).order_by(Transaction.created_at.desc())
    total = query.count()
    data = query.offset((page - 1) * limit).limit(limit).all()
    return {"total": total, "items": data}


@router.post("")
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    for item in payload.items:
        if item.total_count != (item.valid_count + item.damaged_count + item.rejected_count + item.nonconforming_count):
            raise HTTPException(status_code=422, detail="مجاميع العينة غير متطابقة")

    txn = Transaction(transaction_no=f"TXN-{payload.transaction_date.replace('-', '')}", **payload.model_dump(exclude={"items"}))
    db.add(txn)
    db.flush()
    for item in payload.items:
        db.add(TransactionItem(transaction_id=str(txn.id), **item.model_dump()))
    db.commit()
    db.refresh(txn)
    return txn
