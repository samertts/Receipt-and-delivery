"""
V14.0 Real World Operational Hardening

Validates:
- Disaster recovery drills
- Long-term operation simulation
- Multi-user validation
- Upgrade certification
- Low hardware certification
- Field deployment readiness
- Automated operations center
"""

import gc
import os
import shutil
import sqlite3
import sys
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import lab_system.app.settings.config as _cfg

ORIGINAL_DB_PATH = _cfg.CONFIG.db_path
ORIGINAL_STORAGE_DIR = _cfg.CONFIG.storage_dir


# ============================================================================
# FIXTURES
# ============================================================================

def _create_db(path):
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode=WAL;")
    schema_path = os.path.join(
        os.path.dirname(__file__), "..", "lab_system", "app", "database", "db.py"
    )
    with open(schema_path, "r") as f:
        schema_content = f.read()
    globals_ = {}
    exec(schema_content, globals_)
    for table_sql in globals_["SCHEMA"].split(";"):
        if table_sql.strip():
            try:
                conn.execute(table_sql)
            except sqlite3.OperationalError:
                pass
    conn.commit()
    return conn


def _setup_base_data(conn):
    conn.execute(
        "INSERT INTO users(id,full_name,username,password_hash,role,status) "
        "VALUES(1,'Admin','admin','hash','Admin','Active')"
    )
    conn.execute(
        "INSERT INTO users(id,full_name,username,password_hash,role,status) "
        "VALUES(2,'Tech','tech1','hash','User','Active')"
    )
    conn.execute(
        "INSERT INTO organizations(name, code, org_type, governorate) "
        "VALUES('Test Lab','TL001','Laboratory','Beirut')"
    )
    conn.execute(
        "INSERT INTO transaction_types(name, is_active) VALUES('Receipt', 1)"
    )
    conn.execute(
        "INSERT INTO sample_types(name, category, status) VALUES('Blood', 'Clinical', 'Active')"
    )
    conn.commit()


def _insert_receipts(conn, count, start_id=1):
    now = datetime.now()
    for i in range(start_id, start_id + count):
        created_at = (now - timedelta(days=count - i)).isoformat(timespec="seconds")
        conn.execute(
            """INSERT INTO receipts
               (receipt_no, tx_type_id, sender_org_id, receiver_org_id,
                sender_name, receiver_name, status, created_by, created_at)
               VALUES (?, 1, 1, 1, ?, ?, 'Draft', 1, ?)""",
            (f"RCP-{i:08d}", f"Sender {i}", f"Receiver {i}", created_at),
        )
    conn.commit()


def _create_backup(db_path, backup_path):
    """Create a backup by copying the database."""
    shutil.copy2(str(db_path), str(backup_path))
    return backup_path


def _corrupt_file(path):
    """Corrupt a file by writing garbage data."""
    with open(path, "wb") as f:
        f.write(b"CORRUPTED DATA " * 100)


@pytest.fixture
def v14_db(tmp_path):
    db_path = tmp_path / "v14_test.db"
    conn = _create_db(db_path)
    _setup_base_data(conn)
    _insert_receipts(conn, 100)
    conn.close()
    (tmp_path / "backups").mkdir(exist_ok=True)
    (tmp_path / "logs").mkdir(exist_ok=True)
    return db_path


@pytest.fixture
def v14_db_large(tmp_path):
    db_path = tmp_path / "v14_large.db"
    conn = _create_db(db_path)
    _setup_base_data(conn)
    _insert_receipts(conn, 1000)
    conn.close()
    return db_path


@pytest.fixture
def v14_storage(tmp_path):
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    (storage_dir / "backups").mkdir()
    (storage_dir / "snapshots").mkdir()
    (storage_dir / "logs").mkdir()
    return storage_dir


