import io
import os
import shutil
import sqlite3
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

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
        conn.execute(
            "DELETE FROM settings WHERE key IN ('sync.device_id','sync.branch_id')"
        )


class TestSyncQueue:
    def test_enqueue_create(self):
        from lab_system.app.sync.service import SyncService

        svc = SyncService()
        eid = svc.enqueue("receipts", 1, "create", '{"test": true}')
        assert eid > 0

    def test_enqueue_update(self):
        from lab_system.app.sync.service import SyncService

        svc = SyncService()
        eid = svc.enqueue("organizations", 5, "update", "{}")
        assert eid > 0

    def test_enqueue_delete(self):
        from lab_system.app.sync.service import SyncService

        svc = SyncService()
        eid = svc.enqueue("users", 3, "delete", "")
        assert eid > 0

    def test_enqueue_invalid_action(self):
        from lab_system.app.sync.service import SyncService

        svc = SyncService()
        with pytest.raises(ValueError):
            svc.enqueue("receipts", 1, "invalid_action", "")

    def test_get_pending_returns_queued(self):
        from lab_system.app.sync.service import SYNC_STATUS_PENDING, SyncService

        svc = SyncService()
        svc.enqueue("receipts", 1, "create", "{}")
        svc.enqueue("receipts", 2, "update", "{}")
        pending = svc.get_pending()
        assert len(pending) == 2
        assert all(e.status == SYNC_STATUS_PENDING for e in pending)

    def test_mark_synced(self):
        from lab_system.app.sync.service import SyncService

        svc = SyncService()
        eid = svc.enqueue("receipts", 1, "create", "{}")
        svc.mark_synced(eid)
        pending = svc.get_pending()
        assert len(pending) == 0

    def test_mark_conflict(self):
        from lab_system.app.database import db as _db
        from lab_system.app.sync.service import SyncService

        svc = SyncService()
        eid = svc.enqueue("receipts", 1, "create", "{}")
        svc.mark_conflict(eid, "server data differs")
        with _db.get_conn() as conn:
            row = conn.execute(
                "SELECT status, payload FROM sync_queue WHERE id=?", (eid,)
            ).fetchone()
        assert row["status"] == "conflict"
        assert row["payload"] == "server data differs"

    def test_increment_retry(self):
        from lab_system.app.sync.service import SyncService

        svc = SyncService()
        eid = svc.enqueue("receipts", 1, "create", "{}")
        assert svc.increment_retry(eid) == 1
        assert svc.increment_retry(eid) == 2

    def test_clear_synced_noop_when_none_synced(self):
        from lab_system.app.sync.service import SyncService

        svc = SyncService()
        svc.enqueue("receipts", 1, "create", "{}")
        cleared = svc.clear_synced(older_than_seconds=1)
        assert cleared == 0

    def test_get_stats(self):
        from lab_system.app.sync.service import (
            SYNC_STATUS_PENDING,
            SYNC_STATUS_SYNCED,
            SyncService,
        )

        svc = SyncService()
        eid = svc.enqueue("receipts", 1, "create", "{}")
        svc.enqueue("organizations", 2, "update", "{}")
        svc.mark_synced(eid)
        stats = svc.get_stats()
        assert stats.get(SYNC_STATUS_SYNCED, 0) == 1
        assert stats.get(SYNC_STATUS_PENDING, 0) == 1

    def test_sync_all_disabled(self):
        from lab_system.app.sync.service import SyncService

        svc = SyncService()
        svc.enqueue("receipts", 1, "create", "{}")
        result = svc.sync_all()
        assert "error" in result

    def test_sync_all_enabled_no_network(self):
        from lab_system.app.sync.service import SyncService

        svc = SyncService()
        svc._client.enable("http://localhost:9999")
        svc.enqueue("receipts", 1, "create", "{}")
        result = svc.sync_all()
        assert result.get("synced", 0) == 0

    def test_push_entity_pending(self):
        from lab_system.app.sync.service import SYNC_STATUS_PENDING, SyncService

        svc = SyncService()
        result = svc.push_entity("receipts", 1, "create", '{"x": 1}')
        assert result["entry_id"] > 0
        # Offline: queued locally, no sync error since no attempt made
        assert result["status"] == SYNC_STATUS_PENDING

    def test_push_entity_online_returns_pending(self):
        from lab_system.app.sync.service import SyncService

        svc = SyncService()
        svc._client.enable("http://localhost:9999")
        result = svc.push_entity("receipts", 1, "create", '{"x": 1}')
        assert result["entry_id"] > 0


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
        from lab_system.app.sync.device import get_branch_id, set_branch_id

        set_branch_id("BAGHDAD-LAB-01")
        assert get_branch_id() == "BAGHDAD-LAB-01"

    def test_branch_id_default_empty(self):
        from lab_system.app.sync.device import get_branch_id

        bid = get_branch_id()
        assert bid == ""


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
        assert "disabled" in resp.message

    def test_pull_when_disabled(self):
        from lab_system.app.sync.api_client import APIClient

        client = APIClient()
        resp = client.pull()
        assert not resp.success

    def test_enable_disable(self):
        from lab_system.app.sync.api_client import APIClient

        client = APIClient()
        client.enable("http://localhost:8000")
        assert client.is_enabled
        client.disable()
        assert not client.is_enabled

    def test_send_not_implemented(self):
        from lab_system.app.sync.api_client import APIClient

        client = APIClient()
        client.enable("http://localhost:8000")
        resp = client._send("GET", "/test", {})
        assert resp.status_code in (0, 501)


