import hashlib, shutil
from datetime import datetime
from pathlib import Path
from PIL import Image
from lab_system.app.settings.config import STORAGE_DIR
from lab_system.app.database import db as _db

ALLOWED = {'.pdf','.jpg','.jpeg','.png'}

def save_attachment(receipt_id:int, src_path:str, category:str):
    src = Path(src_path)
    if src.suffix.lower() not in ALLOWED:
        raise ValueError('Unsupported file type')
    target = STORAGE_DIR / 'attachments' / f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{src.name}'
    if src.suffix.lower() in {'.jpg','.jpeg','.png'}:
        img=Image.open(src); img.thumbnail((1800,1800)); img.save(target,optimize=True,quality=80)
    else:
        shutil.copy2(src,target)
    h=hashlib.sha256(target.read_bytes()).hexdigest()
    with _db.get_conn() as conn:
        conn.execute('INSERT INTO attachments(receipt_id,file_path,file_type,file_hash,category,created_at) VALUES(?,?,?,?,?,?)',
                     (receipt_id,str(target),target.suffix.lower(),h,category,datetime.now().isoformat(timespec='seconds')))
    return str(target), h
