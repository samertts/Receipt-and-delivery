"""Receipt service integration tests."""

import os
import sys
from datetime import datetime

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

ADMIN_USER = {"id": 1, "username": "admin", "role": "Admin", "status": "Active"}


def _seed_base(conn):
    """Insert base data needed for receipt operations."""
    from lab_system.app.auth.security import hash_password
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("INSERT OR IGNORE INTO users(username,password_hash,full_name,role,status,password_changed_at) VALUES(?,?,?,?,?,?)",
                 ("admin", hash_password("Admin@123"), "Admin User", "Admin", "Active", ""))
    conn.execute("INSERT OR IGNORE INTO transaction_types(name) VALUES(?)", ("Receipt",))
    conn.execute("INSERT OR IGNORE INTO transaction_types(name) VALUES(?)", ("Delivery",))
    conn.execute("INSERT OR IGNORE INTO sample_types(name,category,status) VALUES(?,?,?)", ("Blood", "Biological", "Active"))
    conn.execute("INSERT OR IGNORE INTO sample_types(name,category,status) VALUES(?,?,?)", ("Urine", "Biological", "Active"))
    conn.execute("INSERT OR IGNORE INTO organizations(name,code,org_type,governorate,status) VALUES(?,?,?,?,?)",
                 ("Lab A", "LA", "Laboratory", "Baghdad", "Active"))
    conn.execute("INSERT OR IGNORE INTO organizations(name,code,org_type,governorate,status) VALUES(?,?,?,?,?)",
                 ("Lab B", "LB", "Laboratory", "Erbil", "Active"))
    conn.commit()


def _get_ids(conn):
    tx_id = conn.execute("SELECT id FROM transaction_types WHERE name='Receipt'").fetchone()[0]
    org_a = conn.execute("SELECT id FROM organizations WHERE code='LA'").fetchone()[0]
    org_b = conn.execute("SELECT id FROM organizations WHERE code='LB'").fetchone()[0]
    st_id = conn.execute("SELECT id FROM sample_types WHERE name='Blood'").fetchone()[0]
    return tx_id, org_a, org_b, st_id


def _create_receipt(fresh_db, seed_data, receipt_no_suffix=None, status="Draft"):
    import lab_system.app.database.db as _db
    with _db.get_conn() as conn:
        _seed_base(conn)
        tx_id, org_a, org_b, st_id = _get_ids(conn)

    from lab_system.app.services.receipt_service import create_receipt
    return create_receipt(
        data={
            "tx_type_id": tx_id,
            "sender_org_id": org_a,
            "receiver_org_id": org_b,
            "sender_name": "Ahmed",
            "receiver_name": "Ali",
            "sender_job_title": "Tech",
            "receiver_job_title": "Manager",
            "auth_doc_no": "AUTH-001",
            "auth_date": "2026-01-01",
            "notes": "Test receipt",
            "transport_info": "Truck",
            "additional_comments": "",
            "status": status,
        },
        items=[{
            "sample_type_id": st_id,
            "name": "Blood Test",
            "total_count": 10,
            "valid_count": 8,
            "damaged_count": 1,
            "rejected_count": 1,
            "non_conforming_count": 0,
            "transport_condition": "Cold",
            "notes": "Sample notes",
        }],
        user_id=1,
        user=ADMIN_USER,
    )


class TestNextReceiptNo:
    def test_generates_receipt_no(self, fresh_db, seed_data):
        from lab_system.app.services.receipt_service import next_receipt_no
        import lab_system.app.database.db as _db
        with _db.get_conn() as conn:
            _seed_base(conn)
            no = next_receipt_no(conn)
        year = datetime.now().year
        assert no.startswith(f"LAB-{year}-")
        assert len(no) == f"LAB-{year}-000000".__len__()

    def test_increments(self, fresh_db, seed_data):
        from lab_system.app.services.receipt_service import next_receipt_no
        import lab_system.app.database.db as _db
        with _db.get_conn() as conn:
            _seed_base(conn)
            no1 = next_receipt_no(conn)
            no2 = next_receipt_no(conn)
        assert no1 != no2


