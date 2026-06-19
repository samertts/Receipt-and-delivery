import hashlib
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.models.attachment import Attachment
from app.models.transaction import Transaction
from app.models.user import User

router = APIRouter(prefix="/attachments", tags=["المرفقات"])

UPLOAD_DIR = "uploads/attachments"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


@router.post("/upload")
async def upload_attachment(
    transaction_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("create_transaction")),
    db: Session = Depends(get_db),
):
    # Validate transaction exists
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="المعاملة غير موجودة")
    
    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="نوع الملف غير مدعوم")
    
    # Read file content
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="حجم الملف يتجاوز 50 ميغابايت")
    
    # Generate unique filename
    file_ext = ALLOWED_TYPES[file.content_type]
    storage_name = f"{uuid.uuid4()}{file_ext}"
    
    # Create upload directory if it doesn't exist
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Save file
    file_path = os.path.join(UPLOAD_DIR, storage_name)
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Compute hash
    sha256_hash = hashlib.sha256(content).hexdigest()
    
    # Create database record
    attachment = Attachment(
        transaction_id=transaction_id,
        original_name=file.filename,
        storage_name=storage_name,
        content_type=file.content_type,
        sha256_hash=sha256_hash,
        size_bytes=len(content),
        path=file_path,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    
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
    
    if not os.path.exists(attachment.path):
        raise HTTPException(status_code=404, detail="ملف المرفق غير موجود")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=attachment.path,
        filename=attachment.original_name,
        media_type=attachment.content_type,
    )