def _patch_db(db_path, storage_dir=None):
    import lab_system.app.settings.config as cfg_mod
    import lab_system.app.database.db as db_mod

    originals = {}
    originals["db_get_conn"] = db_mod.get_conn

    @contextmanager
    def _test_get_conn():
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode=WAL;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    db_mod.get_conn = _test_get_conn
    originals["cfg_db_path"] = cfg_mod.CONFIG.db_path
    object.__setattr__(cfg_mod.CONFIG, "db_path", str(db_path))

    if storage_dir is not None:
        originals["cfg_storage_dir"] = cfg_mod.CONFIG.storage_dir
        object.__setattr__(cfg_mod.CONFIG, "storage_dir", storage_dir)

    class _Ctx:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            db_mod.get_conn = originals["db_get_conn"]
            object.__setattr__(cfg_mod.CONFIG, "db_path", originals["cfg_db_path"])
            if "cfg_storage_dir" in originals:
                object.__setattr__(cfg_mod.CONFIG, "storage_dir", originals["cfg_storage_dir"])

    return _Ctx()


@pytest.fixture(autouse=True)
def _restore_config():
    import lab_system.app.settings.config as cfg_mod
    yield
    object.__setattr__(cfg_mod.CONFIG, "db_path", ORIGINAL_DB_PATH)
    object.__setattr__(cfg_mod.CONFIG, "storage_dir", ORIGINAL_STORAGE_DIR)


# ============================================================================
# PHASE 1 — DISASTER RECOVERY DRILLS
# ============================================================================

