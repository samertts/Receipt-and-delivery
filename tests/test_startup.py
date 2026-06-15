import os
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _setup_env():
    tmp = Path(tempfile.mkdtemp(prefix="lab_diag_"))
    db_path = tmp / "database" / "test.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);")
    conn.execute("INSERT INTO meta VALUES('k','v')")
    conn.commit()
    conn.close()
    return tmp, db_path


def _patch_config(tmp, db_path):
    import lab_system.app.settings.config as cfg_mod
    import lab_system.app.diagnostics.startup as diag_mod
    orig_cfg = cfg_mod.CONFIG
    orig_storage = cfg_mod.STORAGE_DIR
    new_cfg = cfg_mod.AppConfig(
        base_dir=cfg_mod.BASE_DIR,
        app_dir=cfg_mod.ROOT_DIR,
        storage_dir=tmp,
        assets_dir=cfg_mod.ROOT_DIR / "assets",
        db_path=db_path,
        app_name=cfg_mod.APP_NAME,
        version_file=cfg_mod.ROOT_DIR / "VERSION",
        app_version=cfg_mod._read_app_version(cfg_mod.ROOT_DIR / "VERSION"),
    )
    cfg_mod.CONFIG = new_cfg
    diag_mod.CONFIG = new_cfg
    return cfg_mod, orig_cfg, orig_storage


def _restore_config(cfg_mod, orig_cfg, orig_storage):
    import lab_system.app.diagnostics.startup as diag_mod
    cfg_mod.CONFIG = orig_cfg
    cfg_mod.STORAGE_DIR = orig_storage
    diag_mod.CONFIG = orig_cfg


