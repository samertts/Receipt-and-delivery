from pathlib import Path
from lab_system.app.settings.config import CONFIG


class StorageManager:
    def __init__(self) -> None:
        self.base = CONFIG.storage_dir

    def path_for(self, category: str) -> Path:
        path = self.base / category
        path.mkdir(parents=True, exist_ok=True)
        return path


storage_manager = StorageManager()
