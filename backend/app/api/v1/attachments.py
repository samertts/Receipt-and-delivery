from __future__ import annotations

import hashlib
import os
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.config import settings
from app.db.session import get_db
from app.models.attachment import Attachment
from app.models.transaction import Transaction
from app.models.user import User

router = APIRouter(prefix="/attachments", tags=["المرفقات"])

UPLOAD_DIR = (Path(settings.storage_root) / "uploads" / "attachments").resolve()
MAX_FILE_SIZE = 50 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024
ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}
MAGIC_BYTES = {
    b"\x25\x50\x44\x46": "application/pdf",
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89\x50\x4e\x47": "image/png",
}


def _detect_content_type(header: bytes) -> str | None:
    for magic, mime in MAGIC_BYTES.items():
        if header.startswith(magic):
            return mime
    return None


async def _save_upload_to_disk(file: UploadFile) -> tuple[Path, int, str, str]:
    """Stream an upload to a private temporary file before validating and renaming it."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    digest = hashlib.sha256()
    header = b""
    size = 0
    fd, temporary_name = tempfile.mkstemp(prefix="upload-", suffix=".tmp", dir=UPLOAD_DIR)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            while chunk := await file.read(CHUNK_SIZE):
                if not header:
                    header = chunk[:8]
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise HTTPException(status_code=400, detail="حجم الملف يتجاوز 50 ميغابايت")
                digest.update(chunk)
                stream.write(chunk)
            stream.flush()
            os.fsync(stream.fileno())

        actual_type = _detect_content_type(header)
        if file.content_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=400, detail="نوع الملف غير مدعوم")
        if actual_type is None:
            raise HTTPException(status_code=400, detail="محتوى الملف لا يتطابق مع النوع المعلن")
        if actual_type != file.content_type:
            raise HTTPException(status_code=400, detail="نوع الملف غير متطابق")

        storage_name = f"{uuid.uuid4()}{ALLOWED_TYPES[actual_type]}"
        target = (UPLOAD_DIR / storage_name).resolve()
        if not target.is_relative_to(UPLOAD_DIR):
            raise HTTPException(status_code=400, detail="مسار الملف غير صالح")
        os.replace(temporary_path, target)
        temporary_path = None
        return target, size, digest.hexdigest(), storage_name
    finally:
        if temporary_path:
            temporary_path.unlink(missing_ok=True)


@router.post("/upload")
async def upload_attachment(
    transaction_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("create_transaction")),
    db: Session = Depends(get_db),
):
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="المعاملة غير موجودة")

    target, size, sha256_hash, storage_name = await _save_upload_to_disk(file)
    try:
        attachment = Attachment(
            transaction_id=transaction_id,
            original_name=file.filename or storage_name,
            storage_name=storage_name,
            content_type=file.content_type or "application/octet-stream",
            sha256_hash=sha256_hash,
            size_bytes=size,
            path=str(target),
        )
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
    except Exception:
        target.unlink(missing_ok=True)
        db.rollback()
        raise

    return {
        "id": str(attachment.id),
        "original_name": attachment.original_name,
        "size_bytes": attachment.size_bytes,
        "content_type": attachment.content_type,
    }


@router.get("/{attachment_id}/download")
async def download_attachment(
    attachment_id: str,
    current_user: User = Depends(require_permission("view_transactions")),
    db: Session = Depends(get_db),
):
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="المرفق غير موجود")

    resolved_path = Path(attachment.path).resolve()
    if not resolved_path.is_relative_to(UPLOAD_DIR):
        raise HTTPException(status_code=403, detail="مرفوض")
    if not resolved_path.is_file():
        raise HTTPException(status_code=404, detail="ملف المرفق غير موجود")

    from fastapi.responses import FileResponse

    return FileResponse(
        path=str(resolved_path),
        filename=attachment.original_name or attachment.storage_name,
        media_type=attachment.content_type,
    )