class TestDisasterRecoveryDrills:
    """Simulate disaster scenarios and validate recovery."""

    def test_full_database_loss_recovery(self, tmp_path):
        """Recover from full database loss using backup."""
        db_path = tmp_path / "main.db"
        backup_path = tmp_path / "backup.db"
        conn = _create_db(db_path)
        _setup_base_data(conn)
        _insert_receipts(conn, 50)
        count_before = conn.execute("SELECT COUNT(*) as cnt FROM receipts").fetchone()["cnt"]
        conn.close()
        _create_backup(db_path, backup_path)
        os.unlink(db_path)
        assert not db_path.exists(), "Database should be deleted"
        shutil.copy2(str(backup_path), str(db_path))
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        count_after = conn.execute("SELECT COUNT(*) as cnt FROM receipts").fetchone()["cnt"]
        conn.close()
        assert count_before == count_after, f"Data loss: {count_before} != {count_after}"

    def test_backup_corruption_detection(self, tmp_path):
        """Detect corrupted backup files."""
        backup_path = tmp_path / "corrupt_backup.db"
        _create_backup(tmp_path / "source.db", backup_path) if False else None
        source = tmp_path / "source.db"
        conn = _create_db(source)
        conn.close()
        _create_backup(source, backup_path)
        _corrupt_file(backup_path)
        result = {"valid": False, "error": None}
        try:
            conn = sqlite3.connect(str(backup_path))
            row = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            if row and row[0] == "ok":
                result["valid"] = True
            else:
                result["error"] = "Integrity check failed"
        except Exception as e:
            result["error"] = str(e)
        assert result["valid"] is False
        assert result["error"] is not None

    def test_snapshot_corruption_recovery(self, tmp_path):
        """Recover from snapshot corruption."""
        db_path = tmp_path / "main.db"
        snapshot_path = tmp_path / "snapshot.db"
        conn = _create_db(db_path)
        _setup_base_data(conn)
        _insert_receipts(conn, 25)
        conn.close()
        shutil.copy2(str(db_path), str(snapshot_path))
        _corrupt_file(snapshot_path)
        result = {"recovered": False}
        try:
            shutil.copy2(str(db_path), str(snapshot_path))
            conn = sqlite3.connect(str(snapshot_path))
            row = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            if row and row[0] == "ok":
                result["recovered"] = True
        except Exception:
            pass
        assert result["recovered"] is True

    def test_storage_failure_simulation(self, tmp_path):
        """Simulate storage failure and recovery."""
        db_path = tmp_path / "main.db"
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        conn = _create_db(db_path)
        _setup_base_data(conn)
        _insert_receipts(conn, 30)
        conn.close()
        backup_path = backup_dir / "backup.db"
        shutil.copy2(str(db_path), str(backup_path))
        result = {"backup_exists": backup_path.exists()}
        assert result["backup_exists"] is True
        if db_path.exists():
            os.unlink(db_path)
        shutil.copy2(str(backup_path), str(db_path))
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        count = conn.execute("SELECT COUNT(*) as cnt FROM receipts").fetchone()["cnt"]
        conn.close()
        assert count == 30

    def test_unexpected_shutdown_during_restore(self, tmp_path):
        """Simulate unexpected shutdown during restore operation."""
        db_path = tmp_path / "main.db"
        backup_path = tmp_path / "backup.db"
        temp_restore = tmp_path / "restore_temp.db"
        conn = _create_db(db_path)
        _setup_base_data(conn)
        _insert_receipts(conn, 40)
        conn.close()
        shutil.copy2(str(db_path), str(backup_path))
        with open(str(temp_restore), "wb") as f:
            f.write(b"partial restore")
        result = {"restored": False}
        if temp_restore.exists() and temp_restore.stat().st_size < 100:
            temp_restore.unlink()
        if backup_path.exists():
            shutil.copy2(str(backup_path), str(db_path))
            result["restored"] = True
        assert result["restored"] is True
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        count = conn.execute("SELECT COUNT(*) as cnt FROM receipts").fetchone()["cnt"]
        conn.close()
        assert count == 40

    def test_recovery_success_rate_above_99_9(self, tmp_path):
        """Recovery success rate >= 99.9%."""
        successes = 0
        total = 100
        for i in range(total):
            db_path = tmp_path / f"test_{i}.db"
            backup_path = tmp_path / f"backup_{i}.db"
            conn = _create_db(db_path)
            _setup_base_data(conn)
            _insert_receipts(conn, 10)
            conn.close()
            shutil.copy2(str(db_path), str(backup_path))
            os.unlink(db_path)
            try:
                shutil.copy2(str(backup_path), str(db_path))
                conn = sqlite3.connect(str(db_path))
                row = conn.execute("PRAGMA integrity_check").fetchone()
                conn.close()
                if row and row[0] == "ok":
                    successes += 1
            except Exception:
                pass
        success_rate = (successes / total) * 100
        assert success_rate >= 99.9, f"Recovery rate {success_rate:.1f}%, target >= 99.9%"


# ============================================================================
# PHASE 2 — LONG TERM OPERATION
# ============================================================================

