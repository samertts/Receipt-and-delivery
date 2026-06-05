import os
from dataclasses import dataclass
from pathlib import Path

from lab_system.app.utils.constants import APP_NAME


@dataclass(frozen=True)
class AppConfig:
    base_dir: Path
    app_dir: Path
    storage_dir: Path
    assets_dir: Path
    db_path: Path
    app_name: str
    version_file: Path
    app_version: str


def _resolve_storage_root(app_name: str) -> Path:
    local_app_data = os.getenv('LOCALAPPDATA')
    if local_app_data:
        return Path(local_app_data) / app_name
    return (Path.home() / 'Documents' / app_name).resolve()


BASE_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = BASE_DIR.parent
STORAGE_ROOT = _resolve_storage_root('LabReceiptSystem')

def _read_app_version(version_file: Path) -> str:
    if version_file.exists():
        return version_file.read_text(encoding='utf-8').strip() or '0.0.0'
    return '0.0.0'


CONFIG = AppConfig(
    base_dir=BASE_DIR,
    app_dir=ROOT_DIR,
    storage_dir=STORAGE_ROOT,
    assets_dir=ROOT_DIR / 'assets',
    db_path=STORAGE_ROOT / 'database' / 'lab_system.db',
    app_name=APP_NAME,
    version_file=ROOT_DIR / 'VERSION',
    app_version=_read_app_version(ROOT_DIR / 'VERSION'),
)

for folder in [
    'database',
    'attachments',
    'logs',
    'backups',
    'exports',
    'settings',
    'templates',
    'recovery',
    'diagnostics',
    'migrations',
    'updates',
    'temp',
    'receipts',
]:
    (CONFIG.storage_dir / folder).mkdir(parents=True, exist_ok=True)

DB_PATH = CONFIG.db_path
STORAGE_DIR = CONFIG.storage_dir
