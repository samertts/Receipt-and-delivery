from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.response_envelope import wrap_response
from app.db.session import get_db
from app.models.organization import Organization
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import TransactionResponse

router = APIRouter(prefix="/dashboard", tags=["لوحة التحكم"])

_STATUS_KEYS = ("approved", "draft", "rejected", "archived", "cancelled")


def _start_of_day(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def _end_of_day(value: date) -> datetime:
    return datetime.combine(value + timedelta(days=1), time.min, tzinfo=timezone.utc)


def _percentage_change(current: int, previous: int) -> int:
    if previous == 0:
        return 0 if current == 0 else 100
    return round(((current - previous) / previous) * 100)


@router.get("/summary")
def dashboard_summary(
    days: int = Query(7, ge=7, le=90, description="عدد الأيام في الاتجاه اليومي"),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("view_dashboard")),
):
    """Return the dashboard KPIs and chart series in one API response."""
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=days - 1)
    start_dt = _start_of_day(start_date)
    end_dt = _end_of_day(today)
    previous_start_dt = start_dt - timedelta(days=days)

    total_transactions = db.query(func.count(Transaction.id)).scalar() or 0
    total_organizations = db.query(func.count(Organization.id)).scalar() or 0

    status_rows = (
        db.query(Transaction.status, func.count(Transaction.id))
        .group_by(Transaction.status)
        .all()
    )
    by_status = {key: 0 for key in _STATUS_KEYS}
    for status, count in status_rows:
        by_status[status or "unknown"] = count

    current_status_rows = (
        db.query(Transaction.status, func.count(Transaction.id))
        .filter(Transaction.created_at >= start_dt, Transaction.created_at < end_dt)
        .group_by(Transaction.status)
        .all()
    )
    previous_status_rows = (
        db.query(Transaction.status, func.count(Transaction.id))
        .filter(
            Transaction.created_at >= previous_start_dt,
            Transaction.created_at < start_dt,
        )
        .group_by(Transaction.status)
        .all()
    )
    current_by_status = {key: 0 for key in _STATUS_KEYS}
    previous_by_status = {key: 0 for key in _STATUS_KEYS}
    for status, count in current_status_rows:
        current_by_status[status or "unknown"] = count
    for status, count in previous_status_rows:
        previous_by_status[status or "unknown"] = count

    current_total = sum(current_by_status.values())
    previous_total = sum(previous_by_status.values())
    current_orgs = (
        db.query(func.count(Organization.id))
        .filter(Organization.created_at >= start_dt, Organization.created_at < end_dt)
        .scalar()
        or 0
    )
    previous_orgs = (
        db.query(func.count(Organization.id))
        .filter(
            Organization.created_at >= previous_start_dt,
            Organization.created_at < start_dt,
        )
        .scalar()
        or 0
    )
    trends = {
        "total": _percentage_change(current_total, previous_total),
        "approved": _percentage_change(current_by_status.get("approved", 0), previous_by_status.get("approved", 0)),
        "draft": _percentage_change(current_by_status.get("draft", 0), previous_by_status.get("draft", 0)),
        "orgs": _percentage_change(current_orgs, previous_orgs),
    }

    type_rows = (
        db.query(Transaction.transaction_type, func.count(Transaction.id))
        .group_by(Transaction.transaction_type)
        .order_by(func.count(Transaction.id).desc())
        .limit(8)
        .all()
    )
    by_type = [
        {"key": transaction_type or "غير محدد", "count": count}
        for transaction_type, count in type_rows
    ]

    day_expression = func.date(Transaction.created_at)
    daily_rows = (
        db.query(day_expression.label("day"), func.count(Transaction.id))
        .filter(Transaction.created_at >= start_dt, Transaction.created_at < end_dt)
        .group_by(day_expression)
        .order_by(day_expression)
        .all()
    )
    daily_counts = {}
    for day, count in daily_rows:
        day_key = day.isoformat() if hasattr(day, "isoformat") else str(day)
        daily_counts[day_key] = count

    trend = [
        {
            "date": (start_date + timedelta(days=offset)).isoformat(),
            "count": daily_counts.get(
                (start_date + timedelta(days=offset)).isoformat(),
                0,
            ),
        }
        for offset in range(days)
    ]

    recent_transactions = (
        db.query(Transaction)
        .order_by(Transaction.created_at.desc())
        .limit(5)
        .all()
    )

    return wrap_response(
        data={
            "summary": {
                "total_transactions": total_transactions,
                "total_organizations": total_organizations,
                "by_status": by_status,
            },
            "trends": trends,
            "trend": trend,
            "by_type": by_type,
            "recent_transactions": [
                TransactionResponse.model_validate(item).model_dump(mode="json")
                for item in recent_transactions
            ],
        },
        message="تم تحميل إحصائيات لوحة التحكم بنجاح",
        meta={"days": days, "start_date": start_date.isoformat(), "end_date": today.isoformat()},
    )
