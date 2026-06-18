from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.models.organization import Organization
from app.models.transaction import Transaction
from app.models.user import User

router = APIRouter(prefix="/reports", tags=["التقارير"])


@router.get("/governorate/{governorate_name}")
async def get_governorate_report(
    governorate_name: str,
    start_date: date = Query(..., description="تاريخ البداية"),
    end_date: date = Query(..., description="تاريخ النهاية"),
    current_user: User = Depends(require_permission("view_reports")),
    db: Session = Depends(get_db),
):
    """Aggregate data across all institutions in a governorate."""
    
    # Get all institutions in the governorate
    institutions = db.query(Organization).filter(
        Organization.governorate == governorate_name
    ).all()
    
    if not institutions:
        return {
            "governorate": governorate_name,
            "total_transactions": 0,
            "institutions": [],
        }
    
    institution_ids = [str(inst.id) for inst in institutions]
    
    # Count transactions for each institution
    transaction_counts = db.query(
        Transaction.sender_organization_id,
        func.count(Transaction.id)
    ).filter(
        Transaction.sender_organization_id.in_(institution_ids),
        Transaction.created_at >= start_date.isoformat(),
        Transaction.created_at <= f"{end_date.isoformat()}T23:59:59"
    ).group_by(Transaction.sender_organization_id).all()
    
    # Create mapping of institution_id to count
    count_map = dict(transaction_counts)
    
    # Build response
    institutions_data = []
    total_transactions = 0
    for inst in institutions:
        count = count_map.get(str(inst.id), 0)
        total_transactions += count
        institutions_data.append({
            "id": str(inst.id),
            "name": inst.name,
            "code": inst.code,
            "transaction_count": count,
        })
    
    return {
        "governorate": governorate_name,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_transactions": total_transactions,
        "institutions": institutions_data,
    }
