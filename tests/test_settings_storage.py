import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestStorageManager:
    def test_path_for_creates_dir(self):
        from lab_system.app.settings.storage import StorageManager
        tmp = Path(tempfile.mkdtemp(prefix="lab_stor_"))
        sm = StorageManager()
        orig_base = sm.base
        sm.base = tmp
        path = sm.path_for("test_category")
        assert path.exists()
        assert path.is_dir()
        assert path.name == "test_category"
        assert str(path).startswith(str(tmp))
        sm.base = orig_base

    def test_path_for_twice_returns_same(self):
        from lab_system.app.settings.storage import StorageManager
        tmp = Path(tempfile.mkdtemp(prefix="lab_stor_"))
        sm = StorageManager()
        orig_base = sm.base
        sm.base = tmp
        p1 = sm.path_for("my_stuff")
        p2 = sm.path_for("my_stuff")
        assert p1 == p2
        sm.base = orig_base

    def test_path_for_nested(self):
        from lab_system.app.settings.storage import StorageManager
        tmp = Path(tempfile.mkdtemp(prefix="lab_stor_"))
        sm = StorageManager()
        orig_base = sm.base
        sm.base = tmp
        path = sm.path_for("a/b/c")
        assert path.exists()
        assert path.name == "c"
        sm.base = orig_base

    def test_storage_manager_singleton(self):
        from lab_system.app.settings.storage import storage_manager, StorageManager
        assert isinstance(storage_manager, StorageManager)

    def test_write_and_read_file(self):
        from lab_system.app.settings.storage import StorageManager
        tmp = Path(tempfile.mkdtemp(prefix="lab_stor_"))
        sm = StorageManager()
        orig_base = sm.base
        sm.base = tmp
        folder = sm.path_for("data")
        test_file = folder / "hello.txt"
        test_file.write_text("world")
        assert test_file.read_text() == "world"
        sm.base = orig_base
