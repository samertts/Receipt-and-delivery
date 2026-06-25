"""Report service tests."""

import csv
import os
import sys
from datetime import datetime


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


ADMIN_USER = {"id": 1, "username": "admin", "role": "Admin", "status": "Active"}


def _seed_reports_db(conn):
    """Insert base data for report tests."""
    from lab_system.app.auth.security import hash_password
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("INSERT OR IGNORE INTO users(username,password_hash,full_name,role,status,password_changed_at) VALUES(?,?,?,?,?,?)",
                 ("admin", hash_password("Admin@123"), "Admin User", "Admin", "Active", ""))
    conn.execute("INSERT OR IGNORE INTO transaction_types(name) VALUES(?)", ("Receipt",))
    conn.execute("INSERT OR IGNORE INTO sample_types(name,category,status) VALUES(?,?,?)", ("Blood", "Biological", "Active"))
    conn.execute("INSERT OR IGNORE INTO sample_types(name,category,status) VALUES(?,?,?)", ("Urine", "Biological", "Active"))
    conn.execute("INSERT OR IGNORE INTO organizations(name,code,org_type,governorate,status) VALUES(?,?,?,?,?)",
                 ("Lab A", "LA", "Laboratory", "Baghdad", "Active"))
    conn.execute("INSERT OR IGNORE INTO organizations(name,code,org_type,governorate,status) VALUES(?,?,?,?,?)",
                 ("Lab B", "LB", "Laboratory", "Erbil", "Active"))
    conn.commit()


