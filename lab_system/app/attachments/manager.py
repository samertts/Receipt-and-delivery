import hashlib
import re
import shutil
from datetime import datetime
from pathlib import Path

from PIL import Image

from lab_system.app.database import db as _db
from lab_system.app.settings.config import STORAGE_DIR

ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png'}

MAGIC_BYTES = {
    b'\x25\x50\x44\x46': '.pdf',
    b'\xff\xd8\xff': '.jpg',
    b'\x89\x50\x4e\x47': '.png',
}

MAX_FILE_SIZE = 50 * 1024 * 1024


def _sanitize_filename(name: str) -> str:
    name = Path(name).name
    name = re.sub(r'[^\w\.\-\u0600-\u06FF ]', '_', name)
    return name[:128]


def _compute_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _check_magic_bytes(path: Path) -> str | None:
    try:
        with open(path, 'rb') as f:
            header = f.read(8)
        for magic, ext in MAGIC_BYTES.items():
            if header.startswith(magic):
                return ext
        return None
    except Exception:
        return None


def save_attachment(receipt_id: int, src_path: str, category: str):
    src = Path(src_path)
    if not src.exists():
        raise ValueError('الملف غير موجود')
    if src.stat().st_size > MAX_FILE_SIZE:
        raise ValueError('حجم الملف يتجاوز 50 ميغابايت')
    detected_ext = _check_magic_bytes(src)
    if detected_ext is None:
        raise ValueError('نوع الملف غير مدعوم أو الملف تالف')
    if detected_ext not in ALLOWED_EXTENSIONS:
        raise ValueError('نوع الملف غير مسموح به')

    src_hash = _compute_hash(src)
    with _db.get_conn() as conn:
        existing = conn.execute(
            "SELECT id, file_path FROM attachments WHERE file_hash=?", (src_hash,),
        ).fetchone()
        if existing:
            raise ValueError(
                f'الملف موجود مسبقاً (مرفق #{existing["id"]})',
            )

    safe_name = _sanitize_filename(src.name)
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    target = STORAGE_DIR / 'attachments' / f'{ts}_{safe_name}'
    target = target.resolve()
    if not str(target).startswith(str(STORAGE_DIR.resolve())):
        raise ValueError('مسار الملف غير صالح')
    if detected_ext in {'.jpg', '.jpeg', '.png'}:
        img = Image.open(src)
        img.thumbnail((1800, 1800))
        img.save(target, optimize=True, quality=80)
    else:
        shutil.copy2(src, target)
    with _db.get_conn() as conn:
        conn.execute(
            'INSERT INTO attachments(receipt_id,file_path,file_type,file_hash,file_size,category,created_at) VALUES(?,?,?,?,?,?,?)',
            (receipt_id, str(target), detected_ext, src_hash, target.stat().st_size, category,
             datetime.now().isoformat(timespec='seconds')),
        )
    return str(target), src_hash