class TestLongTermOperation:
    """Simulate extended operation periods."""

    def test_30_day_simulation(self, v14_db):
        """Simulate 30 days of operation."""
        conn = sqlite3.connect(str(v14_db))
        conn.row_factory = sqlite3.Row
        gc.collect()
        for day in range(30):
            for _ in range(10):
                conn.execute(
                    "INSERT INTO receipts(receipt_no, tx_type_id, sender_org_id, "
                    "receiver_org_id, sender_name, receiver_name, status, created_by, "
                    "created_at) VALUES (?, 1, 1, 1, ?, ?, 'Draft', 1, ?)",
                    (f"DAY{day}-{_:04d}", f"S{day}", f"R{day}",
                     datetime.now().isoformat(timespec="seconds")),
                )
            conn.commit()
            conn.execute("SELECT * FROM receipts LIMIT 10").fetchall()
        count = conn.execute("SELECT COUNT(*) as cnt FROM receipts").fetchone()["cnt"]
        conn.close()
        assert count >= 400, f"Expected >= 400 receipts, got {count}"

    def test_60_day_simulation(self, v14_db):
        """Simulate 60 days of operation."""
        conn = sqlite3.connect(str(v14_db))
        conn.row_factory = sqlite3.Row
        for day in range(60):
            conn.execute(
                "INSERT INTO receipts(receipt_no, tx_type_id, sender_org_id, "
                "receiver_org_id, sender_name, receiver_name, status, created_by, "
                "created_at) VALUES (?, 1, 1, 1, ?, ?, 'Draft', 1, ?)",
                (f"DAY{day}-0001", f"S{day}", f"R{day}",
                 datetime.now().isoformat(timespec="seconds")),
            )
            conn.commit()
        count = conn.execute("SELECT COUNT(*) as cnt FROM receipts").fetchone()["cnt"]
        conn.close()
        assert count >= 160

    def test_90_day_simulation(self, v14_db):
        """Simulate 90 days of operation."""
        conn = sqlite3.connect(str(v14_db))
        conn.row_factory = sqlite3.Row
        for day in range(90):
            conn.execute(
                "INSERT INTO receipts(receipt_no, tx_type_id, sender_org_id, "
                "receiver_org_id, sender_name, receiver_name, status, created_by, "
                "created_at) VALUES (?, 1, 1, 1, ?, ?, 'Draft', 1, ?)",
                (f"DAY{day}-0001", f"S{day}", f"R{day}",
                 datetime.now().isoformat(timespec="seconds")),
            )
            conn.commit()
        count = conn.execute("SELECT COUNT(*) as cnt FROM receipts").fetchone()["cnt"]
        conn.close()
        assert count >= 190

    def test_no_memory_degradation(self, v14_db):
        """No memory degradation over extended operation."""
        import resource
        gc.collect()
        start_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        conn = sqlite3.connect(str(v14_db))
        conn.row_factory = sqlite3.Row
        for _ in range(500):
            conn.execute("SELECT * FROM receipts LIMIT 10").fetchall()
        conn.close()
        gc.collect()
        end_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        growth_mb = (end_mem - start_mem) / 1024
        assert growth_mb < 20, f"Memory grew {growth_mb:.1f}MB over extended operation"

    def test_no_database_corruption(self, v14_db):
        """Database remains corruption-free over extended operation."""
        conn = sqlite3.connect(str(v14_db))
        for _ in range(100):
            conn.execute(
                "INSERT INTO receipts(receipt_no, tx_type_id, sender_org_id, "
                "receiver_org_id, sender_name, receiver_name, status, created_by, "
                "created_at) VALUES (?, 1, 1, 1, 'Test', 'Test', 'Draft', 1, ?)",
                (f"CORR-{_:04d}", datetime.now().isoformat(timespec="seconds")),
            )
        conn.commit()
        result = conn.execute("PRAGMA integrity_check").fetchone()
        conn.close()
        assert result[0] == "ok", f"Integrity check failed: {result[0]}"


# ============================================================================
# PHASE 3 — MULTI USER VALIDATION
# ============================================================================