class TestCreateReceipt:
    def test_creates_receipt(self, fresh_db, seed_data):
        rid, no = _create_receipt(fresh_db, seed_data)
        assert rid > 0
        assert no.startswith("LAB-")

    def test_invalid_totals_raises(self, fresh_db, seed_data):
        import lab_system.app.database.db as _db
        with _db.get_conn() as conn:
            _seed_base(conn)
            tx_id, org_a, _, st_id = _get_ids(conn)

        from lab_system.app.services.receipt_service import create_receipt
        with pytest.raises(ValueError, match="Invalid item totals"):
            create_receipt(
                data={
                    "tx_type_id": tx_id, "sender_org_id": org_a, "receiver_org_id": org_a,
                    "sender_name": "A", "receiver_name": "B", "sender_job_title": "",
                    "receiver_job_title": "", "auth_doc_no": "", "auth_date": "",
                    "notes": "", "transport_info": "", "additional_comments": "", "status": "Draft",
                },
                items=[{"sample_type_id": st_id, "name": "X", "total_count": 5,
                         "valid_count": 3, "damaged_count": 0, "rejected_count": 0,
                         "non_conforming_count": 0, "transport_condition": "", "notes": ""}],
                user_id=1, user=ADMIN_USER,
            )


class TestGetReceipt:
    def test_get_existing(self, fresh_db, seed_data):
        rid, _ = _create_receipt(fresh_db, seed_data)
        from lab_system.app.services.receipt_service import get_receipt
        r, items, atts = get_receipt(rid)
        assert r is not None
        assert r["sender_name"] == "Ahmed"
        assert len(items) == 1
        assert isinstance(atts, list)

    def test_get_nonexistent(self, fresh_db, seed_data):
        from lab_system.app.services.receipt_service import get_receipt
        r, items, atts = get_receipt(99999)
        assert r is None


class TestUpdateReceipt:
    def test_updates_receipt(self, fresh_db, seed_data):
        rid, _ = _create_receipt(fresh_db, seed_data)
        import lab_system.app.database.db as _db
        with _db.get_conn() as conn:
            tx_id, org_a, org_b, st_id = _get_ids(conn)

        from lab_system.app.services.receipt_service import update_receipt
        update_receipt(
            rid,
            data={
                "tx_type_id": tx_id, "sender_org_id": org_b, "receiver_org_id": org_a,
                "sender_name": "Updated", "receiver_name": "Receiver", "sender_job_title": "",
                "receiver_job_title": "", "auth_doc_no": "", "auth_date": "",
                "notes": "Updated", "transport_info": "", "additional_comments": "", "status": "Draft",
            },
            items=[{"sample_type_id": st_id, "name": "Updated Item", "total_count": 5,
                     "valid_count": 5, "damaged_count": 0, "rejected_count": 0,
                     "non_conforming_count": 0, "transport_condition": "", "notes": ""}],
            user=ADMIN_USER,
        )
        from lab_system.app.services.receipt_service import get_receipt
        r, items, _ = get_receipt(rid)
        assert r["sender_name"] == "Updated"
        assert items[0]["total_count"] == 5


class TestDeleteRestore:
    def test_soft_delete(self, fresh_db, seed_data):
        rid, _ = _create_receipt(fresh_db, seed_data)
        from lab_system.app.services.receipt_service import soft_delete_receipt, list_receipts
        soft_delete_receipt(rid, user_id=1, user=ADMIN_USER)
        rows, total = list_receipts(include_deleted=False)
        assert total == 0
        rows_all, total_all = list_receipts(include_deleted=True)
        assert total_all >= 1

    def test_hard_delete(self, fresh_db, seed_data):
        rid, _ = _create_receipt(fresh_db, seed_data)
        from lab_system.app.services.receipt_service import hard_delete_receipt, get_receipt
        hard_delete_receipt(rid, user_id=1, user=ADMIN_USER)
        r, _, _ = get_receipt(rid)
        assert r is None

    def test_restore(self, fresh_db, seed_data):
        rid, _ = _create_receipt(fresh_db, seed_data)
        from lab_system.app.services.receipt_service import soft_delete_receipt, restore_receipt, list_receipts
        soft_delete_receipt(rid, user_id=1, user=ADMIN_USER)
        restore_receipt(rid, user_id=1, user=ADMIN_USER)
        rows, total = list_receipts()
        assert total >= 1


