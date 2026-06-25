"""Sync service tests."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _seed_sync_db(conn):
    """Create sync_queue table if it doesn't exist."""
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sync_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            payload TEXT DEFAULT '',
            idempotency_key TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'pending',
            retry_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT '',
            synced_at TEXT DEFAULT ''
        )
    """)
    conn.commit()


class TestSyncServiceEnqueue:
    def test_enqueue_create(self, fresh_db, seed_data):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        entry_id = svc.enqueue("receipts", 1, "create", '{"test": true}')
        assert entry_id > 0

    def test_enqueue_update(self, fresh_db, seed_data):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        entry_id = svc.enqueue("receipts", 1, "update", "")
        assert entry_id > 0

    def test_enqueue_delete(self, fresh_db, seed_data):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        entry_id = svc.enqueue("receipts", 1, "delete", "")
        assert entry_id > 0

    def test_enqueue_invalid_action_raises(self, fresh_db, seed_data):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        with pytest.raises(ValueError, match="Invalid sync action"):
            svc.enqueue("receipts", 1, "invalid")


class TestSyncServicePending:
    def test_empty_pending(self, fresh_db, seed_data):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        pending = svc.get_pending()
        assert len(pending) == 0

    def test_pending_after_enqueue(self, fresh_db, seed_data):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        svc.enqueue("receipts", 1, "create", "")
        pending = svc.get_pending()
        assert len(pending) == 1
        assert pending[0].entity_type == "receipts"
        assert pending[0].entity_id == 1
        assert pending[0].action == "create"


class TestSyncServiceMarkSynced:
    def test_mark_synced(self, fresh_db, seed_data):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        entry_id = svc.enqueue("receipts", 1, "create", "")
        svc.mark_synced(entry_id)
        pending = svc.get_pending()
        assert len(pending) == 0

    def test_mark_synced_batch(self, fresh_db, seed_data):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        id1 = svc.enqueue("receipts", 1, "create", "")
        id2 = svc.enqueue("receipts", 2, "update", "")
        svc.mark_synced_batch([id1, id2])
        pending = svc.get_pending()
        assert len(pending) == 0

    def test_mark_synced_batch_empty(self, fresh_db, seed_data):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        svc.mark_synced_batch([])


class TestSyncServiceMarkConflict:
    def test_mark_conflict(self, fresh_db, seed_data):
        from lab_system.app.sync.service import SyncService, SYNC_STATUS_CONFLICT
        svc = SyncService()
        entry_id = svc.enqueue("receipts", 1, "create", "")
        svc.mark_conflict(entry_id, "server conflict")
        pending = svc.get_pending()
        assert len(pending) == 0
        stats = svc.get_stats()
        assert stats.get(SYNC_STATUS_CONFLICT, 0) == 1


class TestSyncServiceRetry:
    def test_increment_retry(self, fresh_db, seed_data):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        entry_id = svc.enqueue("receipts", 1, "create", "")
        count = svc.increment_retry(entry_id)
        assert count == 1
        count = svc.increment_retry(entry_id)
        assert count == 2


class TestSyncServiceClearSynced:
    def test_clear_synced(self, fresh_db, seed_data):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        entry_id = svc.enqueue("receipts", 1, "create", "")
        svc.mark_synced(entry_id)
        import time
        time.sleep(1.5)
        cleared = svc.clear_synced(older_than_seconds=0)
        assert cleared >= 1


class TestSyncServiceStats:
    def test_empty_stats(self, fresh_db, seed_data):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        stats = svc.get_stats()
        assert stats == {}

    def test_stats_with_entries(self, fresh_db, seed_data):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        svc.enqueue("receipts", 1, "create", "")
        svc.enqueue("receipts", 2, "update", "")
        stats = svc.get_stats()
        assert stats.get("pending", 0) == 2


class TestSyncServiceConflictResolution:
    def test_server_wins(self, fresh_db, seed_data):
        from lab_system.app.sync.service import SyncService, SyncQueueEntry
        svc = SyncService()
        entry = SyncQueueEntry(entity_type="receipts", entity_id=1, action="create")
        remote = {"updated_at": "2026-06-25 12:00:00"}
        local = {"updated_at": "2026-06-25 10:00:00"}
        resolution = svc.resolve_conflict(entry, remote, local)
        assert resolution.strategy == "server-wins"
        assert resolution.resolved is True
        assert resolution.merged == remote

    def test_last_writer_wins(self, fresh_db, seed_data):
        from lab_system.app.sync.service import SyncService, SyncQueueEntry
        svc = SyncService()
        entry = SyncQueueEntry(entity_type="receipts", entity_id=1, action="create")
        remote = {"updated_at": "2026-06-25 10:00:00"}
        local = {"updated_at": "2026-06-25 12:00:00"}
        resolution = svc.resolve_conflict(entry, remote, local)
        assert resolution.strategy == "last-writer-wins"
        assert resolution.resolved is True
        assert resolution.merged == local


class TestSyncServiceHealth:
    def test_health_when_empty(self, fresh_db, seed_data):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        health = svc.get_health()
        assert health["enabled"] is False
        assert health["pending"] == 0
        assert health["conflicts"] == 0
        assert health["healthy"] is True

    def test_health_with_pending(self, fresh_db, seed_data):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        svc.enqueue("receipts", 1, "create", "")
        health = svc.get_health()
        assert health["pending"] == 1
        assert health["healthy"] is False


class TestSyncServiceOnline:
    def test_sync_all_offline(self, fresh_db, seed_data):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        result = svc.sync_all()
        assert "error" in result

    def test_sync_pending_offline(self, fresh_db, seed_data):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        result = svc.sync_pending()
        assert "error" in result

    def test_push_entity_offline(self, fresh_db, seed_data):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        result = svc.push_entity("receipts", 1, "create")
        assert result["status"] == "pending"
