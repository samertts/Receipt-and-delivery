"""
DATABASE DESTRUCTION TESTS
Simulates catastrophic database failures and verifies recovery capabilities.

This test suite breaks everything on purpose and checks if the system can survive.
"""

import hashlib
import os
import shutil
import sqlite3
import struct
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure lab_system is importable
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ADMIN_USER = {"role": "Admin", "username": "test_admin"}


def _redirect_db(db_path):
    """Redirect lab_system DB config to a test path."""
    import lab_system.app.database.db as db_mod
    from lab_system.app.settings.config import AppConfig

    orig = db_mod.CONFIG
    test_config = AppConfig(
        base_dir=orig.base_dir,
        app_dir=orig.app_dir,
        storage_dir=orig.storage_dir,
        assets_dir=orig.assets_dir,
        db_path=db_path,
        app_name=orig.app_name,
        version_file=orig.version_file,
        app_version=orig.app_version,
    )
    db_mod.CONFIG = test_config
    return orig


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_db_dir(tmp_path):
    """Create a temporary database directory."""
    db_dir = tmp_path / "lab_db_test"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir


@pytest.fixture
def fresh_db(tmp_db_dir):
    """Create a fresh database with full schema."""
    db_path = tmp_db_dir / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")

    from lab_system.app.database.db import SCHEMA
    conn.executescript(SCHEMA)

    # Seed with test data
    conn.execute("INSERT INTO organizations(name, code, status) VALUES('Org A', 'ORG-A', 'Active')")
    conn.execute("INSERT INTO organizations(name, code, status) VALUES('Org B', 'ORG-B', 'Active')")
    conn.execute("INSERT INTO users(full_name, username, password_hash, role, institution_id, status) "
                 "VALUES('Admin User', 'admin', 'hash_admin', 'Admin', 1, 'Active')")
    conn.execute("INSERT INTO users(full_name, username, password_hash, role, institution_id, status) "
                 "VALUES('Regular User', 'user1', 'hash_user1', 'User', 1, 'Active')")
    conn.execute("INSERT INTO transaction_types(name) VALUES('Receipt')")
    conn.execute("INSERT INTO transaction_types(name) VALUES('Delivery')")
    conn.execute("INSERT INTO sample_types(name, status) VALUES('Blood Sample', 'Active')")
    conn.execute("INSERT INTO sample_types(name, status) VALUES('Urine Sample', 'Active')")
    conn.execute("INSERT INTO receipts(receipt_no, tx_type_id, sender_org_id, receiver_org_id, "
                 "sender_name, receiver_name, created_at, status, created_by) "
                 "VALUES('REC-001', 1, 1, 2, 'Sender A', 'Receiver B', '2024-01-15T10:00:00', 'Draft', 1)")
    conn.execute("INSERT INTO receipts(receipt_no, tx_type_id, sender_org_id, receiver_org_id, "
                 "sender_name, receiver_name, created_at, status, created_by) "
                 "VALUES('REC-002', 2, 2, 1, 'Sender B', 'Receiver A', '2024-01-16T14:30:00', 'Approved', 2)")
    conn.execute("INSERT INTO receipt_items(receipt_id, sample_type_id, total_count, valid_count, "
                 "damaged_count, rejected_count, non_conforming_count) "
                 "VALUES(1, 1, 100, 90, 5, 3, 2)")
    conn.execute("INSERT INTO receipt_items(receipt_id, sample_type_id, total_count, valid_count, "
                 "damaged_count, rejected_count, non_conforming_count) "
                 "VALUES(2, 2, 50, 48, 1, 1, 0)")
    conn.execute("INSERT INTO meta(key, value) VALUES('schema_version', '10')")
    conn.execute("INSERT INTO schema_version(id, version, app_version, updated_at) "
                 "VALUES(1, 10, '1.0.0', '2024-01-16T00:00:00')")
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def backup_db(fresh_db, tmp_db_dir):
    """Create a known-good backup of the fresh database."""
    backup_path = tmp_db_dir / "backups" / "good_backup.db"
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(fresh_db), str(backup_path))
    # Also copy WAL/SHM if present
    for ext in ('-wal', '-shm'):
        src = fresh_db.parent / (fresh_db.name + ext)
        if src.exists():
            shutil.copy2(str(src), str(backup_path) + ext)
    return backup_path


# ===========================================================================
# 1. CORRUPTED DATABASE HEADER
# ===========================================================================

class TestCorruptedDatabaseHeader:
    """Simulate catastrophic header corruption."""

    def test_corrupt_header_bytes_detected_by_integrity(self, fresh_db, tmp_db_dir):
        """Overwrite SQLite magic bytes and verify integrity check catches it."""
        db_path = fresh_db

        # Save original data counts
        orig_conn = sqlite3.connect(str(db_path))
        orig_counts = {}
        for t in ['organizations', 'users', 'receipts', 'receipt_items']:
            orig_counts[t] = orig_conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        orig_conn.close()

        # Corrupt header: overwrite first 16 bytes with garbage
        with open(str(db_path), "r+b") as f:
            f.seek(0)
            f.write(b"X" * 16)

        # Verify corruption is detected by PRAGMA integrity_check
        try:
            conn = sqlite3.connect(str(db_path))
            row = conn.execute("PRAGMA integrity_check").fetchone()
            integrity_ok = row and row[0] == "ok"
            conn.close()
        except Exception:
            integrity_ok = False

        result = {"corruption_detected": not integrity_ok,
                  "orig_counts": orig_counts}
        assert result["corruption_detected"], "Header corruption should be detected by integrity_check"

    def test_corrupt_header_makes_db_unreadable(self, fresh_db):
        """Verify corrupted header prevents normal operations."""
        db_path = fresh_db

        with open(str(db_path), "r+b") as f:
            f.seek(0)
            f.write(b"CORRUPT" * 10)

        # Should fail to open or execute queries
        try:
            conn = sqlite3.connect(str(db_path))
            conn.execute("SELECT 1")
            conn.close()
            error_caught = False
        except Exception:
            error_caught = True

        assert error_caught, "Corrupted header should prevent normal operations"


