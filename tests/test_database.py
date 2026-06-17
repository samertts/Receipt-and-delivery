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
        def do_stuff(user=None):
            return "done"

        result = do_stuff(user={"role": "Admin"})
        assert result == "done"

    def test_with_permission_decorator_denies(self):
        from lab_system.app.auth.permissions import with_permission
        from lab_system.app.utils.errors import AuthorizationError
        import pytest

        @with_permission("settings.update")
        def do_stuff(user=None):
            return "done"

        with pytest.raises(AuthorizationError):
            do_stuff(user={"role": "Auditor"})

    def test_with_permission_no_user_passes_through(self):
        """When no user kwarg is provided, the decorator should pass through."""
        from lab_system.app.auth.permissions import with_permission

        @with_permission("settings.update")
        def do_stuff(x, y, user=None):
            return x + y

        # No user kwarg — should pass through without raising
        result = do_stuff(1, 2)
        assert result == 3


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


class TestMigration:
    def setup_method(self):
        import tempfile
        self.tmp = Path(tempfile.mkdtemp(prefix="lab_mig_"))
        self.db_path = self.tmp / "test.db"

    def _make_empty_db(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
        """)
        conn.commit()
        conn.close()

    def _make_conn(self):
        c = sqlite3.connect(str(self.db_path))
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys = ON;")
        return c

    def test_table_columns(self):
        from lab_system.app.database.db import SCHEMA, _table_columns
        conn = self._make_conn()
        conn.executescript(SCHEMA)
        cols = _table_columns(conn, "receipts")
        assert "id" in cols
        assert "receipt_no" in cols
        assert "sender_name" in cols
        conn.close()

    def test_migrate_from_scratch(self):
        from lab_system.app.database.db import SCHEMA, migrate_db
        conn = self._make_conn()
        conn.executescript(SCHEMA.replace("INSERT INTO meta(key,value) VALUES('schema_version','9')",
                                          "INSERT INTO meta(key,value) VALUES('schema_version','0')"))
        conn.commit()
        migrate_db(conn)
        row = conn.execute("SELECT count(*) FROM migration_history").fetchone()
        assert row[0] > 0, "migrate_db should record at least one migration entry"
        conn.close()

    def test_migration_lock_acquire_release(self):
        from lab_system.app.database.db import SCHEMA, _acquire_migration_lock, _release_migration_lock
        conn = self._make_conn()
        conn.executescript(SCHEMA)
        _acquire_migration_lock(conn)
        row = conn.execute("SELECT is_locked FROM migration_lock WHERE id=1").fetchone()
        assert int(row[0]) == 1
        _release_migration_lock(conn)
        row = conn.execute("SELECT is_locked FROM migration_lock WHERE id=1").fetchone()
        assert int(row[0]) == 0
        conn.close()

    def test_migration_lock_double_acquire_raises(self):
        from lab_system.app.database.db import SCHEMA, _acquire_migration_lock
        conn = self._make_conn()
        conn.executescript(SCHEMA)
        _acquire_migration_lock(conn)
        import pytest
        with pytest.raises(RuntimeError):
            _acquire_migration_lock(conn)
        conn.close()

    def test_v9_index_exists(self):
        from lab_system.app.database.db import SCHEMA, migrate_db
        conn = self._make_conn()
        conn.executescript(SCHEMA)
        conn.commit()
        migrate_db(conn)
        indexes = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_receipt_items_receipt_id'"
        ).fetchall()
        assert len(indexes) == 1
        conn.close()

    def test_default_settings_populated(self):
        from lab_system.app.database.db import SCHEMA, init_db, DEFAULT_SETTINGS
        import lab_system.app.database.db as db_mod
        import lab_system.app.settings.config as cfg_mod
        self._orig_config = db_mod.CONFIG
        new_config = cfg_mod.AppConfig(
            base_dir=cfg_mod.BASE_DIR,
            app_dir=cfg_mod.ROOT_DIR,
            storage_dir=cfg_mod.ROOT_DIR,
            assets_dir=cfg_mod.ROOT_DIR / "assets",
            db_path=self.db_path,
            app_name=cfg_mod.APP_NAME,
            version_file=cfg_mod.ROOT_DIR / "VERSION",
            app_version=cfg_mod._read_app_version(cfg_mod.ROOT_DIR / "VERSION"),
        )
        db_mod.CONFIG = new_config
        cfg_mod.CONFIG = new_config

        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(SCHEMA)
        conn.close()

        init_db()

        c = sqlite3.connect(str(self.db_path))
        c.row_factory = sqlite3.Row
        rows = c.execute("SELECT COUNT(*) c FROM settings").fetchone()
        assert rows["c"] == len(DEFAULT_SETTINGS)
        row = c.execute("SELECT value FROM settings WHERE key='receipt.numbering_prefix'").fetchone()
        assert row is not None
        assert row["value"] == "LAB"
        c.close()

        db_mod.CONFIG = self._orig_config
        cfg_mod.CONFIG = self._orig_config

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)