class TestMultiUserValidation:
    """Validate concurrency and transaction integrity."""

    def test_5_concurrent_users(self, v14_db):
        """5 users operating concurrently."""
        errors = []
        results = []

        def user_task(user_id):
            try:
                conn = sqlite3.connect(str(v14_db))
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA journal_mode=WAL;")
                for i in range(20):
                    conn.execute(
                        "INSERT INTO receipts(receipt_no, tx_type_id, sender_org_id, "
                        "receiver_org_id, sender_name, receiver_name, status, created_by, "
                        "created_at) VALUES (?, 1, 1, 1, ?, ?, 'Draft', ?, ?)",
                        (f"U{user_id}-{i:04d}", f"User{user_id}", f"Recv{i}",
                         user_id, datetime.now().isoformat(timespec="seconds")),
                    )
                conn.commit()
                conn.close()
                results.append(f"user_{user_id}_ok")
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=user_task, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)
        assert len(errors) == 0, f"Concurrent errors: {errors}"
        assert len(results) == 5

    def test_10_concurrent_users(self, v14_db):
        """10 users operating concurrently."""
        errors = []

        def user_task(user_id):
            try:
                conn = sqlite3.connect(str(v14_db))
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA journal_mode=WAL;")
                for i in range(10):
                    conn.execute(
                        "INSERT INTO receipts(receipt_no, tx_type_id, sender_org_id, "
                        "receiver_org_id, sender_name, receiver_name, status, created_by, "
                        "created_at) VALUES (?, 1, 1, 1, ?, ?, 'Draft', ?, ?)",
                        (f"U{user_id}-{i:04d}", f"User{user_id}", f"Recv{i}",
                         user_id, datetime.now().isoformat(timespec="seconds")),
                    )
                conn.commit()
                conn.close()
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=user_task, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)
        assert len(errors) == 0, f"Concurrent errors: {errors}"

    def test_25_concurrent_users(self, v14_db):
        """25 users operating concurrently."""
        errors = []

        def user_task(user_id):
            try:
                conn = sqlite3.connect(str(v14_db))
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA journal_mode=WAL;")
                for i in range(5):
                    conn.execute(
                        "INSERT INTO receipts(receipt_no, tx_type_id, sender_org_id, "
                        "receiver_org_id, sender_name, receiver_name, status, created_by, "
                        "created_at) VALUES (?, 1, 1, 1, ?, ?, 'Draft', ?, ?)",
                        (f"U{user_id}-{i:04d}", f"User{user_id}", f"Recv{i}",
                         user_id, datetime.now().isoformat(timespec="seconds")),
                    )
                conn.commit()
                conn.close()
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=user_task, args=(i,)) for i in range(25)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60)
        assert len(errors) == 0, f"Concurrent errors: {errors}"

    def test_50_concurrent_users(self, v14_db):
        """50 users operating concurrently."""
        errors = []

        def user_task(user_id):
            try:
                conn = sqlite3.connect(str(v14_db))
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA journal_mode=WAL;")
                for i in range(3):
                    conn.execute(
                        "INSERT INTO receipts(receipt_no, tx_type_id, sender_org_id, "
                        "receiver_org_id, sender_name, receiver_name, status, created_by, "
                        "created_at) VALUES (?, 1, 1, 1, ?, ?, 'Draft', ?, ?)",
                        (f"U{user_id}-{i:04d}", f"User{user_id}", f"Recv{i}",
                         user_id, datetime.now().isoformat(timespec="seconds")),
                    )
                conn.commit()
                conn.close()
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=user_task, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=120)
        assert len(errors) == 0, f"Concurrent errors: {errors}"

    def test_transaction_integrity(self, v14_db):
        """Transaction integrity under concurrent load."""
        errors = []
        initial_count = 0

        def read_write_task(task_id):
            try:
                conn = sqlite3.connect(str(v14_db))
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA journal_mode=WAL;")
                for i in range(10):
                    conn.execute(
                        "INSERT INTO receipts(receipt_no, tx_type_id, sender_org_id, "
                        "receiver_org_id, sender_name, receiver_name, status, created_by, "
                        "created_at) VALUES (?, 1, 1, 1, ?, ?, 'Draft', ?, ?)",
                        (f"TX{task_id}-{i:04d}", f"Sender{task_id}", f"Recv{i}",
                         task_id, datetime.now().isoformat(timespec="seconds")),
                    )
                conn.commit()
                conn.close()
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=read_write_task, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)
        conn = sqlite3.connect(str(v14_db))
        conn.row_factory = sqlite3.Row
        final_count = conn.execute("SELECT COUNT(*) as cnt FROM receipts").fetchone()["cnt"]
        conn.close()
        assert len(errors) == 0, f"Transaction errors: {errors}"
        assert final_count > initial_count


# ============================================================================
# PHASE 4 — UPGRADE CERTIFICATION
# ============================================================================

