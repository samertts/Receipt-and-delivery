from pathlib import Path
from dataclasses import dataclass
from lab_system.app.utils.constants import APP_NAME


@dataclass(frozen=True)
class AppConfig:
    base_dir: Path
    app_dir: Path
    storage_dir: Path
    assets_dir: Path
    db_path: Path
    app_name: str


BASE_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = BASE_DIR.parent
CONFIG = AppConfig(
    base_dir=BASE_DIR,
    app_dir=ROOT_DIR,
    storage_dir=BASE_DIR / 'storage',
    assets_dir=ROOT_DIR / 'assets',
    db_path=ROOT_DIR / 'lab_system.db',
    app_name=APP_NAME,
)

for folder in ['receipts', 'attachments', 'exports', 'backups', 'temp']:
    (CONFIG.storage_dir / folder).mkdir(parents=True, exist_ok=True)
