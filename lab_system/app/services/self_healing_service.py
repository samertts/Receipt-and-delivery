"""
Self Healing Service — Automatic Detection and Safe Recovery

Detects database locks, backup failures, recovery failures,
sync failures, and storage exhaustion. Attempts safe automatic
recovery with full audit evidence.
"""

import shutil
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from lab_system.app.settings.config import CONFIG


class HealthStatus:
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class SelfHealingService:
    """Detects failures and attempts safe automatic recovery."""

    def __init__(self, db_path: str | Path | None = None):
        self._db_path = str(db_path or CONFIG.db_path)
        self._healing_log: list[dict] = []
        self._max_healing_actions = 10

    def _log_healing(self, action: str, result: str, details: str = ""):
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "action": action,
            "result": result,
            "details": details,
        }
        self._healing_log.append(entry)
        if len(self._healing_log) > 100:
            self._healing_log = self._healing_log[-50:]

    def detect_database_lock(self) -> dict:
        result = {"status": HealthStatus.UNKNOWN, "details": ""}
        try:
            conn = sqlite3.connect(self._db_path, timeout=1)
            conn.execute("PRAGMA busy_timeout = 1000;")
            row = conn.execute("PRAGMA journal_mode;").fetchone()
            mode = row[0] if row else "unknown"
            conn.execute("PRAGMA wal_checkpoint(PASSIVE);")
            conn.close()
            result["status"] = HealthStatus.HEALTHY
            result["details"] = f"Journal mode: {mode}"
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() or "busy" in str(e).lower():
                result["status"] = HealthStatus.UNHEALTHY
                result["details"] = f"Database locked: {e}"
            else:
                result["status"] = HealthStatus.DEGRADED
                result["details"] = str(e)
        except Exception as e:
            result["status"] = HealthStatus.UNHEALTHY
            result["details"] = str(e)
        return result

    def recover_database_lock(self) -> dict:
        result = {"success": False, "actions": []}
        try:
            conn = sqlite3.connect(self._db_path, timeout=5)
            conn.execute("PRAGMA busy_timeout = 10000;")
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            conn.close()
            result["success"] = True
            result["actions"].append("WAL checkpoint performed")
            self._log_healing("database_lock_recovery", "success", "WAL checkpoint")
        except Exception as e:
            result["actions"].append(f"Recovery failed: {e}")
            self._log_healing("database_lock_recovery", "failed", str(e))
        return result

    def detect_backup_health(self) -> dict:
        result = {"status": HealthStatus.UNKNOWN, "details": ""}
        backup_dir = Path(CONFIG.storage_dir) / "backups"
        if not backup_dir.exists():
            result["status"] = HealthStatus.DEGRADED
            result["details"] = "Backup directory does not exist"
            return result
        db_files = list(backup_dir.glob("*.db"))
        if not db_files:
            result["status"] = HealthStatus.DEGRADED
            result["details"] = "No backup files found"
            return result
        latest = max(db_files, key=lambda f: f.stat().st_mtime)
        age_hours = (time.time() - latest.stat().st_mtime) / 3600
        result["status"] = HealthStatus.HEALTHY if age_hours < 24 else HealthStatus.DEGRADED
        result["details"] = f"{len(db_files)} backups, latest: {age_hours:.1f}h ago"
        return result

    def recover_backup_failure(self) -> dict:
        result = {"success": False, "actions": []}
        try:
            from lab_system.app.services.backup_service import create_backup
            system_user = {"id": 0, "username": "system", "role": "Admin", "status": "Active"}
            path = create_backup(user_id=None, notes="self_healing_auto_backup", user=system_user)
            result["success"] = True
            result["actions"].append(f"Backup created: {path}")
            self._log_healing("backup_recovery", "success", f"Path: {path}")
        except Exception as e:
            result["actions"].append(f"Backup creation failed: {e}")
            self._log_healing("backup_recovery", "failed", str(e))
        return result

    def detect_recovery_health(self) -> dict:
        result = {"status": HealthStatus.UNKNOWN, "details": ""}
        try:
            conn = sqlite3.connect(self._db_path, timeout=1)
            row = conn.execute("PRAGMA integrity_check;").fetchone()
            conn.close()
            if row and row[0] == "ok":
                result["status"] = HealthStatus.HEALTHY
                result["details"] = "Database integrity verified"
            else:
                result["status"] = HealthStatus.UNHEALTHY
                result["details"] = f"Integrity check: {row}"
        except Exception as e:
            result["status"] = HealthStatus.UNHEALTHY
            result["details"] = str(e)
        return result

    def detect_sync_health(self) -> dict:
        result = {"status": HealthStatus.UNKNOWN, "details": ""}
        try:
            conn = sqlite3.connect(self._db_path, timeout=1)
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM sync_queue WHERE status='pending'"
            ).fetchone()
            pending = row["cnt"] if row else 0
            row2 = conn.execute(
                "SELECT COUNT(*) as cnt FROM sync_queue WHERE status='failed'"
            ).fetchone()
            failed = row2["cnt"] if row2 else 0
            conn.close()
            if failed > 0:
                result["status"] = HealthStatus.UNHEALTHY
                result["details"] = f"{pending} pending, {failed} failed"
            elif pending > 100:
                result["status"] = HealthStatus.DEGRADED
                result["details"] = f"{pending} pending (high queue depth)"
            else:
                result["status"] = HealthStatus.HEALTHY
                result["details"] = f"{pending} pending, {failed} failed"
        except Exception as e:
            result["status"] = HealthStatus.DEGRADED
            result["details"] = str(e)
        return result

    def detect_storage_health(self) -> dict:
        result = {"status": HealthStatus.UNKNOWN, "details": ""}
        try:
            storage = Path(CONFIG.storage_dir)
            stat = shutil.disk_usage(str(storage))
            free_gb = stat.free / (1024 ** 3)
            total_gb = stat.total / (1024 ** 3)
            used_pct = (stat.used / stat.total) * 100
            if free_gb < 1:
                result["status"] = HealthStatus.UNHEALTHY
            elif free_gb < 5:
                result["status"] = HealthStatus.DEGRADED
            else:
                result["status"] = HealthStatus.HEALTHY
            result["details"] = (
                f"Free: {free_gb:.1f}GB, Total: {total_gb:.1f}GB, Used: {used_pct:.1f}%"
            )
        except Exception as e:
            result["status"] = HealthStatus.DEGRADED
            result["details"] = str(e)
        return result

    def get_overall_health(self) -> dict:
        checks = {
            "database_lock": self.detect_database_lock(),
            "backup": self.detect_backup_health(),
            "recovery": self.detect_recovery_health(),
            "sync": self.detect_sync_health(),
            "storage": self.detect_storage_health(),
        }
        status_weights = {
            HealthStatus.HEALTHY: 2,
            HealthStatus.DEGRADED: 1,
            HealthStatus.UNHEALTHY: 0,
            HealthStatus.UNKNOWN: 1,
        }
        total_weight = 0
        for check in checks.values():
            total_weight += status_weights.get(check["status"], 0)
        max_weight = len(checks) * 2
        health_score = (total_weight / max_weight) * 100 if max_weight > 0 else 0

        statuses = [c["status"] for c in checks.values()]
        if HealthStatus.UNHEALTHY in statuses:
            overall = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY

        return {
            "overall_status": overall,
            "health_score": round(health_score, 1),
            "checks": checks,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

    def attempt_auto_healing(self) -> dict:
        result = {"healed": 0, "failed": 0, "actions": []}
        db_lock = self.detect_database_lock()
        if db_lock["status"] == HealthStatus.UNHEALTHY:
            healing = self.recover_database_lock()
            if healing["success"]:
                result["healed"] += 1
                result["actions"].extend(healing["actions"])
            else:
                result["failed"] += 1
                result["actions"].extend(healing["actions"])

        backup = self.detect_backup_health()
        if backup["status"] == HealthStatus.DEGRADED:
            healing = self.recover_backup_failure()
            if healing["success"]:
                result["healed"] += 1
                result["actions"].extend(healing["actions"])
            else:
                result["failed"] += 1
                result["actions"].extend(healing["actions"])

        return result

    def get_healing_log(self) -> list[dict]:
        return list(self._healing_log)
