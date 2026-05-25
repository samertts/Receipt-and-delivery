import shutil
from datetime import datetime
from lab_system.app.settings.config import DB_PATH, STORAGE_DIR
from lab_system.app.database.db import get_conn

def create_backup(user_id=None, notes=''):
    name = f'lab_system_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    target = STORAGE_DIR / 'backups' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DB_PATH, target)
    with get_conn() as conn:
        conn.execute('INSERT INTO backups(backup_file,created_at,created_by,notes) VALUES(?,?,?,?)',
                     (str(target), datetime.now().isoformat(timespec='seconds'), user_id, notes))
    return str(target)