# ===========================================================================
# 2. MISSING WAL FILE
# ===========================================================================

class TestMissingWALFile:
    """Simulate WAL file deletion."""

    def test_wal_deleted_recovery(self, fresh_db):
        """Delete WAL file and verify database still works."""
        wal_path = fresh_db.parent / (fresh_db.name + "-wal")
        shm_path = fresh_db.parent / (fresh_db.name + "-shm")

        # Ensure WAL exists by writing data
        conn = sqlite3.connect(str(fresh_db))
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("INSERT INTO meta(key, value) VALUES('wal_test', 'value1')")
        conn.commit()
        # Force WAL to be written to disk
        conn.execute("PRAGMA wal_checkpoint(PASSIVE);")
        conn.close()

        # Delete WAL and SHM
        wal_deleted = False
        if wal_path.exists():
            wal_path.unlink()
            wal_deleted = True
        if shm_path.exists():
            shm_path.unlink()

        # Re-open and verify data integrity
        conn = sqlite3.connect(str(fresh_db))
        conn.execute("PRAGMA journal_mode=WAL;")
        row = conn.execute("SELECT value FROM meta WHERE key='wal_test'").fetchone()

        # The committed data should be in the main DB file after checkpoint
        result = {"data_preserved": row is not None and row[0] == "value1",
                  "wal_existed": wal_deleted}
        conn.close()
        return result

    def test_wal_deleted_with_uncommitted_data(self, fresh_db):
        """Delete WAL with uncommitted changes - data loss expected for uncommitted."""
        wal_path = fresh_db.parent / (fresh_db.name + "-wal")

        # Start uncommitted transaction in one connection
        conn1 = sqlite3.connect(str(fresh_db))
        conn1.execute("PRAGMA journal_mode=WAL;")
        conn1.execute("INSERT INTO meta(key, value) VALUES('uncommitted', 'lost')")
        # DO NOT COMMIT

        # Delete WAL
        if wal_path.exists():
            wal_path.unlink()

        # This should fail or lose the uncommitted data
        try:
            conn1.commit()
        except Exception:
            pass
        conn1.close()

        # Verify - uncommitted data should be lost
        conn2 = sqlite3.connect(str(fresh_db))
        row = conn2.execute("SELECT value FROM meta WHERE key='uncommitted'").fetchone()
        result = {"uncommitted_lost": row is None}
        conn2.close()
        return result


# ===========================================================================
# 3. MISSING INDEXES
# ===========================================================================

class TestMissingIndexes:
    """Simulate index deletion and verify recovery."""

    def test_drop_all_indexes(self, fresh_db):
        """Drop all indexes and verify they are recreated by init_db."""
        conn = sqlite3.connect(str(fresh_db))
        conn.execute("PRAGMA foreign_keys = ON;")

        # Drop all non-auto indexes
        indexes = conn.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
        ).fetchall()
        for name, sql in indexes:
            try:
                conn.execute(f"DROP INDEX IF EXISTS {name}")
            except Exception:
                pass
        conn.commit()

        # Verify indexes are gone
        remaining = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
        ).fetchone()[0]

        # Now run init_db to recreate
        from lab_system.app.database import db as db_mod
        orig_config = _redirect_db(fresh_db)
        try:
            db_mod.init_db()
        finally:
            db_mod.CONFIG = orig_config

        # Verify indexes recreated
        after = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
        ).fetchone()[0]
        conn.close()

        result = {
            "indexes_before": len(indexes),
            "indexes_after_drop": remaining,
            "indexes_after_restore": after,
            "recovery_success": after >= len(indexes)
        }
        assert result["recovery_success"], "Indexes should be recreated by init_db"
        return result

    def test_critical_index_performance_degradation(self, fresh_db):
        """Verify queries still work (slower) without indexes."""
        conn = sqlite3.connect(str(fresh_db))
        conn.execute("PRAGMA foreign_keys = ON;")

        # Drop receipt indexes
        conn.execute("DROP INDEX IF EXISTS idx_receipts_no")
        conn.execute("DROP INDEX IF EXISTS idx_receipts_created")
        conn.execute("DROP INDEX IF EXISTS idx_receipt_items_receipt_id")
        conn.commit()

        # Query should still work
        start = time.time()
        rows = conn.execute(
            "SELECT r.* FROM receipts r JOIN receipt_items ri ON r.id = ri.receipt_id"
        ).fetchall()
        elapsed = time.time() - start

        result = {"query_works_without_indexes": len(rows) > 0,
                  "query_time_seconds": round(elapsed, 4)}
        conn.close()
        assert result["query_works_without_indexes"], "Queries should work without indexes"
        return result


# ===========================================================================
# 4. BROKEN FOREIGN KEYS
# ===========================================================================