class TestStatusTransitions:
    def test_valid_transition(self, fresh_db, seed_data):
        rid, _ = _create_receipt(fresh_db, seed_data)
        from lab_system.app.services.receipt_service import approve_receipt, archive_receipt
        approve_receipt(rid, user_id=1, user=ADMIN_USER)
        archive_receipt(rid, user_id=1, user=ADMIN_USER)

    def test_invalid_transition_raises(self, fresh_db, seed_data):
        rid, _ = _create_receipt(fresh_db, seed_data)
        from lab_system.app.services.receipt_service import approve_receipt, change_receipt_status
        approve_receipt(rid, user_id=1, user=ADMIN_USER)
        with pytest.raises(ValueError):
            change_receipt_status(rid, "Draft", user_id=1, user=ADMIN_USER)

    def test_validate_status_transition(self):
        from lab_system.app.services.receipt_service import validate_status_transition
        validate_status_transition("Draft", "Approved")
        with pytest.raises(ValueError):
            validate_status_transition("Draft", "Archived")

    def test_same_status_noop(self, fresh_db, seed_data):
        rid, _ = _create_receipt(fresh_db, seed_data)
        from lab_system.app.services.receipt_service import change_receipt_status
        change_receipt_status(rid, "Draft", user_id=1, user=ADMIN_USER)

    def test_nonexistent_receipt_raises(self, fresh_db, seed_data):
        from lab_system.app.services.receipt_service import change_receipt_status
        with pytest.raises(ValueError, match="not found"):
            change_receipt_status(99999, "Approved", user_id=1, user=ADMIN_USER)


class TestBatchOperations:
    def test_batch_status_update(self, fresh_db, seed_data):
        rid1, _ = _create_receipt(fresh_db, seed_data)
        rid2, _ = _create_receipt(fresh_db, seed_data)
        from lab_system.app.services.receipt_service import batch_update_status
        results = batch_update_status([rid1, rid2], "Approved", user_id=1, user=ADMIN_USER)
        assert all(r[1] == "ok" for r in results)

    def test_batch_soft_delete(self, fresh_db, seed_data):
        rid1, _ = _create_receipt(fresh_db, seed_data)
        rid2, _ = _create_receipt(fresh_db, seed_data)
        from lab_system.app.services.receipt_service import batch_soft_delete
        results = batch_soft_delete([rid1, rid2], user_id=1, user=ADMIN_USER)
        assert all(r[1] == "ok" for r in results)


class TestReceiptHistory:
    def test_history_recorded(self, fresh_db, seed_data):
        rid, _ = _create_receipt(fresh_db, seed_data)
        from lab_system.app.services.receipt_service import approve_receipt, get_receipt_history
        approve_receipt(rid, user_id=1, user=ADMIN_USER)
        history = get_receipt_history(rid)
        assert len(history) >= 1
        assert history[0]["field_name"] == "status"
        assert history[0]["old_value"] == "Draft"
        assert history[0]["new_value"] == "Approved"


class TestListReceipts:
    def test_list_empty(self, fresh_db, seed_data):
        from lab_system.app.services.receipt_service import list_receipts
        rows, total = list_receipts()
        assert total == 0
        assert len(rows) == 0

    def test_list_with_data(self, fresh_db, seed_data):
        _create_receipt(fresh_db, seed_data)
        from lab_system.app.services.receipt_service import list_receipts
        rows, total = list_receipts()
        assert total == 1
        assert rows[0]["sender_name"] == "Ahmed"

    def test_list_filter_status(self, fresh_db, seed_data):
        _create_receipt(fresh_db, seed_data, status="Draft")
        from lab_system.app.services.receipt_service import list_receipts
        rows, total = list_receipts(status="Draft")
        assert total == 1
        rows, total = list_receipts(status="Approved")
        assert total == 0

    def test_list_search(self, fresh_db, seed_data):
        _create_receipt(fresh_db, seed_data)
        from lab_system.app.services.receipt_service import list_receipts
        rows, total = list_receipts(q="Ahmed")
        assert total == 1

    def test_list_pagination(self, fresh_db, seed_data):
        _create_receipt(fresh_db, seed_data)
        _create_receipt(fresh_db, seed_data)
        from lab_system.app.services.receipt_service import list_receipts
        rows, total = list_receipts(page=1, page_size=1)
        assert total == 2
        assert len(rows) == 1

    def test_search_receipts(self, fresh_db, seed_data):
        _create_receipt(fresh_db, seed_data)
        from lab_system.app.services.receipt_service import search_receipts
        rows = search_receipts(q="Ahmed")
        assert len(rows) == 1