class TestStartupDiagnostics:
    def setup_method(self):
        self.tmp, self.db_path = _setup_env()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _with_env(self):
        return _patch_config(self.tmp, self.db_path)

    def test_check_indexes_db_not_found(self):
        cfg_mod, orig_cfg, orig_storage = self._with_env()
        try:
            from lab_system.app.diagnostics.startup import check_indexes
            dummy = self.tmp / "nonexistent.db"
            import lab_system.app.diagnostics.startup as diag_mod
            new_cfg = cfg_mod.AppConfig(
                base_dir=cfg_mod.CONFIG.base_dir,
                app_dir=cfg_mod.CONFIG.app_dir,
                storage_dir=self.tmp,
                assets_dir=cfg_mod.CONFIG.assets_dir,
                db_path=dummy,
                app_name=cfg_mod.CONFIG.app_name,
                version_file=cfg_mod.CONFIG.version_file,
                app_version=cfg_mod.CONFIG.app_version,
            )
            cfg_mod.CONFIG = new_cfg
            diag_mod.CONFIG = new_cfg
            result = check_indexes()
            assert result["ok"] is False
            assert "Database does not exist" in str(result["errors"])
        finally:
            _restore_config(cfg_mod, orig_cfg, orig_storage)

    def test_check_indexes_with_db(self):
        cfg_mod, orig_cfg, orig_storage = self._with_env()
        try:
            from lab_system.app.diagnostics.startup import check_indexes
            result = check_indexes()
            assert "ok" in result
            assert "present" in result
        finally:
            _restore_config(cfg_mod, orig_cfg, orig_storage)

    def test_check_indexes_error(self):
        cfg_mod, orig_cfg, orig_storage = self._with_env()
        try:
            from lab_system.app.diagnostics.startup import check_indexes
            import lab_system.app.diagnostics.startup as diag_mod
            dummy = Path("/nonexistent_dir_xyz_abc123/db.db")
            new_cfg = cfg_mod.AppConfig(
                base_dir=cfg_mod.CONFIG.base_dir,
                app_dir=cfg_mod.CONFIG.app_dir,
                storage_dir=self.tmp,
                assets_dir=cfg_mod.CONFIG.assets_dir,
                db_path=dummy,
                app_name=cfg_mod.CONFIG.app_name,
                version_file=cfg_mod.CONFIG.version_file,
                app_version=cfg_mod.CONFIG.app_version,
            )
            cfg_mod.CONFIG = new_cfg
            diag_mod.CONFIG = new_cfg
            result = check_indexes()
            assert result["ok"] is False
        finally:
            _restore_config(cfg_mod, orig_cfg, orig_storage)

    def test_check_integrity_ok(self):
        cfg_mod, orig_cfg, orig_storage = self._with_env()
        try:
            from lab_system.app.diagnostics.startup import check_integrity
            result = check_integrity()
            assert result["db_ok"] is True
            assert result["wal_ok"] is True
        finally:
            _restore_config(cfg_mod, orig_cfg, orig_storage)

    def test_check_integrity_db_missing(self):
        cfg_mod, orig_cfg, orig_storage = self._with_env()
        try:
            from lab_system.app.diagnostics.startup import check_integrity
            dummy = self.tmp / "nope.db"
            import lab_system.app.diagnostics.startup as diag_mod
            diag_mod.CONFIG = cfg_mod.AppConfig(
                base_dir=cfg_mod.CONFIG.base_dir,
                app_dir=cfg_mod.CONFIG.app_dir,
                storage_dir=cfg_mod.CONFIG.storage_dir,
                assets_dir=cfg_mod.CONFIG.assets_dir,
                db_path=dummy,
                app_name=cfg_mod.CONFIG.app_name,
                version_file=cfg_mod.CONFIG.version_file,
                app_version=cfg_mod.CONFIG.app_version,
            )
            result = check_integrity()
            assert result["db_ok"] is False
        finally:
            _restore_config(cfg_mod, orig_cfg, orig_storage)

    def test_check_folders_creates_missing(self):
        cfg_mod, orig_cfg, orig_storage = self._with_env()
        try:
            from lab_system.app.diagnostics.startup import check_folders
            result = check_folders()
            assert "created" in result
            assert "missing" in result
        finally:
            _restore_config(cfg_mod, orig_cfg, orig_storage)

    def test_check_folders_all_exist(self):
        cfg_mod, orig_cfg, orig_storage = self._with_env()
        try:
            from lab_system.app.diagnostics.startup import check_folders
            check_folders()
            result = check_folders()
            assert len(result["created"]) == 0
        finally:
            _restore_config(cfg_mod, orig_cfg, orig_storage)

    def test_check_network_unreachable(self):
        import unittest.mock as mock
        with mock.patch('urllib.request.urlopen', side_effect=OSError("no route to host")):
            from lab_system.app.diagnostics.startup import check_network
            result = check_network(host="http://192.0.2.1", timeout=1)
            assert result["reachable"] is False
            assert "error" in result

    def test_check_config(self):
        cfg_mod, orig_cfg, orig_storage = self._with_env()
        try:
            from lab_system.app.diagnostics.startup import check_config
            result = check_config()
            assert "version" in result
            assert "issues" in result
        finally:
            _restore_config(cfg_mod, orig_cfg, orig_storage)

    def test_run_all_checks(self):
        cfg_mod, orig_cfg, orig_storage = self._with_env()
        try:
            from lab_system.app.diagnostics.startup import run_all_checks
            result = run_all_checks()
            assert "timestamp" in result
            assert "integrity" in result
            assert "indexes" in result
            assert "folders" in result
            assert "config" in result
            assert "network" in result
            assert "all_ok" in result
        finally:
            _restore_config(cfg_mod, orig_cfg, orig_storage)

    def test_self_repair(self):
        cfg_mod, orig_cfg, orig_storage = self._with_env()
        try:
            from lab_system.app.diagnostics.startup import self_repair
            actions = self_repair()
            assert isinstance(actions, list)
        finally:
            _restore_config(cfg_mod, orig_cfg, orig_storage)

    def test_diagnose_and_report(self):
        cfg_mod, orig_cfg, orig_storage = self._with_env()
        try:
            from lab_system.app.diagnostics.startup import diagnose_and_report
            report = diagnose_and_report()
            assert "Startup Diagnostics" in report
            assert "Database" in report
            assert "Indexes" in report
            assert "Folders" in report
            assert "Configuration" in report
        finally:
            _restore_config(cfg_mod, orig_cfg, orig_storage)