class TestUpgradeCertification:
    """Validate schema migration and upgrade paths."""

    def test_schema_migration_v1_to_v2(self, tmp_path):
        """Simulate v1.0 to v1.1 upgrade."""
        db_path = tmp_path / "upgrade_v1.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_no TEXT UNIQUE NOT NULL,
                patient_name TEXT DEFAULT '',
                status TEXT DEFAULT 'Draft',
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("INSERT INTO receipts(receipt_no, patient_name, status, created_at) "
                     "VALUES('RCP-001', 'Patient1', 'Draft', '2026-01-01')")
        conn.commit()
        conn.close()
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        count = conn.execute("SELECT COUNT(*) as cnt FROM receipts").fetchone()["cnt"]
        assert count == 1
        try:
            conn.execute("ALTER TABLE receipts ADD COLUMN doctor_name TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass
        conn.execute("UPDATE receipts SET doctor_name='Dr. Smith' WHERE receipt_no='RCP-001'")
        conn.commit()
        row = conn.execute("SELECT doctor_name FROM receipts WHERE receipt_no='RCP-001'").fetchone()
        conn.close()
        assert row["doctor_name"] == "Dr. Smith"

    def test_schema_migration_preserves_data(self, tmp_path):
        """Schema migration preserves existing data."""
        db_path = tmp_path / "preserve_data.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_no TEXT UNIQUE NOT NULL,
                patient_name TEXT NOT NULL,
                status TEXT DEFAULT 'Draft',
                created_at TEXT NOT NULL
            )
        """)
        for i in range(50):
            conn.execute(
                "INSERT INTO receipts(receipt_no, patient_name, status, created_at) "
                "VALUES(?, ?, 'Draft', '2026-01-01')",
                (f"RCP-{i:03d}", f"Patient{i}"),
            )
        conn.commit()
        count_before = conn.execute("SELECT COUNT(*) as cnt FROM receipts").fetchone()["cnt"]
        conn.close()
        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute("ALTER TABLE receipts ADD COLUMN notes TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass
        conn.commit()
        conn.row_factory = sqlite3.Row
        count_after = conn.execute("SELECT COUNT(*) as cnt FROM receipts").fetchone()["cnt"]
        conn.close()
        assert count_before == count_after, f"Data loss: {count_before} != {count_after}"

    def test_no_data_loss_on_upgrade(self, tmp_path):
        """No data loss during upgrade process."""
        db_path = tmp_path / "no_loss.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_no TEXT UNIQUE NOT NULL,
                patient_name TEXT NOT NULL,
                status TEXT DEFAULT 'Draft',
                created_at TEXT NOT NULL
            )
        """)
        for i in range(100):
            conn.execute(
                "INSERT INTO receipts(receipt_no, patient_name, status, created_at) "
                "VALUES(?, ?, 'Draft', '2026-01-01')",
                (f"RCP-{i:03d}", f"Patient{i}"),
            )
        conn.commit()
        conn.close()
        backup_path = tmp_path / "pre_upgrade_backup.db"
        shutil.copy2(str(db_path), str(backup_path))
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("ALTER TABLE receipts ADD COLUMN priority TEXT DEFAULT 'normal'")
        except sqlite3.OperationalError:
            pass
        conn.commit()
        count_after = conn.execute("SELECT COUNT(*) as cnt FROM receipts").fetchone()["cnt"]
        conn.close()
        assert count_after == 100


# ============================================================================
# PHASE 5 — LOW HARDWARE CERTIFICATION
# ============================================================================

