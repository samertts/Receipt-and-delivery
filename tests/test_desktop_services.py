"""
Comprehensive tests for desktop app services.

Uses a temporary SQLite file for isolated testing (fixes :memory: isolation issue).
"""

import sys
import os
import sqlite3
import tempfile
import shutil
from pathlib import Path
from contextlib import contextmanager

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

TEST_DIR = Path(tempfile.mkdtemp(prefix="lab_test_"))
TEST_DB = TEST_DIR / "test.db"


def _init_test_db():
    """Create a temporary SQLite database with full schema and seed data."""
    from lab_system.app.database.db import SCHEMA
    conn = sqlite3.connect(str(TEST_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA)
    conn.execute("INSERT INTO organizations(name,code,org_type,status) VALUES('Org A','OA-001','Lab','Active')")
    conn.execute("INSERT INTO organizations(name,code,org_type,status) VALUES('Org B','OB-001','Lab','Active')")
    conn.execute("INSERT INTO users(full_name,username,password_hash,role,status) VALUES('Admin','admin','hash','Admin','Active')")
    conn.execute("INSERT INTO transaction_types(name,is_active) VALUES('Sample Receipt',1)")
    conn.execute("INSERT INTO sample_types(name,category,status) VALUES('Serum','Blood','Active')")
    conn.execute("INSERT INTO sample_types(name,category,status) VALUES('Urine','General','Active')")
    conn.commit()
    conn.close()
    return TEST_DB


def _make_test_get_conn():
    """Returns a get_conn replacement that uses the persistent test DB file."""
    @contextmanager
    def test_get_conn():
        conn = sqlite3.connect(str(TEST_DB))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    return test_get_conn


def setup_module():
    _init_test_db()
    import lab_system.app.database.db as db_mod
    import lab_system.app.settings.config as cfg_mod
    db_mod.get_conn = _make_test_get_conn()
    cfg_mod.DB_PATH = TEST_DB


def teardown_module():
    shutil.rmtree(TEST_DIR, ignore_errors=True)


class TestReceiptServiceFull:
    @staticmethod
    def _data(overrides=None):
        d = {"tx_type_id": 1, "sender_org_id": 1, "receiver_org_id": 2,
             "sender_name": "Ali", "receiver_name": "Sara",
             "sender_job_title": "Tech", "receiver_job_title": "Sup",
             "auth_doc_no": "A-001", "auth_date": "2026-05-27",
             "notes": "", "transport_info": "Cold", "additional_comments": "",
             "status": "Draft"}
        if overrides:
            d.update(overrides)
        return d



    @staticmethod
    def _item(overrides=None):
        i = {"sample_type_id": 1, "total_count": 100, "valid_count": 95,
             "damaged_count": 3, "rejected_count": 1, "non_conforming_count": 1,
             "transport_condition": "Good", "notes": ""}
        if overrides:
            i.update(overrides)
        return i

    def test_1_create_receipt(self):
        from lab_system.app.services.receipt_service import create_receipt
        rid, rno = create_receipt(self._data(), [self._item()], 1)
        assert rid > 0
        assert rno.startswith("LAB-2026-")

    def test_2_get_receipt(self):
        from lab_system.app.services.receipt_service import create_receipt, get_receipt
        rid, _ = create_receipt(self._data(), [self._item(), self._item({"sample_type_id": 2})], 1)
        r, items, atts = get_receipt(rid)
        assert r is not None
        assert r["sender_name"] == "Ali"
        assert len(items) == 2

    def test_3_update_receipt(self):
        from lab_system.app.services.receipt_service import create_receipt, get_receipt, update_receipt
        rid, _ = create_receipt(self._data(), [self._item()], 1)
        d = self._data({"status": "Approved", "additional_comments": "OK"})
        items = [self._item({"valid_count": 96, "damaged_count": 2})]
        update_receipt(rid, d, items)
        r, ri, _ = get_receipt(rid)
        assert r["status"] == "Approved"
        assert ri[0]["valid_count"] == 96

    def test_4_status_transitions(self):
        from lab_system.app.services.receipt_service import create_receipt, get_receipt, set_receipt_status
        rid, _ = create_receipt(self._data(), [self._item()], 1)
        for st in ["Approved", "Rejected", "Archived"]:
            set_receipt_status(rid, st)
            assert get_receipt(rid)[0]["status"] == st

    def test_5_list_receipts(self):
        from lab_system.app.services.receipt_service import create_receipt, list_receipts, set_receipt_status
        r1, _ = create_receipt(self._data(), [self._item()], 1)
        r2, _ = create_receipt(self._data(), [self._item()], 1)
        set_receipt_status(r2, "Approved")
        _, total = list_receipts()
        assert total >= 2
        _, total = list_receipts(status="Draft")
        assert total >= 1
        _, total = list_receipts(status="Approved")
        assert total >= 1

    def test_6_search_receipts(self):
        from lab_system.app.services.receipt_service import create_receipt, search_receipts
        create_receipt(self._data(), [self._item()], 1)
        r = search_receipts(q="Org A")
        assert len(r) >= 1
        r = search_receipts(q="ZZZZNONEXISTENT")
        assert len(r) == 0

    def test_7_delete_receipt(self):
        from lab_system.app.services.receipt_service import create_receipt, get_receipt, hard_delete_receipt
        rid, _ = create_receipt(self._data(), [self._item()], 1)
        hard_delete_receipt(rid)
        assert get_receipt(rid)[0] is None

    def test_8_validation(self):
        from lab_system.app.services.receipt_service import create_receipt
        import pytest
        bad = [{"sample_type_id": 1, "total_count": 100, "valid_count": 50,
                "damaged_count": 10, "rejected_count": 5, "non_conforming_count": 5,
                "transport_condition": "", "notes": ""}]
        with pytest.raises(ValueError):
            create_receipt(self._data(), bad, 1)


class TestOrganizationService:
    def test_list_and_upsert(self):
        from lab_system.app.services.org_service import list_organizations, upsert_organization
        orgs = list_organizations()
        assert len(orgs) >= 2
        upsert_organization({"name": "Org C", "code": "OC-001", "org_type": "Lab",
                             "governorate": "Baghdad", "address": "", "phone": "",
                             "email": "", "logo_path": "", "notes": "", "status": "Active"})
        orgs = list_organizations()
        names = [o["name"] for o in orgs]
        assert "Org C" in names

    def test_active_only(self):
        from lab_system.app.services.org_service import list_organizations
        active = list_organizations(active_only=True)
        for o in active:
            assert o["status"] == "Active"


class TestReportService:
    def test_receipt_summary(self):
        from lab_system.app.services.report_service import receipt_summary
        summary = receipt_summary()
        assert "total" in summary
        assert "by_status" in summary
        assert "by_type" in summary

    def test_sample_summary(self):
        from lab_system.app.services.report_service import sample_summary
        samples = sample_summary()
        assert isinstance(samples, list)

    def test_export_csv(self):
        from lab_system.app.services.report_service import export_receipts_csv
        path = TEST_DIR / "test_export.csv"
        result = export_receipts_csv(str(path))
        assert Path(result).exists()
        assert Path(result).stat().st_size > 0


class TestBackupService:
    def test_create_backup(self):
        from lab_system.app.services.backup_service import create_backup
        path = create_backup(user_id=1, notes="Test backup")
        assert Path(path).exists()
        assert Path(path).stat().st_size > 0


class TestSettings:
    def test_defaults_exist(self):
        from lab_system.app.database.db import DEFAULT_SETTINGS
        assert "receipt.numbering_prefix" in DEFAULT_SETTINGS
        assert "printer.mode" in DEFAULT_SETTINGS
        assert "backup.auto_enabled" in DEFAULT_SETTINGS


class TestCatalogService:
    def test_catalog_functions(self):
        from lab_system.app.services.catalog_service import list_transaction_types, list_sample_types
        tx = list_transaction_types()
        assert len(tx) >= 1
        sm = list_sample_types()
        assert len(sm) >= 2


class TestUserService:
    def test_list_users(self):
        from lab_system.app.services.user_service import list_users, create_user
        users = list_users()
        assert len(users) >= 1
        create_user("New User", "newuser", "Pass@123", "User", institution_id=1)
        users = list_users()
        usernames = [u["username"] for u in users]
        assert "newuser" in usernames


class TestConstants:
    def test_constants(self):
        from lab_system.app.utils.constants import APP_NAME, ROLES, THEME, DEFAULT_WINDOW_SIZE
        assert APP_NAME == "نظام إدارة الاستلام المختبري"
        assert "Admin" in ROLES
        assert "User" in ROLES
        assert "Auditor" in ROLES
        assert "primary" in THEME
        assert len(DEFAULT_WINDOW_SIZE) == 2
