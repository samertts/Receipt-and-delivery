from app.models.organization import Organization
from app.models.transaction import Transaction
from app.models.transaction_item import TransactionItem
from app.models.user import User
from app.repositories.base import BaseRepository


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
    ) -> tuple[list[Transaction], int]:
        filters = {}
        if status:
            filters["status"] = status
        items, total = self.list(page=page, limit=limit, filters=filters, order_by="created_at", desc=True)
        if search:
            items = [i for i in items if search.lower() in (i.transaction_no or "").lower()]
            total = len(items)
        return items, total