def _seed_receipts(conn, count=3, status="Approved"):
    """Insert test receipts."""
    tx_id = conn.execute("SELECT id FROM transaction_types WHERE name='Receipt'").fetchone()[0]
    org_a = conn.execute("SELECT id FROM organizations WHERE code='LA'").fetchone()[0]
    org_b = conn.execute("SELECT id FROM organizations WHERE code='LB'").fetchone()[0]
    st_id = conn.execute("SELECT id FROM sample_types WHERE name='Blood'").fetchone()[0]
    now = datetime.now().isoformat(timespec="seconds")

    for i in range(count):
        cur = conn.execute(
            """INSERT INTO receipts(receipt_no,tx_type_id,sender_org_id,receiver_org_id,
                sender_name,receiver_name,sender_job_title,receiver_job_title,
                auth_doc_no,auth_date,created_at,notes,transport_info,
                additional_comments,status,created_by)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (f"RPT-{i:06d}", tx_id, org_a, org_b, f"Sender{i}", f"Receiver{i}",
             "", "", "", "", now, f"Note {i}", "", "", status, 1),
        )
        rid = cur.lastrowid
        conn.execute(
            """INSERT INTO receipt_items(receipt_id,sample_type_id,
                total_count,valid_count,damaged_count,rejected_count,
                non_conforming_count,transport_condition,notes)
                VALUES(?,?,?,?,?,?,?,?,?)""",
            (rid, st_id, 10, 8, 1, 1, 0, "Cold", "Item notes"),
        )
    conn.commit()


class TestReceiptSummary:
    def test_empty_db(self, fresh_db, seed_data):
        from lab_system.app.services.report_service import receipt_summary
        result = receipt_summary()
        assert result["total"] == 0
        assert result["by_status"] == {}
        assert result["by_type"] == {}

    def test_with_data(self, fresh_db, seed_data):
        import lab_system.app.database.db as _db
        with _db.get_conn() as conn:
            _seed_reports_db(conn)
            _seed_receipts(conn, count=3)

        from lab_system.app.services.report_service import receipt_summary
        result = receipt_summary()
        assert result["total"] == 3
        assert "Approved" in result["by_status"]
        assert result["by_status"]["Approved"] == 3


class TestDailyReport:
    def test_empty_db(self, fresh_db, seed_data):
        from lab_system.app.services.report_service import daily_report
        result = daily_report()
        assert isinstance(result, list)
        assert len(result) == 0

    def test_with_data(self, fresh_db, seed_data):
        import lab_system.app.database.db as _db
        with _db.get_conn() as conn:
            _seed_reports_db(conn)
            _seed_receipts(conn, count=2)

        from lab_system.app.services.report_service import daily_report
        result = daily_report()
        assert len(result) >= 1
        assert "day" in result[0]
        assert "total" in result[0]


class TestMonthlyReport:
    def test_empty_db(self, fresh_db, seed_data):
        from lab_system.app.services.report_service import monthly_report
        result = monthly_report()
        assert isinstance(result, list)

    def test_with_year_filter(self, fresh_db, seed_data):
        import lab_system.app.database.db as _db
        with _db.get_conn() as conn:
            _seed_reports_db(conn)
            _seed_receipts(conn, count=2)

        from lab_system.app.services.report_service import monthly_report
        result = monthly_report(year=datetime.now().year)
        assert len(result) >= 1


class TestInstitutionStatistics:
    def test_empty_db(self, fresh_db, seed_data):
        from lab_system.app.services.report_service import institution_statistics
        result = institution_statistics()
        assert "by_sender" in result
        assert "by_receiver" in result
        assert len(result["by_sender"]) == 0

    def test_with_data(self, fresh_db, seed_data):
        import lab_system.app.database.db as _db
        with _db.get_conn() as conn:
            _seed_reports_db(conn)
            _seed_receipts(conn, count=3)

        from lab_system.app.services.report_service import institution_statistics
        result = institution_statistics()
        assert len(result["by_sender"]) >= 1
        assert "org_name" in result["by_sender"][0]


class TestRejectionStatistics:
    def test_empty_db(self, fresh_db, seed_data):
        from lab_system.app.services.report_service import rejection_statistics
        result = rejection_statistics()
        assert isinstance(result, list)
        assert len(result) == 0

    def test_with_data(self, fresh_db, seed_data):
        import lab_system.app.database.db as _db
        with _db.get_conn() as conn:
            _seed_reports_db(conn)
            _seed_receipts(conn, count=3)

        from lab_system.app.services.report_service import rejection_statistics
        result = rejection_statistics()
        assert len(result) >= 1
        assert "sample_name" in result[0]


class TestDamageStatistics:
    def test_empty_db(self, fresh_db, seed_data):
        from lab_system.app.services.report_service import damage_statistics
        result = damage_statistics()
        assert isinstance(result, list)
        assert len(result) == 0

    def test_with_data(self, fresh_db, seed_data):
        import lab_system.app.database.db as _db
        with _db.get_conn() as conn:
            _seed_reports_db(conn)
            _seed_receipts(conn, count=3)

        from lab_system.app.services.report_service import damage_statistics
        result = damage_statistics()
        assert len(result) >= 1


class TestSampleSummary:
    def test_empty_db(self, fresh_db, seed_data):
        from lab_system.app.services.report_service import sample_summary
        result = sample_summary()
        assert isinstance(result, list)
        assert len(result) == 0

    def test_with_data(self, fresh_db, seed_data):
        import lab_system.app.database.db as _db
        with _db.get_conn() as conn:
            _seed_reports_db(conn)
            _seed_receipts(conn, count=3)

        from lab_system.app.services.report_service import sample_summary
        result = sample_summary()
        assert len(result) >= 1
        assert "sample_name" in result[0]


class TestExportCsv:
    def test_export_csv(self, fresh_db, seed_data, tmp_path):
        import lab_system.app.database.db as _db
        with _db.get_conn() as conn:
            _seed_reports_db(conn)
            _seed_receipts(conn, count=2)

        from lab_system.app.services.report_service import export_receipts_csv
        csv_path = tmp_path / "export.csv"
        result = export_receipts_csv(str(csv_path))
        assert result.exists()
        with open(result, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) >= 3
            assert rows[0][0] == "رقم الإيصال"
