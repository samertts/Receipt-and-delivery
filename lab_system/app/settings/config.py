from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
STORAGE_DIR = BASE_DIR / 'storage'
DB_PATH = BASE_DIR.parent / 'lab_system.db'
APP_NAME = 'نظام إدارة الاستلام المختبري'

for folder in ['receipts', 'attachments', 'exports', 'backups', 'temp']:
    (STORAGE_DIR / folder).mkdir(parents=True, exist_ok=True)
