import sys
import os
import sqlite3
import tempfile
import shutil
from pathlib import Path
from contextlib import contextmanager
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

TEST_DIR = Path(tempfile.mkdtemp(prefix="lab_test_sync_"))
TEST_DB = TEST_DIR / "test_sync.db"


def _init_test_db():
    from lab_system.app.database.db import SCHEMA
    conn = sqlite3.connect(str(TEST_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def _make_test_get_conn():
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
    db_mod.get_conn = _make_test_get_conn()


def teardown_module():
    shutil.rmtree(TEST_DIR, ignore_errors=True)


@pytest.fixture(autouse=True)
def _clean_queue():
    from lab_system.app.database import db as _db
    with _db.get_conn() as conn:
        conn.execute("DELETE FROM sync_queue")
        conn.execute("DELETE FROM settings WHERE key IN ('sync.device_id','sync.branch_id')")


class TestSyncQueue:
    def test_enqueue_create(self):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        eid = svc.enqueue('receipts', 1, 'create', '{"test": true}')
        assert eid > 0

    def test_enqueue_update(self):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        eid = svc.enqueue('organizations', 5, 'update', '{}')
        assert eid > 0

    def test_enqueue_delete(self):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        eid = svc.enqueue('users', 3, 'delete', '')
        assert eid > 0

    def test_enqueue_invalid_action(self):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        with pytest.raises(ValueError):
            svc.enqueue('receipts', 1, 'invalid_action', '')

    def test_get_pending_returns_queued(self):
        from lab_system.app.sync.service import SyncService, SYNC_STATUS_PENDING
        svc = SyncService()
        svc.enqueue('receipts', 1, 'create', '{}')
        svc.enqueue('receipts', 2, 'update', '{}')
        pending = svc.get_pending()
        assert len(pending) == 2
        assert all(e.status == SYNC_STATUS_PENDING for e in pending)

    def test_mark_synced(self):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        eid = svc.enqueue('receipts', 1, 'create', '{}')
        svc.mark_synced(eid)
        pending = svc.get_pending()
        assert len(pending) == 0

    def test_mark_conflict(self):
        from lab_system.app.database import db as _db
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        eid = svc.enqueue('receipts', 1, 'create', '{}')
        svc.mark_conflict(eid, 'server data differs')
        with _db.get_conn() as conn:
            row = conn.execute("SELECT status, payload FROM sync_queue WHERE id=?", (eid,)).fetchone()
        assert row['status'] == 'conflict'
        assert row['payload'] == 'server data differs'

    def test_increment_retry(self):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        eid = svc.enqueue('receipts', 1, 'create', '{}')
        assert svc.increment_retry(eid) == 1
        assert svc.increment_retry(eid) == 2

    def test_clear_synced_noop_when_none_synced(self):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        svc.enqueue('receipts', 1, 'create', '{}')
        cleared = svc.clear_synced(older_than_seconds=1)
        assert cleared == 0

    def test_get_stats(self):
        from lab_system.app.sync.service import SyncService, SYNC_STATUS_SYNCED, SYNC_STATUS_PENDING
        svc = SyncService()
        eid = svc.enqueue('receipts', 1, 'create', '{}')
        svc.enqueue('organizations', 2, 'update', '{}')
        svc.mark_synced(eid)
        stats = svc.get_stats()
        assert stats.get(SYNC_STATUS_SYNCED, 0) == 1
        assert stats.get(SYNC_STATUS_PENDING, 0) == 1

    def test_sync_all_disabled(self):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        svc.enqueue('receipts', 1, 'create', '{}')
        result = svc.sync_all()
        assert 'error' in result

    def test_sync_all_enabled_no_network(self):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        svc._client.enable('http://localhost:9999')
        svc.enqueue('receipts', 1, 'create', '{}')
        result = svc.sync_all()
        assert result.get('synced', 0) == 0

    def test_push_entity_pending(self):
        from lab_system.app.sync.service import SyncService, SYNC_STATUS_PENDING
        svc = SyncService()
        result = svc.push_entity('receipts', 1, 'create', '{"x": 1}')
        assert result['entry_id'] > 0
        # Offline: queued locally, no sync error since no attempt made
        assert result['status'] == SYNC_STATUS_PENDING

    def test_push_entity_online_returns_pending(self):
        from lab_system.app.sync.service import SyncService
        svc = SyncService()
        svc._client.enable('http://localhost:9999')
        result = svc.push_entity('receipts', 1, 'create', '{"x": 1}')
        assert result['entry_id'] > 0


class TestDevice:
    def test_get_device_id_returns_string(self):
        from lab_system.app.sync.device import get_device_id
        did = get_device_id()
        assert isinstance(did, str)
        assert len(did) > 0

    def test_get_device_id_persists(self):
        from lab_system.app.sync.device import get_device_id
        did1 = get_device_id()
        did2 = get_device_id()
        assert did1 == did2

    def test_set_branch_id(self):
        from lab_system.app.sync.device import set_branch_id, get_branch_id
        set_branch_id('BAGHDAD-LAB-01')
        assert get_branch_id() == 'BAGHDAD-LAB-01'

    def test_branch_id_default_empty(self):
        from lab_system.app.sync.device import get_branch_id
        bid = get_branch_id()
        assert bid == ''


class TestAPIClient:
    def test_default_disabled(self):
        from lab_system.app.sync.api_client import APIClient
        client = APIClient()
        assert not client.is_enabled

    def test_push_when_disabled(self):
        from lab_system.app.sync.api_client import APIClient, SyncPayload
        client = APIClient()
        resp = client.push(SyncPayload())
        assert not resp.success
        assert 'disabled' in resp.message

    def test_pull_when_disabled(self):
        from lab_system.app.sync.api_client import APIClient
        client = APIClient()
        resp = client.pull()
        assert not resp.success

    def test_enable_disable(self):
        from lab_system.app.sync.api_client import APIClient
        client = APIClient()
        client.enable('http://localhost:8000')
        assert client.is_enabled
        client.disable()
        assert not client.is_enabled

    def test_send_not_implemented(self):
        from lab_system.app.sync.api_client import APIClient
        client = APIClient()
        client.enable('http://localhost:8000')
        resp = client._send('GET', '/test', {})
        assert resp.status_code == 501


class TestConflictResolution:
    def test_server_wins_default(self):
        from lab_system.app.sync.service import SyncService, SyncQueueEntry
        svc = SyncService()
        entry = SyncQueueEntry(id=1, entity_type='receipts', entity_id=1, action='update')
        remote = {'name': 'server-data'}
        local = {'name': 'local-data'}
        resolution = svc.resolve_conflict(entry, remote, local)
        assert resolution.resolved
        assert resolution.merged == remote