class TestAPIClientAdvanced:
    """Mock-based tests covering _send internals."""

    def test_set_token(self):
        from lab_system.app.sync.api_client import APIClient

        client = APIClient()
        client.set_token("my-token")
        assert client._token == "my-token"

    def test_status_when_disabled(self):
        from lab_system.app.sync.api_client import APIClient

        client = APIClient()
        resp = client.status()
        assert not resp.success

    def test_send_success(self, monkeypatch):
        import json
        from lab_system.app.sync.api_client import APIClient

        client = APIClient()
        client.enable("http://example.com", token="test-token")

        class FakeResp:
            status = 200

            def read(self):
                return json.dumps({"ok": True}).encode()

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

        monkeypatch.setattr(
            "urllib.request.urlopen", lambda req, timeout=30: FakeResp()
        )
        resp = client._send("POST", "/sync/push", {"key": "val"})
        assert resp.success
        assert resp.status_code == 200
        assert resp.data == {"ok": True}

    def test_send_http_error(self, monkeypatch):
        import json
        import urllib.error
        from lab_system.app.sync.api_client import APIClient

        client = APIClient()
        client.enable("http://example.com")

        def fake_urlopen(req, timeout=30):
            error = urllib.error.HTTPError(
                url=req.full_url,
                code=409,
                msg="Conflict",
                hdrs={},
                fp=io.BytesIO(json.dumps({"detail": "conflict"}).encode()),
            )
            raise error

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
        resp = client.status()
        assert not resp.success
        assert resp.status_code == 409

    def test_send_http_error_bad_json(self, monkeypatch):
        import urllib.error
        from lab_system.app.sync.api_client import APIClient

        client = APIClient()
        client.enable("http://example.com")

        def fake_urlopen(req, timeout=30):
            error = urllib.error.HTTPError(
                url=req.full_url,
                code=500,
                msg="Server Error",
                hdrs={},
                fp=io.BytesIO(b"not json"),
            )
            raise error

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
        resp = client.status()
        assert not resp.success
        assert resp.status_code == 500
        assert "raw" in resp.data

    def test_send_url_error(self, monkeypatch):
        import urllib.error
        from lab_system.app.sync.api_client import APIClient

        client = APIClient()
        client.enable("http://example.com")

        def fake_urlopen(req, timeout=30):
            raise urllib.error.URLError("Connection refused")

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
        resp = client.status()
        assert not resp.success
        assert resp.status_code == 0

    def test_send_generic_exception(self, monkeypatch):
        from lab_system.app.sync.api_client import APIClient

        client = APIClient()
        client.enable("http://example.com")

        def fake_urlopen(req, timeout=30):
            raise RuntimeError("unexpected crash")

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
        resp = client.status()
        assert not resp.success
        assert resp.status_code == 0

    def test_push_with_token(self, monkeypatch):
        import json
        from lab_system.app.sync.api_client import APIClient, SyncPayload

        client = APIClient()
        client.enable("http://example.com", token="secret")

        class FakeResp:
            status = 200

            def read(self):
                return json.dumps({"synced": True}).encode()

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

        monkeypatch.setattr(
            "urllib.request.urlopen", lambda req, timeout=30: FakeResp()
        )
        payload = SyncPayload(entries=[{"id": 1}], device_id="dev1", branch_id="br1")
        resp = client.push(payload)
        assert resp.success
        assert resp.data == {"synced": True}

    def test_pull_with_params(self, monkeypatch):
        import json
        from lab_system.app.sync.api_client import APIClient

        client = APIClient()
        client.enable("http://example.com")

        class FakeResp:
            status = 200

            def read(self):
                return json.dumps({"entries": []}).encode()

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

        monkeypatch.setattr(
            "urllib.request.urlopen", lambda req, timeout=30: FakeResp()
        )
        resp = client.pull(since="2024-01-01", device_id="dev1")
        assert resp.success
        assert resp.data == {"entries": []}


class TestConflictResolution:
    def test_server_wins_default(self):
        from lab_system.app.sync.service import SyncQueueEntry, SyncService

        svc = SyncService()
        entry = SyncQueueEntry(
            id=1, entity_type="receipts", entity_id=1, action="update"
        )
        remote = {"name": "server-data"}
        local = {"name": "local-data"}
        resolution = svc.resolve_conflict(entry, remote, local)
        assert resolution.resolved
        assert resolution.merged == remote

    def test_last_writer_wins_with_timestamps(self):
        from lab_system.app.sync.service import SyncQueueEntry, SyncService

        svc = SyncService()
        entry = SyncQueueEntry(
            id=1, entity_type="receipts", entity_id=1, action="update"
        )
        remote = {"name": "server", "updated_at": "2024-01-01 00:00:00"}
        local = {"name": "local", "updated_at": "2024-06-01 00:00:00"}
        resolution = svc.resolve_conflict(entry, remote, local)
        assert resolution.resolved
        assert resolution.strategy == "last-writer-wins"
        assert resolution.merged == local

    def test_server_wins_when_local_older(self):
        from lab_system.app.sync.service import SyncQueueEntry, SyncService

        svc = SyncService()
        entry = SyncQueueEntry(
            id=1, entity_type="receipts", entity_id=1, action="update"
        )
        remote = {"name": "server", "updated_at": "2024-06-01 00:00:00"}
        local = {"name": "local", "updated_at": "2024-01-01 00:00:00"}
        resolution = svc.resolve_conflict(entry, remote, local)
        assert resolution.resolved
        assert resolution.strategy == "server-wins"
        assert resolution.merged == remote

    def test_get_health_disabled(self):
        from lab_system.app.sync.service import SyncService

        svc = SyncService()
        health = svc.get_health()
        assert not health["enabled"]
        assert health["healthy"]

    def test_get_health_with_pending(self):
        from lab_system.app.sync.service import SyncService

        svc = SyncService()
        svc.enqueue("receipts", 1, "create", "{}")
        health = svc.get_health()
        assert not health["healthy"]
        assert health["pending"] == 1
