"""Transaction service — business logic for transaction CRUD and deep updates."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.audit import log_audit
from app.core.exceptions import NotFoundError, ValidationError
from app.models.transaction import Transaction
from app.models.transaction_item import TransactionItem
from app.models.user import User
from app.repositories import TransactionRepository


class TransactionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TransactionRepository(db)

    def list_transactions(
        self,
        page: int = 1,
        limit: int = 20,
        status: str = "",
        search: str = "",
    ) -> tuple[list[Transaction], int]:
        return self.repo.list_with_filters(page=page, limit=limit, status=status, search=search)

    def create_transaction(
        self,
        payload: dict[str, Any],
        request: Any = None,
        current_user: User | None = None,
    ) -> Transaction:
        items = payload.get("items", [])
        self._validate_item_counts(items)

        # Generate transaction number
        transaction_no = self._generate_transaction_no(payload["transaction_type"])
        
        # Create transaction object
        txn = Transaction(
            transaction_no=transaction_no,
            transaction_type=payload["transaction_type"],
            sender_organization_id=payload["sender_organization_id"],
            receiver_organization_id=payload["receiver_organization_id"],
            sender_name=payload["sender_name"],
            receiver_name=payload["receiver_name"],
            sender_job_title=payload.get("sender_job_title", ""),
            receiver_job_title=payload.get("receiver_job_title", ""),
            authorization_no=payload.get("authorization_no", ""),
            authorization_date=payload.get("authorization_date", ""),
            transaction_date=payload["transaction_date"],
            notes=payload.get("notes", ""),
            transport_info=payload.get("transport_info", ""),
            status=payload.get("status", "draft"),
            created_by=str(current_user.id) if current_user else "",
        )
        self.db.add(txn)
        self.db.flush()  # Get the ID without committing
        
        for item_data in items:
            item = TransactionItem(
                transaction_id=str(txn.id),
                sample_type=item_data.get("sample_type", item_data.sample_type if hasattr(item_data, "sample_type") else ""),
                total_count=item_data.get("total_count", item_data.total_count if hasattr(item_data, "total_count") else 0),
                valid_count=item_data.get("valid_count", item_data.valid_count if hasattr(item_data, "valid_count") else 0),
                damaged_count=item_data.get("damaged_count", item_data.damaged_count if hasattr(item_data, "damaged_count") else 0),
                rejected_count=item_data.get("rejected_count", item_data.rejected_count if hasattr(item_data, "rejected_count") else 0),
                nonconforming_count=item_data.get("nonconforming_count", item_data.nonconforming_count if hasattr(item_data, "nonconforming_count") else 0),
                transport_condition=item_data.get("transport_condition", item_data.transport_condition if hasattr(item_data, "transport_condition") else ""),
                notes=item_data.get("notes", item_data.notes if hasattr(item_data, "notes") else ""),
            )
            self.db.add(item)
        
        self.db.commit()
        self.db.refresh(txn)

        log_audit(
            user_id=str(current_user.id) if current_user else "system",
            action_type="transaction_created",
            request=request,
            details=f"إنشاء معاملة: {txn.transaction_no} ({payload['transaction_type']})",
            db=self.db,
            changes_json=json.dumps({"transaction_no": txn.transaction_no, "type": payload["transaction_type"]}),
        )
        return txn

    def get_transaction(self, txn_id: str) -> Transaction:
        txn = self.repo.find_by_id_with_items(txn_id)
        if not txn:
            raise NotFoundError("المعاملة غير موجودة")
        return txn

    def update_transaction(
        self,
        txn_id: str,
        update_data: dict[str, Any],
        request: Any = None,
        current_user: User | None = None,
    ) -> Transaction:
        txn = self.repo.find_by_id_with_items(txn_id)
        if not txn:
            raise NotFoundError("المعاملة غير موجودة")

        items_data = update_data.pop("items", None)
        changes = self._build_changes_dict(txn, update_data)

        for key, value in update_data.items():
            setattr(txn, key, value)

        if items_data is not None:
            self._validate_item_counts(
                [item for item in items_data if not item.get("delete")]
            )
            existing_ids = {str(item.id) for item in txn.items}

            for item_data in items_data:
                item_id = item_data.get("id")
                if item_id and item_id in existing_ids:
                    item = self.db.query(TransactionItem).filter(TransactionItem.id == item_id).first()
                    if item:
                        if item_data.get("delete"):
                            self.db.delete(item)
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
                    self.db.add(item)
                    changes.setdefault("items_added", []).append(1)

        self.db.commit()
        self.db.refresh(txn, ["items"])

        log_audit(
            user_id=str(current_user.id) if current_user else "system",
            action_type="transaction_updated",
            request=request,
            details=f"تحديث معاملة: {txn.transaction_no}",
            db=self.db,
            changes_json=json.dumps(changes) if changes else "",
        )
        return txn

    def delete_transaction(
        self,
        txn_id: str,
        request: Any = None,
        current_user: User | None = None,
    ) -> None:
        txn = self.repo.get(txn_id)
        if not txn:
            raise NotFoundError("المعاملة غير موجودة")
        self.repo.delete(txn_id)

        log_audit(
            user_id=str(current_user.id) if current_user else "system",
            action_type="transaction_deleted",
            request=request,
            details=f"حذف معاملة: {txn.transaction_no}",
            db=self.db,
            changes_json=json.dumps({"transaction_no": txn.transaction_no}),
        )

    @staticmethod
    def _generate_transaction_no(txn_type: str) -> str:
        return f"TXN-{txn_type[:3].upper()}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    @staticmethod
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

    @staticmethod
    def _build_changes_dict(txn: Transaction, update_data: dict) -> dict:
        changes = {}
        for key, value in update_data.items():
            old = getattr(txn, key, None)
            if old != value:
                changes[key] = {"old": str(old) if old else "", "new": str(value) if value else ""}
        return changes