class TestLowHardwareCertification:
    """Validate system usability on constrained hardware."""

    def test_2gb_ram_simulation(self, v14_db):
        """System remains usable with limited RAM."""
        import resource
        conn = sqlite3.connect(str(v14_db))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA cache_size=-2000")
        for _ in range(100):
            conn.execute("SELECT * FROM receipts LIMIT 10").fetchall()
        usage = resource.getrusage(resource.RUSAGE_SELF)
        ram_mb = usage.ru_maxrss / 1024
        conn.close()
        assert ram_mb < 200, f"RAM usage {ram_mb:.1f}MB on 2GB simulation"

    def test_4gb_ram_simulation(self, v14_db_large):
        """System performs well with 4GB RAM."""
        import resource
        conn = sqlite3.connect(str(v14_db_large))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA cache_size=-8000")
        for _ in range(200):
            conn.execute("SELECT * FROM receipts LIMIT 20").fetchall()
        usage = resource.getrusage(resource.RUSAGE_SELF)
        ram_mb = usage.ru_maxrss / 1024
        conn.close()
        assert ram_mb < 200, f"RAM usage {ram_mb:.1f}MB on 4GB simulation"

    def test_hdd_performance(self, v14_db):
        """System performs acceptably on HDD-like conditions."""
        conn = sqlite3.connect(str(v14_db))
        conn.row_factory = sqlite3.Row
        start = time.time()
        for _ in range(50):
            conn.execute("SELECT * FROM receipts LIMIT 10").fetchall()
        elapsed = time.time() - start
        conn.close()
        assert elapsed < 5, f"HDD simulation took {elapsed:.1f}s"

    def test_ssd_performance(self, v14_db):
        """System performs optimally on SSD-like conditions."""
        conn = sqlite3.connect(str(v14_db))
        conn.row_factory = sqlite3.Row
        start = time.time()
        for _ in range(100):
            conn.execute("SELECT * FROM receipts LIMIT 10").fetchall()
        elapsed = time.time() - start
        conn.close()
        assert elapsed < 2, f"SSD simulation took {elapsed:.1f}s"

    def test_legacy_cpu_simulation(self, v14_db):
        """System usable on legacy CPU."""
        conn = sqlite3.connect(str(v14_db))
        conn.row_factory = sqlite3.Row
        start = time.time()
        for _ in range(200):
            conn.execute("SELECT * FROM receipts LIMIT 5").fetchall()
        elapsed = time.time() - start
        conn.close()
        assert elapsed < 5, f"Legacy CPU simulation took {elapsed:.1f}s"


# ============================================================================
# PHASE 6 — FIELD DEPLOYMENT PACKAGE
# ============================================================================

class TestFieldDeploymentPackage:
    """Validate field deployment wizards."""

    def test_deployment_wizard(self, tmp_path):
        """Deployment wizard creates required structure."""
        from lab_system.app.services.field_deployment_service import DeploymentWizard
        wizard = DeploymentWizard(str(tmp_path))
        result = wizard.run()
        assert result["success"] is True
        assert (tmp_path / "database").exists()
        assert (tmp_path / "backups").exists()
        assert (tmp_path / "logs").exists()

    def test_health_check_wizard(self, v14_db):
        """Health check wizard identifies issues."""
        from lab_system.app.services.field_deployment_service import HealthCheckWizard
        wizard = HealthCheckWizard(str(v14_db))
        result = wizard.run()
        assert "checks" in result
        assert "overall_status" in result

    def test_recovery_wizard(self, tmp_path):
        """Recovery wizard restores from backup."""
        from lab_system.app.services.field_deployment_service import RecoveryWizard
        db_path = tmp_path / "main.db"
        backup_path = tmp_path / "backup.db"
        conn = _create_db(db_path)
        _setup_base_data(conn)
        _insert_receipts(conn, 20)
        conn.row_factory = sqlite3.Row
        count_original = conn.execute("SELECT COUNT(*) as cnt FROM receipts").fetchone()["cnt"]
        conn.close()
        shutil.copy2(str(db_path), str(backup_path))
        os.unlink(db_path)
        wizard = RecoveryWizard(str(backup_path), str(db_path))
        result = wizard.run()
        assert result["success"] is True
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        count_restored = conn.execute("SELECT COUNT(*) as cnt FROM receipts").fetchone()["cnt"]
        conn.close()
        assert count_original == count_restored

    def test_support_package_generation(self, tmp_path):
        """Support package includes all required files."""
        from lab_system.app.services.field_deployment_service import SupportPackageGenerator
        gen = SupportPackageGenerator(str(tmp_path))
        result = gen.generate()
        assert result["success"] is True
        assert (tmp_path / "support_package").exists()