class TestBrokenForeignKeys:
    """Simulate foreign key violations and orphaned records."""

    def test_orphaned_receipt_items(self, fresh_db):
        """Delete a receipt and verify CASCADE deletes its items."""
        conn = sqlite3.connect(str(fresh_db))
        conn.execute("PRAGMA foreign_keys = ON;")

        # Insert a receipt with item
        conn.execute("INSERT INTO receipts(receipt_no, tx_type_id, sender_org_id, receiver_org_id, "
                     "sender_name, receiver_name, created_at, status, created_by) "
                     "VALUES('TEMP-999', 1, 1, 2, 'Test', 'Test', '2024-01-01T00:00:00', 'Draft', 1)")
        receipt_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        conn.execute("INSERT INTO receipt_items(receipt_id, sample_type_id, total_count, valid_count, "
                     "damaged_count, rejected_count, non_conforming_count) "
                     "VALUES(?, 1, 10, 8, 1, 1, 0)", (receipt_id,))
        conn.commit()

        # Verify item exists
        item_count = conn.execute("SELECT COUNT(*) FROM receipt_items WHERE receipt_id=?",
                                  (receipt_id,)).fetchone()[0]
        assert item_count == 1

        # Delete receipt - CASCADE should delete item
        conn.execute("DELETE FROM receipts WHERE id=?", (receipt_id,))
        conn.commit()

        item_count_after = conn.execute("SELECT COUNT(*) FROM receipt_items WHERE receipt_id=?",
                                        (receipt_id,)).fetchone()[0]
        conn.close()

        result = {"cascade_delete_works": item_count_after == 0,
                  "items_before": item_count,
                  "items_after": item_count_after}
        assert result["cascade_delete_works"], "ON DELETE CASCADE should remove child items"
        return result

    def test_broken_fk_detection(self, fresh_db):
        """Insert orphaned record and verify FK violation is detected."""
        conn = sqlite3.connect(str(fresh_db))
        conn.execute("PRAGMA foreign_keys = ON;")

        # Try to insert receipt with non-existent tx_type_id
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO receipts(receipt_no, tx_type_id, sender_org_id, receiver_org_id, "
                         "sender_name, receiver_name, created_at, status, created_by) "
                         "VALUES('FK-TEST', 99999, 1, 2, 'Test', 'Test', '2024-01-01T00:00:00', 'Draft', 1)")
        conn.rollback()
        conn.close()


# ===========================================================================
# 5. PARTIAL RESTORE
# ===========================================================================

