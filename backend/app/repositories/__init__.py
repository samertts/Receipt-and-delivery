from app.models.audit_log import AuditLog
from app.models.organization import Organization
from app.models.sync_log import SyncLog
from app.models.transaction import Transaction
from app.models.transaction_item import TransactionItem as TransactionItem  # noqa: F401
from app.models.user import User
from app.repositories.base import BaseRepository


def escape_like(value: str) -> str:
    """Escape special characters for SQL LIKE patterns."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class UserRepository(BaseRepository[User]):
    def __init__(self, db):
        super().__init__(User, db)

    def find_by_username(self, username: str) -> User | None:
        return self.db.query(User).filter(User.username == username).first()


class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self, db):
        super().__init__(Organization, db)


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, db):
        super().__init__(Transaction, db)

    def list_with_filters(
        self,
        page: int = 1,
        limit: int = 20,
        status: str = "",
        search: str = "",
        institution_id: str = "",
    ) -> tuple[list[Transaction], int]:
        query = self.db.query(Transaction)
        if status:
            query = query.filter(Transaction.status == status)
        if search:
            search_term = f"%{escape_like(search)}%"
            query = query.filter(
                Transaction.transaction_no.ilike(search_term, escape="\\")
            )
        if institution_id:
            # Filter by institution through organization relationships
            query = query.filter(
                (Transaction.sender_organization_id == institution_id)
                | (Transaction.receiver_organization_id == institution_id)
            )
        total = query.count()
        items = (
            query.order_by(Transaction.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )
        return items, total

    def find_by_id_with_items(self, txn_id: str) -> Transaction | None:
        from sqlalchemy.orm import joinedload

        return (
            self.db.query(Transaction)
            .options(
                joinedload(Transaction.items),
            )
            .filter(Transaction.id == txn_id)
            .first()
        )

    def find_by_transaction_no(self, txn_no: str) -> Transaction | None:
        return (
            self.db.query(Transaction)
            .filter(
                Transaction.transaction_no == txn_no,
            )
            .first()
        )


class AuditRepository(BaseRepository[AuditLog]):
    def __init__(self, db):
        super().__init__(AuditLog, db)

    def list_with_filters(
        self,
        page: int = 1,
        limit: int = 50,
        action_type: str = "",
    ) -> tuple[list[AuditLog], int]:
        filters = {}
        if action_type:
            filters["action_type"] = action_type
        return self.list(
            page=page, limit=limit, filters=filters, order_by="created_at", desc=True
        )


class SyncRepository(BaseRepository[SyncLog]):
    def __init__(self, db):
        super().__init__(SyncLog, db)

    def find_since(self, since_dt, device_id: str = "", limit: int = 100):
        query = self.db.query(SyncLog)
        if since_dt is not None:
            query = query.filter(SyncLog.synced_at > since_dt)
        if device_id:
            query = query.filter(SyncLog.device_id == device_id)
        return query.order_by(SyncLog.synced_at.asc()).limit(limit).all()

    def get_latest(self):
        return self.db.query(SyncLog).order_by(SyncLog.synced_at.desc()).first()

    def count_all(self) -> int:
        return self.db.query(SyncLog).count()