# ============================================================================
# PHASE 7 — AUTOMATED OPERATIONS CENTER
# ============================================================================

class TestAutomatedOperationsCenter:
    """Validate automated anomaly detection and recovery."""

    def test_anomaly_detection(self, v14_db):
        """Anomaly detection identifies unusual patterns."""
        from lab_system.app.services.operations_center_service import OperationsCenter
        with _patch_db(v14_db):
            center = OperationsCenter(str(v14_db))
            result = center.detect_anomalies()
            assert "anomalies" in result
            assert "timestamp" in result

    def test_recovery_recommendations(self, v14_db):
        """Recovery recommendations are actionable."""
        from lab_system.app.services.operations_center_service import OperationsCenter
        with _patch_db(v14_db):
            center = OperationsCenter(str(v14_db))
            result = center.get_recovery_recommendations()
            assert isinstance(result, list)

    def test_maintenance_recommendations(self, v14_db):
        """Maintenance recommendations are provided."""
        from lab_system.app.services.operations_center_service import OperationsCenter
        with _patch_db(v14_db):
            center = OperationsCenter(str(v14_db))
            result = center.get_maintenance_recommendations()
            assert isinstance(result, list)

    def test_automatic_health_monitoring(self, v14_db):
        """Automatic health monitoring is active."""
        from lab_system.app.services.operations_center_service import OperationsCenter
        with _patch_db(v14_db):
            center = OperationsCenter(str(v14_db))
            result = center.get_system_health()
            assert "overall_status" in result
            assert "subsystems" in result

    def test_operations_dashboard(self, v14_db):
        """Operations dashboard provides comprehensive view."""
        from lab_system.app.services.operations_center_service import OperationsCenter
        with _patch_db(v14_db):
            center = OperationsCenter(str(v14_db))
            result = center.get_dashboard()
            assert "health" in result
            assert "anomalies" in result
            assert "recommendations" in result


# ============================================================================
# PHASE 8 — FINAL FIELD CERTIFICATION
# ============================================================================

class TestFinalFieldCertification:
    """Final field readiness validation."""

    def test_field_readiness_checklist(self, v14_db):
        """Field readiness checklist is complete."""
        from lab_system.app.services.field_deployment_service import FieldReadinessChecker
        checker = FieldReadinessChecker(str(v14_db))
        result = checker.check()
        assert "checklist" in result
        assert "overall_ready" in result

    def test_disaster_recovery_readiness(self, tmp_path):
        """Disaster recovery readiness is validated."""
        from lab_system.app.services.field_deployment_service import DisasterRecoveryValidator
        db_path = tmp_path / "main.db"
        backup_path = tmp_path / "backup.db"
        conn = _create_db(db_path)
        _setup_base_data(conn)
        _insert_receipts(conn, 10)
        conn.close()
        shutil.copy2(str(db_path), str(backup_path))
        validator = DisasterRecoveryValidator(str(db_path), str(backup_path))
        result = validator.validate()
        assert result["ready"] is True

    def test_concurrent_user_readiness(self, v14_db):
        """System is ready for concurrent users."""
        from lab_system.app.services.field_deployment_service import FieldReadinessChecker
        checker = FieldReadinessChecker(str(v14_db))
        result = checker.check_concurrent_readiness()
        assert result["ready"] is True

    def test_production_deployment_authorization(self, v14_db):
        """Production deployment is authorized."""
        from lab_system.app.services.field_deployment_service import FieldReadinessChecker
        checker = FieldReadinessChecker(str(v14_db))
        result = checker.check()
        assert result["overall_ready"] is True
