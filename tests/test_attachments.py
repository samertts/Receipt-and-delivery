import os
import sqlite3
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _setup():
    from lab_system.app.database.db import SCHEMA
    tmp = Path(tempfile.mkdtemp(prefix="lab_att_"))
    db_path = tmp / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA)
    conn.execute(
        "INSERT INTO organizations(name,code,org_type,status) VALUES('Org','O-01','Lab','Active')"
    )
    conn.execute(
        "INSERT INTO users(full_name,username,password_hash,role,status) VALUES('A','a','h','Admin','Active')"
    )
    conn.execute(
        "INSERT INTO transaction_types(name,is_active) VALUES('Sample Receipt',1)"
    )
    conn.execute(
        "INSERT INTO sample_types(name,category,status) VALUES('Serum','Blood','Active')"
    )
    conn.execute("""
        INSERT INTO receipts(receipt_no,tx_type_id,sender_org_id,receiver_org_id,
            sender_name,receiver_name,created_at,status,created_by)
        VALUES('LAB-2026-000001',1,1,1,'Sender','Receiver',
               datetime('now'),'Draft',1)
    """)
    conn.commit()
    conn.close()

    storage_dir = tmp / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    (storage_dir / "attachments").mkdir(parents=True, exist_ok=True)

    @contextmanager
    def test_conn():
        c = sqlite3.connect(str(db_path))
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys = ON;")
        try:
            yield c
            c.commit()
        finally:
            c.close()

    import lab_system.app.database.db as db_mod
    import lab_system.app.attachments.manager as att_mod
    db_mod.get_conn = test_conn
    att_mod.STORAGE_DIR = storage_dir
    return tmp


_call_count = 0


def _make_pdf(path: Path):
    global _call_count
    _call_count += 1
    path.write_bytes(f"%PDF-1.4 fake pdf content {_call_count}".encode())


def _make_png(path: Path):
    from PIL import Image
    img = Image.new("RGB", (10, 10), color="red")
    img.save(path, format="PNG")


def _make_jpg(path: Path):
    path.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 20)


class TestAttachmentsUtils:
    @classmethod
    def setup_class(cls):
        cls.tmp = _setup()

    def test_sanitize_ascii(self):
        from lab_system.app.attachments.manager import _sanitize_filename
        assert _sanitize_filename("hello.pdf") == "hello.pdf"

    def test_sanitize_arabic(self):
        from lab_system.app.attachments.manager import _sanitize_filename
        assert "تقرير.pdf" in _sanitize_filename("تقرير.pdf")

    def test_sanitize_path_traversal(self):
        from lab_system.app.attachments.manager import _sanitize_filename
        result = _sanitize_filename("../../etc/passwd")
        assert ".." not in result or result.count(".") <= 1

    def test_sanitize_long_name(self):
        from lab_system.app.attachments.manager import _sanitize_filename
        long_name = "a" * 200 + ".pdf"
        result = _sanitize_filename(long_name)
        assert len(result) <= 128

    def test_check_magic_pdf(self):
        from lab_system.app.attachments.manager import _check_magic_bytes
        f = self.tmp / "test.pdf"
        _make_pdf(f)
        assert _check_magic_bytes(f) == ".pdf"

    def test_check_magic_png(self):
        from lab_system.app.attachments.manager import _check_magic_bytes
        f = self.tmp / "test.png"
        _make_png(f)
        assert _check_magic_bytes(f) == ".png"

    def test_check_magic_jpg(self):
        from lab_system.app.attachments.manager import _check_magic_bytes
        f = self.tmp / "test.jpg"
        _make_jpg(f)
        assert _check_magic_bytes(f) == ".jpg"

    def test_check_magic_invalid(self):
        from lab_system.app.attachments.manager import _check_magic_bytes
        f = self.tmp / "test.bin"
        f.write_bytes(b"\x00\x00\x00\x00")
        assert _check_magic_bytes(f) is None

    def test_check_magic_nonexistent(self):
        from lab_system.app.attachments.manager import _check_magic_bytes
        assert _check_magic_bytes(self.tmp / "nope") is None

    def test_compute_hash(self):
        from lab_system.app.attachments.manager import _compute_hash
        f = self.tmp / "hash_me.txt"
        f.write_text("hello")
        assert _compute_hash(f) == _compute_hash(f)

    def test_compute_hash_length(self):
        from lab_system.app.attachments.manager import _compute_hash
        f = self.tmp / "len_test.txt"
        f.write_text("test")
        assert len(_compute_hash(f)) == 64

    def test_save_attachment_file_not_found(self):
        from lab_system.app.attachments.manager import save_attachment
        import pytest
        with pytest.raises(ValueError, match="الملف غير موجود"):
            save_attachment(1, str(self.tmp / "nope"), "receipt")

    def test_save_attachment_oversized(self):
        from lab_system.app.attachments.manager import save_attachment, MAX_FILE_SIZE
        import pytest
        f = self.tmp / "big.pdf"
        _make_pdf(f)
        f.write_bytes(b"X" * (MAX_FILE_SIZE + 1))
        with pytest.raises(ValueError, match="حجم الملف"):
            save_attachment(1, str(f), "receipt")

    def test_save_attachment_bad_magic(self):
        from lab_system.app.attachments.manager import save_attachment
        import pytest
        f = self.tmp / "fake.pdf"
        f.write_text("not a real pdf")
        with pytest.raises(ValueError, match="غير مدعوم"):
            save_attachment(1, str(f), "receipt")

    def test_save_attachment_success_pdf(self):
        from lab_system.app.attachments.manager import save_attachment
        f = self.tmp / "good.pdf"
        _make_pdf(f)
        path, h = save_attachment(1, str(f), "receipt")
        assert Path(path).exists()
        assert len(h) == 64

    def test_save_attachment_duplicate(self):
        from lab_system.app.attachments.manager import save_attachment
        import pytest
        f = self.tmp / "dup_test.pdf"
        f.write_bytes(b"%PDF-1.4 unique content for dup test")
        save_attachment(1, str(f), "receipt")
        with pytest.raises(ValueError, match="موجود مسبقاً"):
            save_attachment(1, str(f), "receipt")

    def test_round_trip_pdf(self):
        from lab_system.app.attachments.manager import save_attachment
        f = self.tmp / "rt.pdf"
        _make_pdf(f)
        path, h = save_attachment(1, str(f), "receipt")
        assert Path(path).exists()
        assert len(h) == 64
        from lab_system.app.database import db as _db
        with _db.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM attachments WHERE file_hash=?", (h,)
            ).fetchone()
        assert row is not None
        assert row["receipt_id"] == 1
        assert row["file_type"] == ".pdf"

    def test_round_trip_png(self):
        from lab_system.app.attachments.manager import save_attachment
        f = self.tmp / "rt.png"
        _make_png(f)
        path, h = save_attachment(1, str(f), "receipt_attachment")
        assert Path(path).exists()
        assert len(h) == 64
        from lab_system.app.database import db as _db
        with _db.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM attachments ORDER BY id DESC LIMIT 1"
            ).fetchone()
        assert row is not None
        assert row["category"] == "receipt_attachment"
