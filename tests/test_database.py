import os
import sqlite3
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _get_test_db_path():
    from lab_system.app.database.db import SCHEMA
    db_path = Path(tempfile.mkdtemp(prefix="lab_db_")) / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    return db_path


class TestConnectionScope:
    def setup_method(self):
        self.db_path = _get_test_db_path()
        import lab_system.app.database.db as db_mod

        @contextmanager
        def test_conn():
            c = sqlite3.connect(str(self.db_path))
            c.row_factory = sqlite3.Row
            c.execute("PRAGMA foreign_keys = ON;")
            try:
                yield c
                c.commit()
            finally:
                c.close()

        self._orig = db_mod.get_conn
        db_mod.get_conn = test_conn

    def teardown_method(self):
        import lab_system.app.database.db as db_mod
        db_mod.get_conn = self._orig

    def test_connection_scope_yields_conn(self):
        from lab_system.app.database.connection import connection_scope
        with connection_scope() as conn:
            row = conn.execute("SELECT 1 AS v").fetchone()
            assert row["v"] == 1

    def test_connection_scope_commits(self):
        from lab_system.app.database.connection import connection_scope
        with connection_scope() as conn:
            conn.execute("INSERT INTO meta(key,value) VALUES('test_commit','ok')")
        with connection_scope() as conn:
            row = conn.execute("SELECT value FROM meta WHERE key='test_commit'").fetchone()
            assert row is not None
            assert row["value"] == "ok"


class TestBaseRepository:
    def setup_method(self):
        self.db_path = _get_test_db_path()
        import lab_system.app.database.db as db_mod

        @contextmanager
        def test_conn():
            c = sqlite3.connect(str(self.db_path))
            c.row_factory = sqlite3.Row
            c.execute("PRAGMA foreign_keys = ON;")
            try:
                yield c
                c.commit()
            finally:
                c.close()

        self._orig = db_mod.get_conn
        db_mod.get_conn = test_conn

    def teardown_method(self):
        import lab_system.app.database.db as db_mod
        db_mod.get_conn = self._orig

    def test_fetch_one(self):
        from lab_system.app.database.repository import BaseRepository
        repo = BaseRepository()
        row = repo.fetch_one("SELECT 42 AS val")
        assert row["val"] == 42

    def test_fetch_all(self):
        from lab_system.app.database.repository import BaseRepository
        repo = BaseRepository()
        rows = repo.fetch_all("SELECT 1 AS n UNION ALL SELECT 2")
        assert len(rows) == 2

    def test_execute(self):
        from lab_system.app.database.repository import BaseRepository
        repo = BaseRepository()
        repo.execute("INSERT INTO meta(key,value) VALUES(?,?)", ("repo_test", "works"))
        row = repo.fetch_one("SELECT value FROM meta WHERE key='repo_test'")
        assert row["value"] == "works"


class TestPermissions:
    def setup_method(self):
        self.db_path = _get_test_db_path()
        import lab_system.app.database.db as db_mod

        @contextmanager
        def test_conn():
            c = sqlite3.connect(str(self.db_path))
            c.row_factory = sqlite3.Row
            c.execute("PRAGMA foreign_keys = ON;")
            try:
                yield c
                c.commit()
            finally:
                c.close()

        self._orig = db_mod.get_conn
        db_mod.get_conn = test_conn

    def teardown_method(self):
        import lab_system.app.database.db as db_mod
        db_mod.get_conn = self._orig

    def test_require_permission_allows_admin(self):
        from lab_system.app.auth.permissions import require_permission
        require_permission("Admin", "receipts.create")

    def test_require_permission_denies_user(self):
        from lab_system.app.auth.permissions import require_permission
        from lab_system.app.utils.errors import AuthorizationError
        import pytest
        with pytest.raises(AuthorizationError):
            require_permission("User", "receipts.delete")

    def test_check_permission_passes(self):
        from lab_system.app.auth.permissions import check_permission
        check_permission({"role": "Supervisor"}, "receipts.approve")

    def test_check_permission_raises(self):
        from lab_system.app.auth.permissions import check_permission
        from lab_system.app.utils.errors import AuthorizationError
        import pytest
        with pytest.raises(AuthorizationError):
            check_permission({"role": "Auditor"}, "receipts.create")

    def test_with_permission_decorator_allows(self):
        from lab_system.app.auth.permissions import with_permission

        @with_permission("settings.read")
        def do_stuff(user):
            return "done"

        result = do_stuff({"role": "Admin"})
        assert result == "done"

    def test_with_permission_decorator_denies(self):
        from lab_system.app.auth.permissions import with_permission
        from lab_system.app.utils.errors import AuthorizationError
        import pytest

        @with_permission("settings.update")
        def do_stuff(user):
            return "done"

        with pytest.raises(AuthorizationError):
            do_stuff({"role": "Auditor"})


class TestCatalogService:
    def setup_method(self):
        self.db_path = _get_test_db_path()
        import lab_system.app.database.db as db_mod

        @contextmanager
        def test_conn():
            c = sqlite3.connect(str(self.db_path))
            c.row_factory = sqlite3.Row
            c.execute("PRAGMA foreign_keys = ON;")
            try:
                yield c
                c.commit()
            finally:
                c.close()

        self._orig = db_mod.get_conn
        db_mod.get_conn = test_conn

    def teardown_method(self):
        import lab_system.app.database.db as db_mod
        db_mod.get_conn = self._orig

    def test_seed_defaults_inserts_data(self):
        from lab_system.app.services.catalog_service import seed_defaults
        seed_defaults()
        from lab_system.app.database.connection import connection_scope
        with connection_scope() as conn:
            tx_count = conn.execute("SELECT COUNT(*) c FROM transaction_types").fetchone()["c"]
            sm_count = conn.execute("SELECT COUNT(*) c FROM sample_types").fetchone()["c"]
        assert tx_count == 4
        assert sm_count == 8

    def test_seed_defaults_idempotent(self):
        from lab_system.app.services.catalog_service import seed_defaults
        seed_defaults()
        seed_defaults()
        from lab_system.app.database.connection import connection_scope
        with connection_scope() as conn:
            tx_count = conn.execute("SELECT COUNT(*) c FROM transaction_types").fetchone()["c"]
        assert tx_count == 4

    def test_list_transaction_types(self):
        from lab_system.app.services.catalog_service import seed_defaults, list_transaction_types
        seed_defaults()
        items = list_transaction_types()
        assert len(items) == 4
        assert items[0]["is_active"] == 1

    def test_list_sample_types(self):
        from lab_system.app.services.catalog_service import seed_defaults, list_sample_types
        seed_defaults()
        items = list_sample_types()
        assert len(items) == 8