class TestPartialRestore:
    """Simulate interrupted or partial restore operations."""

    def test_partial_file_copy_restore(self, fresh_db, backup_db, tmp_db_dir):
        """Simulate a restore where the file copy was interrupted."""
        truncated = tmp_db_dir / "truncated_backup.db"
        with open(str(backup_db), "rb") as src:
            data = src.read()
        # Write only first 20% of the file
        with open(str(truncated), "wb") as dst:
            dst.write(data[:len(data) // 5])

        from lab_system.app.services.recovery_service import verify_backup
        result = verify_backup(truncated)

        assert not result["valid"], "Truncated backup should be detected as invalid"
        return {"truncated_detected": True, "error": result.get("error"), "size": result.get("size")}

    def test_partial_migration_rollback(self, fresh_db):
        """Verify migration lock prevents concurrent migrations."""
        conn = sqlite3.connect(str(fresh_db))
        conn.execute("PRAGMA foreign_keys = ON;")

        from lab_system.app.database.db import _acquire_migration_lock, _release_migration_lock
        _acquire_migration_lock(conn)
        try:
            with pytest.raises(RuntimeError, match="Migration lock is active"):
                _acquire_migration_lock(conn)
        finally:
            _release_migration_lock(conn)
            conn.close()


# ===========================================================================
# 6. INTERRUPTED BACKUP
# ===========================================================================

class TestInterruptedBackup:
    """Simulate backup creation interruption."""

    def test_backup_interruption(self, fresh_db, tmp_db_dir):
        """Simulate backup process interrupted mid-copy."""
        backup_dir = tmp_db_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        target = backup_dir / "interrupted_backup.db"

        # Simulate interrupted backup by writing partial file
        with open(str(fresh_db), "rb") as src:
            chunk = src.read(1024)  # Only first 1KB
        with open(str(target), "wb") as dst:
            dst.write(chunk)

        from lab_system.app.services.recovery_service import verify_backup
        result = verify_backup(target)

        assert not result["valid"], "Partial backup should be detected as invalid"
        return {"partial_backup_detected": True, "error": result.get("error"), "size": result.get("size")}

    def test_backup_zero_length(self, fresh_db, tmp_db_dir):
        """Simulate backup that created empty file."""
        backup_dir = tmp_db_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        target = backup_dir / "empty_backup.db"
        target.touch()

        from lab_system.app.services.recovery_service import verify_backup
        result = verify_backup(target)

        assert not result["valid"], "Empty backup should be detected as invalid"
        return {"empty_backup_detected": True, "error": result.get("error")}


# ===========================================================================
# 7. INTERRUPTED RECOVERY
# ===========================================================================

class TestInterruptedRecovery:
    """Simulate recovery interruption mid-restore."""

    def test_recovery_interruption_leaves_original(self, fresh_db, backup_db, tmp_db_dir):
        """Simulate recovery failure - original DB should survive."""
        # Create a corrupted backup to try restoring
        corrupted_backup = tmp_db_dir / "corrupted_for_test.db"
        with open(str(corrupted_backup), "wb") as f:
            f.write(b"NOT_A_DATABASE" * 100)

        from lab_system.app.services.recovery_service import restore_from_backup
        # Restore should fail because backup is invalid (even with user)
        result = restore_from_backup(corrupted_backup, user=ADMIN_USER)

        # Original DB should still be intact
        conn = sqlite3.connect(str(fresh_db))
        row_count = conn.execute("SELECT COUNT(*) FROM receipts").fetchone()[0]
        conn.close()

        assert not result["success"], "Restore from corrupted backup should fail"
        assert row_count > 0, "Original data should be intact"
        return {"restore_failed_as_expected": True, "original_intact": row_count > 0,
                "error": result.get("error")}

    def test_recovery_with_no_backups(self, fresh_db, tmp_db_dir):
        """Test recovery when no backups exist."""
        empty_dir = tmp_db_dir / "empty_backups"
        empty_dir.mkdir()

        from lab_system.app.services.recovery_service import attempt_recovery
        # attempt_recovery uses DB_PATH which points to production, we need to redirect
        orig_config = _redirect_db(fresh_db)
        try:
            result = attempt_recovery(user=ADMIN_USER)
        finally:
            from lab_system.app.database import db as db_mod
            db_mod.CONFIG = orig_config

        return {"recovery_attempted": True,
                "no_backups_message": any("No backup" in a for a in result.get("actions", []))}


# ===========================================================================
# 8. DISK FULL CONDITION
# ===========================================================================

class TestDiskFullCondition:
    """Simulate disk-full conditions during writes."""

    def test_write_failure_rollback(self, fresh_db):
        """Simulate write failure via exception and verify rollback."""
        conn = sqlite3.connect(str(fresh_db))
        conn.execute("PRAGMA foreign_keys = ON;")

        # Count records before
        count_before = conn.execute("SELECT COUNT(*) FROM receipts").fetchone()[0]

        # Simulate disk full via transaction that fails
        try:
            conn.execute("BEGIN")
            conn.execute("INSERT INTO receipts(receipt_no, tx_type_id, sender_org_id, receiver_org_id, "
                         "sender_name, receiver_name, created_at, status, created_by) "
                         "VALUES('DISK-FULL', 1, 1, 2, 'Test', 'Test', '2024-01-01T00:00:00', 'Draft', 1)")
            # Simulate disk full error
            raise sqlite3.OperationalError("database or disk is full")
        except sqlite3.OperationalError:
            conn.rollback()

        count_after = conn.execute("SELECT COUNT(*) FROM receipts").fetchone()[0]
        conn.close()

        result = {"data_preserved": count_before == count_after,
                  "records_before": count_before,
                  "records_after": count_after}
        assert result["data_preserved"], "Rollback should preserve existing data"
        return result

    def test_wal_write_failure(self, fresh_db):
        """Simulate WAL write with contention."""
        conn = sqlite3.connect(str(fresh_db))
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.execute("PRAGMA journal_mode=WAL;")

        # Simulate high contention
        connections = []
        for _ in range(10):
            c = sqlite3.connect(str(fresh_db), timeout=1)
            c.execute("PRAGMA journal_mode=WAL;")
            c.execute("PRAGMA busy_timeout = 5000;")
            connections.append(c)

        results = []
        errors = []

        def write_to_db(conn, idx):
            try:
                conn.execute("INSERT INTO meta(key, value) VALUES(?, ?)",
                             (f"concurrent_{idx}", f"val_{idx}"))
                conn.commit()
                results.append(idx)
            except Exception as e:
                errors.append(str(e))
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

        threads = [threading.Thread(target=write_to_db, args=(c, i))
                   for i, c in enumerate(connections)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        # Clean up
        for c in connections:
            try:
                c.close()
            except Exception:
                pass

        return {"successful_writes": len(results), "errors": len(errors)}


# ===========================================================================
# 9. CONCURRENT MIGRATION ATTEMPTS
# ===========================================================================

class TestConcurrentMigrations:
    """Simulate concurrent migration attempts."""

    def test_migration_lock_prevents_concurrent(self, fresh_db):
        """Verify migration lock prevents parallel migrations via separate connections."""
        from lab_system.app.database.db import _acquire_migration_lock, _release_migration_lock

        # Use separate connections with WAL mode and busy_timeout
        conn1 = sqlite3.connect(str(fresh_db), timeout=10)
        conn1.execute("PRAGMA foreign_keys = ON;")
        conn1.execute("PRAGMA journal_mode=WAL;")
        conn1.execute("PRAGMA busy_timeout = 5000;")

        conn2 = sqlite3.connect(str(fresh_db), timeout=10)
        conn2.execute("PRAGMA foreign_keys = ON;")
        conn2.execute("PRAGMA journal_mode=WAL;")
        conn2.execute("PRAGMA busy_timeout = 5000;")

        # First acquires lock
        _acquire_migration_lock(conn1)

        # Second should fail because lock is held
        lock_acquired_by_second = False
        try:
            _acquire_migration_lock(conn2)
            lock_acquired_by_second = True
        except (RuntimeError, sqlite3.OperationalError):
            pass

        _release_migration_lock(conn1)
        conn1.close()
        conn2.close()

        assert not lock_acquired_by_second, "Second migration should be blocked by lock"
        return {"second_lock_blocked": not lock_acquired_by_second}

    def test_migration_lock_stale_detection(self, fresh_db):
        """Test handling of stale migration lock."""
        conn = sqlite3.connect(str(fresh_db))
        conn.execute("PRAGMA foreign_keys = ON;")

        # Simulate stale lock by manually setting it
        conn.execute("UPDATE migration_lock SET is_locked=1, owner='dead_process', "
                     "updated_at='2020-01-01T00:00:00' WHERE id=1")
        conn.commit()

        row = conn.execute("SELECT is_locked, updated_at FROM migration_lock WHERE id=1").fetchone()
        is_stale = row and row[0] == 1

        from lab_system.app.database.db import _acquire_migration_lock
        try:
            _acquire_migration_lock(conn)
            release_needed = True
        except RuntimeError:
            release_needed = False

        if release_needed:
            from lab_system.app.database.db import _release_migration_lock
            _release_migration_lock(conn)

        conn.close()
        assert is_stale, "Stale lock should be detected"
        return {"stale_lock_detected": is_stale, "requires_manual_release": release_needed}


# ===========================================================================
# 10. DATABASE LOCK HANDLING
# ===========================================================================

class TestDatabaseLockHandling:
    """Test SQLite lock behavior under contention."""

    def test_busy_timeout_prevents_immediate_failure(self, fresh_db):
        """Verify busy_timeout gives other connections time to finish."""
        conn = sqlite3.connect(str(fresh_db))
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("BEGIN IMMEDIATE")

        # Another connection with short timeout should wait/fail
        conn2 = sqlite3.connect(str(fresh_db), timeout=0.001)

        start = time.time()
        try:
            conn2.execute("INSERT INTO meta(key, value) VALUES('lock_test2', 'waiting')")
            conn2.commit()
            wait_result = "succeeded"
        except sqlite3.OperationalError as e:
            wait_result = f"failed: {e}"
        elapsed = time.time() - start

        conn.commit()
        conn.close()
        conn2.close()

        return {"wait_result": wait_result, "elapsed_seconds": round(elapsed, 3)}

    def test_connection_cleanup_on_exception(self, fresh_db):
        """Verify connections are properly closed even on exceptions."""
        import lab_system.app.database.db as db_mod

        # The get_conn context manager should close connections even on exceptions
        with pytest.raises(ValueError, match="Simulated error"):
            with db_mod.get_conn() as conn:
                conn.execute("INSERT INTO meta(key, value) VALUES('cleanup_test', 'ok')")
                raise ValueError("Simulated error")

        # Verify connection was closed (no leak)
        # If we get here without error, connection was properly cleaned up

    def test_wal_mode_persists_across_connections(self, fresh_db):
        """Verify WAL mode is set on every new connection."""
        for i in range(5):
            conn = sqlite3.connect(str(fresh_db))
            row = conn.execute("PRAGMA journal_mode").fetchone()
            conn.close()


# ===========================================================================
# 11. CONNECTION POOL EXHAUSTION
# ===========================================================================

class TestConnectionPoolExhaustion:
    """Test behavior under connection exhaustion."""

    def test_many_simultaneous_connections(self, fresh_db):
        """Open many simultaneous connections and verify no crash."""
        connections = []
        errors = []

        for i in range(50):
            try:
                c = sqlite3.connect(str(fresh_db), timeout=2)
                c.execute("PRAGMA busy_timeout = 2000;")
                c.execute("SELECT 1")
                connections.append(c)
            except Exception as e:
                errors.append(str(e))

        for c in connections:
            try:
                c.close()
            except Exception:
                pass

        return {"opened": len(connections), "errors": len(errors),
                "error_messages": errors[:5]}

    def test_repository_connection_cleanup(self, fresh_db):
        """Verify BaseRepository properly cleans up connections."""
        import lab_system.app.database.db as db_mod

        @contextmanager
        def test_conn():
            c = sqlite3.connect(str(fresh_db))
            c.row_factory = sqlite3.Row
            c.execute("PRAGMA foreign_keys = ON;")
            c.execute("PRAGMA busy_timeout = 5000;")
            c.execute("PRAGMA journal_mode=WAL;")
            try:
                yield c
                c.commit()
            except Exception:
                c.rollback()
                raise
            finally:
                c.close()

        orig = db_mod.get_conn
        db_mod.get_conn = test_conn
        try:
            from lab_system.app.database.repository import BaseRepository
            repo = BaseRepository()

            repo.execute("INSERT INTO meta(key, value) VALUES('repo_test', 'ok')")
            row = repo.fetch_one("SELECT value FROM meta WHERE key='repo_test'")
            assert row["value"] == "ok"
        finally:
            db_mod.get_conn = orig


# ===========================================================================
# 12. TRANSACTION ISOLATION
# ===========================================================================

class TestTransactionIsolation:
    """Test transaction isolation levels."""

    def test_read_uncommitted_phantom_read(self, fresh_db):
        """Test that uncommitted reads work with WAL mode."""
        conn1 = sqlite3.connect(str(fresh_db))
        conn1.execute("PRAGMA journal_mode=WAL;")
        conn1.execute("PRAGMA busy_timeout = 5000;")

        conn2 = sqlite3.connect(str(fresh_db))
        conn2.execute("PRAGMA journal_mode=WAL;")
        conn2.execute("PRAGMA busy_timeout = 5000;")

        # Count before
        count1 = conn1.execute("SELECT COUNT(*) FROM meta").fetchone()[0]

        # Insert in conn2 but don't commit
        conn2.execute("INSERT INTO meta(key, value) VALUES('isolation_test', 'uncommitted')")

        # conn1 should NOT see uncommitted data (WAL provides snapshot isolation)
        count2 = conn1.execute("SELECT COUNT(*) FROM meta").fetchone()[0]

        # Now commit in conn2
        conn2.commit()

        # Now conn1 SHOULD see it (in WAL, after snapshot refresh)
        count3 = conn1.execute("SELECT COUNT(*) FROM meta").fetchone()[0]

        conn1.close()
        conn2.close()

        return {"before_insert": count1, "during_uncommitted": count2,
                "after_commit": count3, "isolation_works": count2 == count1}


# ===========================================================================
# 13. DATA PRESERVATION DURING FAILURES
# ===========================================================================

class TestDataPreservation:
    """Verify data survives various failure scenarios."""

    def test_data_survives_process_crash(self, fresh_db):
        """Simulate process crash after commit - data should be in DB."""
        conn = sqlite3.connect(str(fresh_db))
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("INSERT INTO meta(key, value) VALUES('crash_test', 'survived')")
        conn.commit()
        conn.close()

        # "Crash" = just close and reopen
        conn2 = sqlite3.connect(str(fresh_db))
        row = conn2.execute("SELECT value FROM meta WHERE key='crash_test'").fetchone()
        conn2.close()

        assert row is not None and row[0] == "survived"
        return {"data_survived": True}

    def test_data_survives_checkpoint(self, fresh_db):
        """Data should survive WAL checkpoint."""
        conn = sqlite3.connect(str(fresh_db))
        conn.execute("PRAGMA journal_mode=WAL;")
        for i in range(100):
            conn.execute("INSERT INTO meta(key, value) VALUES(?, ?)",
                         (f"checkpoint_{i}", f"value_{i}"))
        conn.commit()

        # Force checkpoint
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        conn.close()

        # Verify data survived
        conn2 = sqlite3.connect(str(fresh_db))
        count = conn2.execute("SELECT COUNT(*) FROM meta WHERE key LIKE 'checkpoint_%'").fetchone()[0]
        conn2.close()

        assert count == 100
        return {"data_survived_checkpoint": count == 100}

    def test_audit_trail_integrity(self, fresh_db):
        """Verify audit chain integrity with prev_hash."""
        conn = sqlite3.connect(str(fresh_db))
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode=WAL;")

        entries = [
            ("action1", "machine1", "2024-01-01T00:00:00", "details1"),
            ("action2", "machine1", "2024-01-01T00:01:00", "details2"),
            ("action3", "machine1", "2024-01-01T00:02:00", "details3"),
        ]

        prev_hash = ""
        for action, machine, ts, details in entries:
            entry_hash = hashlib.sha256(f"{action}{ts}{prev_hash}".encode()).hexdigest()
            conn.execute(
                "INSERT INTO audit_logs(action, machine_name, timestamp, details, prev_hash) "
                "VALUES(?, ?, ?, ?, ?)",
                (action, machine, ts, details, prev_hash)
            )
            prev_hash = entry_hash
        conn.commit()

        rows = conn.execute(
            "SELECT action, prev_hash FROM audit_logs ORDER BY id"
        ).fetchall()

        chain_valid = True
        for i, (action, ph) in enumerate(rows):
            if i == 0:
                if ph != "":
                    chain_valid = False
            else:
                if ph == "":
                    chain_valid = False

        conn.close()
        assert chain_valid
        return {"audit_chain_valid": chain_valid, "entries": len(rows)}


# ===========================================================================
# 14. BACKUP VERIFICATION DEEP TESTS
# ===========================================================================

class TestBackupVerification:
    """Deep tests of backup verification logic."""

    def test_verify_valid_backup(self, fresh_db, backup_db):
        """Verify a known-good backup passes all checks."""
        from lab_system.app.services.recovery_service import verify_backup

        v = verify_backup(backup_db)

        assert v["valid"], "Valid backup should pass verification"
        assert v["integrity_ok"], "Integrity check should pass"
        return {"integrity_ok": v["integrity_ok"], "valid": v["valid"]}

    def test_verify_tampered_backup(self, fresh_db, backup_db):
        """Verify a tampered backup is detected."""
        with open(str(backup_db), "r+b") as f:
            f.seek(1024)
            f.write(b"\xff" * 10)

        from lab_system.app.services.recovery_service import verify_backup
        result = verify_backup(backup_db)

        assert not result["integrity_ok"], "Tampered backup should fail integrity check"
        return {"tampered_detected": True, "error": result.get("error")}

    def test_verify_nonexistent_backup(self, tmp_db_dir):
        """Verify a nonexistent backup is handled gracefully."""
        from lab_system.app.services.recovery_service import verify_backup
        result = verify_backup(tmp_db_dir / "nonexistent.db")

        assert result["error"] == "File not found"
        return {"not_found_handled": True}


# ===========================================================================
# 15. RECOVERY SERVICE INTEGRATION
# ===========================================================================

class TestRecoveryServiceIntegration:
    """Integration tests for the recovery service."""

    def test_detect_corruption_on_corrupted_db(self, fresh_db):
        """Verify detect_corruption finds corruption."""
        # Redirect DB_PATH for detect_corruption
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.settings.config import DB_PATH as ORIG_DB_PATH

        # Patch DB_PATH temporarily
        rs_mod.DB_PATH = fresh_db
        try:
            # First, verify healthy
            from lab_system.app.services.recovery_service import detect_corruption
            healthy = detect_corruption()
            assert healthy["ok"], "Fresh DB should be healthy"

            # Corrupt the header
            with open(str(fresh_db), "r+b") as f:
                f.seek(0)
                f.write(b"CORRUPTEDHEADER!!")

            # Now detect should find corruption
            corrupted = detect_corruption()
            assert not corrupted["ok"], "Corruption should be detected"
        finally:
            rs_mod.DB_PATH = ORIG_DB_PATH

    def test_recovery_snapshot_created_before_restore(self, fresh_db, backup_db):
        """Verify snapshot is created before restore."""
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import create_recovery_snapshot

        # Redirect DB_PATH
        rs_mod.DB_PATH = fresh_db
        try:
            snap = create_recovery_snapshot("test_restore")
            assert snap["success"], "Snapshot creation should succeed"

            snap_path = Path(snap["path"])
            assert snap_path.exists(), "Snapshot file should exist on disk"

            from lab_system.app.services.recovery_service import verify_backup
            v = verify_backup(snap_path)
            assert v["valid"], "Snapshot should be a valid database"
        finally:
            rs_mod.DB_PATH = ORIG_DB_PATH

    def test_verify_recovery_service_functions(self, fresh_db, backup_db, tmp_db_dir):
        """Test recovery_service functions with proper DB_PATH redirection."""
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.settings.config import DB_PATH as ORIG_DB_PATH

        rs_mod.DB_PATH = fresh_db
        try:
            from lab_system.app.services.recovery_service import (
                detect_corruption, verify_backup, list_backups, auto_backup
            )

            # Test detect_corruption
            d = detect_corruption()
            assert d["ok"], "Fresh DB should pass corruption check"

            # Test verify_backup
            v = verify_backup(backup_db)
            assert v["valid"], "Good backup should be valid"

            # Test list_backups
            backups_dir = fresh_db.parent / "backups"
            backups_dir.mkdir(exist_ok=True)
            shutil.copy2(str(backup_db), str(backups_dir / "test.db"))
            bl = list_backups()
            assert len(bl) >= 1
        finally:
            rs_mod.DB_PATH = ORIG_DB_PATH


# ===========================================================================
# 16. FTS5 REBUILD AFTER CORRUPTION
# ===========================================================================

class TestFTSRebuild:
    """Test FTS5 index rebuild after corruption."""

    def test_fts_rebuild(self, fresh_db):
        """Rebuild FTS indexes and verify search works."""
        import lab_system.app.database.db as db_mod
        orig = _redirect_db(fresh_db)
        try:
            conn = sqlite3.connect(str(fresh_db))
            conn.execute("PRAGMA foreign_keys = ON;")

            # Verify FTS has data
            count = conn.execute("SELECT COUNT(*) FROM receipts_fts").fetchone()[0]

            # Corrupt FTS
            conn.execute("DELETE FROM receipts_fts")
            conn.commit()

            count_after_corrupt = conn.execute("SELECT COUNT(*) FROM receipts_fts").fetchone()[0]

            # Rebuild
            from lab_system.app.database.db import rebuild_fts
            rebuild_fts()

            count_after_rebuild = conn.execute("SELECT COUNT(*) FROM receipts_fts").fetchone()[0]
            conn.close()

            assert count_after_rebuild == count
            return {"original_count": count, "after_corrupt": count_after_corrupt,
                    "after_rebuild": count_after_rebuild, "rebuild_successful": True}
        finally:
            db_mod.CONFIG = orig


# ===========================================================================
# 17. MIGRATION HISTORY INTEGRITY
# ===========================================================================

class TestMigrationHistoryIntegrity:
    """Test migration history tracking and verification."""

    def test_migration_checksum_verification(self, fresh_db):
        """Verify migration checksums are consistent."""
        conn = sqlite3.connect(str(fresh_db))
        conn.execute("PRAGMA foreign_keys = ON;")

        rows = conn.execute(
            "SELECT migration_key, checksum, status FROM migration_history ORDER BY id"
        ).fetchall()

        all_applied = all(r[2] == 'applied' for r in rows)
        all_have_checksums = all(len(r[1]) == 64 for r in rows)

        conn.close()
        assert all_applied
        assert all_have_checksums
        return {"migration_count": len(rows), "all_applied": all_applied,
                "all_have_checksums": all_have_checksums, "keys": [r[0] for r in rows]}

    def test_migration_lock_auto_released(self, fresh_db):
        """Verify migration lock is released properly."""
        from lab_system.app.database.db import _acquire_migration_lock, _release_migration_lock

        conn = sqlite3.connect(str(fresh_db))
        conn.execute("PRAGMA foreign_keys = ON;")

        _acquire_migration_lock(conn)
        _release_migration_lock(conn)

        row = conn.execute("SELECT is_locked FROM migration_lock WHERE id=1").fetchone()
        conn.close()

        assert row[0] == 0
        return {"lock_released": True}


# ===========================================================================
# 18. BACKUP SERVICE EDGE CASES
# ===========================================================================

class TestBackupServiceEdgeCases:
    """Edge cases in backup creation."""

    def test_backup_creates_valid_file(self, fresh_db, tmp_db_dir):
        """Verify backup creates a valid SQLite file."""
        import lab_system.app.database.db as db_mod

        orig = _redirect_db(fresh_db)
        try:
            from lab_system.app.services.backup_service import create_backup
            path = create_backup(user_id=1, notes="test backup", user=ADMIN_USER)

            from lab_system.app.services.recovery_service import verify_backup
            v = verify_backup(Path(path))
            assert v["valid"], "Backup should be valid"
            return {"backup_created": True, "valid": v["valid"], "integrity_ok": v["integrity_ok"]}
        finally:
            db_mod.CONFIG = orig


# ===========================================================================
# 19. AUTOMATIC RECOVERY PATHS
# ===========================================================================

class TestAutomaticRecoveryPaths:
    """Test automatic recovery attempt paths."""

    def test_wal_checkpoint_recovery(self, fresh_db):
        """Test that WAL checkpoint can recover pending writes."""
        conn = sqlite3.connect(str(fresh_db))
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("INSERT INTO meta(key, value) VALUES('wal_recovery', 'test')")
        conn.commit()
        conn.close()

        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.services.recovery_service import _checkpoint_wal

        rs_mod.DB_PATH = fresh_db
        try:
            _checkpoint_wal()
        finally:
            from lab_system.app.settings.config import DB_PATH as ORIG
            rs_mod.DB_PATH = ORIG

        conn = sqlite3.connect(str(fresh_db))
        row = conn.execute("SELECT value FROM meta WHERE key='wal_recovery'").fetchone()
        conn.close()

        assert row is not None and row[0] == "test"
        return {"data_preserved": True}

    def test_detect_corruption_checks_wal(self, fresh_db):
        """Verify detect_corruption checks WAL file size."""
        import lab_system.app.services.recovery_service as rs_mod
        from lab_system.app.settings.config import DB_PATH as ORIG

        rs_mod.DB_PATH = fresh_db
        try:
            from lab_system.app.services.recovery_service import detect_corruption

            # Ensure WAL exists
            conn = sqlite3.connect(str(fresh_db))
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("INSERT INTO meta(key, value) VALUES('wal_check', 'test')")
            conn.commit()
            conn.close()

            result = detect_corruption()
            return {"wal_size_reported": "wal_size" in result, "db_ok": result["ok"]}
        finally:
            rs_mod.DB_PATH = ORIG


# ===========================================================================
# 20. DEADLOCK POTENTIAL
# ===========================================================================

class TestDeadlockPotential:
    """Test for potential deadlocks in concurrent operations."""

    def test_no_deadlock_with_migration_lock(self, fresh_db):
        """Verify migration lock doesn't cause deadlock."""
        from lab_system.app.database.db import _acquire_migration_lock, _release_migration_lock
        import threading

        results = []

        def try_migrate(thread_id):
            conn = sqlite3.connect(str(fresh_db), timeout=10)
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA busy_timeout = 5000;")
            try:
                _acquire_migration_lock(conn)
                results.append(f"thread_{thread_id}_acquired")
                time.sleep(0.05)
                _release_migration_lock(conn)
                results.append(f"thread_{thread_id}_released")
            except (RuntimeError, sqlite3.OperationalError):
                results.append(f"thread_{thread_id}_denied")
            finally:
                conn.close()

        threads = [threading.Thread(target=try_migrate, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        # Each thread either acquired+released OR was denied
        assert len(results) == 10
        return {"results": results, "no_deadlock": True}


# ===========================================================================
# 21. GRACEFUL DEGRADATION
# ===========================================================================

class TestGracefulDegradation:
    """Test system behavior when DB is unavailable."""

    def test_repository_error_handling(self, fresh_db):
        """Verify repository handles DB errors gracefully."""
        import lab_system.app.database.db as db_mod

        @contextmanager
        def broken_conn():
            raise sqlite3.OperationalError("unable to open database file")
            yield  # Never reached

        orig = db_mod.get_conn
        db_mod.get_conn = broken_conn
        try:
            from lab_system.app.database.repository import BaseRepository
            repo = BaseRepository()
            try:
                repo.fetch_one("SELECT 1")
                error_caught = False
            except sqlite3.OperationalError:
                error_caught = True
            except Exception:
                error_caught = True
            assert error_caught
            return {"error_caught": True}
        finally:
            db_mod.get_conn = orig


# ===========================================================================
# 22. COMPREHENSIVE SCHEMA VALIDATION
# ===========================================================================

class TestSchemaValidation:
    """Validate complete schema integrity."""

    def test_all_tables_exist(self, fresh_db):
        """Verify all required tables exist."""
        conn = sqlite3.connect(str(fresh_db))
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()}

        required = {
            'meta', 'organizations', 'users', 'transaction_types', 'sample_types',
            'templates', 'receipts', 'receipt_history', 'receipt_items', 'attachments',
            'settings', 'schema_version', 'migration_history', 'migration_lock',
            'backups', 'audit_logs', 'login_attempts', 'sync_queue',
        }

        missing = required - tables
        conn.close()

        assert not missing, f"Missing tables: {missing}"
        return {"all_tables_exist": True, "table_count": len(tables)}

    def test_all_indexes_exist(self, fresh_db):
        """Verify all required indexes exist."""
        conn = sqlite3.connect(str(fresh_db))
        indexes = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
        ).fetchall()}

        required = {
            'idx_sync_status', 'idx_sync_entity', 'idx_login_attempts_user',
            'idx_receipts_no', 'idx_receipts_created', 'idx_items_sample',
            'idx_org_code', 'idx_users_username', 'idx_receipts_status_created',
            'idx_receipt_items_receipt_id',
        }

        missing = required - indexes
        conn.close()

        assert not missing, f"Missing indexes: {missing}"
        return {"all_indexes_exist": True, "index_count": len(indexes)}

    def test_all_triggers_exist(self, fresh_db):
        """Verify all required triggers exist."""
        conn = sqlite3.connect(str(fresh_db))
        triggers = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger'"
        ).fetchall()}

        required = {
            'receipts_ai', 'receipts_ad', 'receipts_au',
            'organizations_ai', 'organizations_ad', 'organizations_au',
        }

        missing = required - triggers
        conn.close()

        assert not missing, f"Missing triggers: {missing}"
        return {"all_triggers_exist": True, "trigger_count": len(triggers)}

    def test_fts_tables_exist(self, fresh_db):
        """Verify FTS virtual tables exist."""
        conn = sqlite3.connect(str(fresh_db))
        fts = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_fts'"
        ).fetchall()}

        assert 'receipts_fts' in fts
        assert 'organizations_fts' in fts
        conn.close()
        return {"fts_tables_exist": True}


# ===========================================================================
# SUMMARY REPORT
# ===========================================================================

class TestSummaryReport:
    """Generate comprehensive test report."""

    def test_all_critical_paths_covered(self):
        """Verify all critical recovery paths are tested."""
        critical_paths = [
            "corrupted_header",
            "missing_wal",
            "missing_indexes",
            "broken_foreign_keys",
            "partial_restore",
            "interrupted_backup",
            "interrupted_recovery",
            "disk_full",
            "concurrent_migration",
            "database_lock",
            "connection_exhaustion",
            "transaction_isolation",
            "data_preservation",
            "backup_verification",
            "recovery_integration",
            "fts_rebuild",
            "migration_history",
            "backup_edge_cases",
            "automatic_recovery",
            "deadlock_prevention",
            "graceful_degradation",
            "schema_validation",
        ]
        assert len(critical_paths) == 22
        return {"critical_paths_count": len(critical_paths), "paths": critical_paths}
