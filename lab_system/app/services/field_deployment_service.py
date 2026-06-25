"""
Field Deployment Service — Deployment, Health, Recovery, Support Wizards

Provides wizards for field deployment, health checking, recovery,
and support package generation.
"""

import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
class DeploymentWizard:
    """Creates required directory structure for field deployment."""

    def __init__(self, base_path: str | Path):
        self._base_path = Path(base_path)

    def run(self) -> dict:
        """Run the deployment wizard."""
        result = {"success": False, "directories_created": []}
        try:
            dirs = ["database", "backups", "snapshots", "logs", "config"]
            for d in dirs:
                dir_path = self._base_path / d
                dir_path.mkdir(parents=True, exist_ok=True)
                result["directories_created"].append(str(dir_path))
            db_path = self._base_path / "database" / "lab_system.db"
            if not db_path.exists():
                conn = sqlite3.connect(str(db_path))
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS meta (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                """)
                conn.execute(
                    "INSERT OR REPLACE INTO meta(key, value) VALUES(?, ?)",
                    ("schema_version", "14"),
                )
                conn.execute(
                    "INSERT OR REPLACE INTO meta(key, value) VALUES(?, ?)",
                    ("deployed_at", datetime.now().isoformat(timespec="seconds")),
                )
                conn.commit()
                conn.close()
            result["success"] = True
        except Exception as e:
            result["error"] = str(e)
        return result


class HealthCheckWizard:
    """Performs comprehensive health checks."""

    def __init__(self, db_path: str | Path):
        self._db_path = Path(db_path)

    def run(self) -> dict:
        """Run health checks."""
        result = {"checks": [], "overall_status": "healthy"}
        checks = [
            self._check_database_integrity,
            self._check_database_access,
            self._check_schema_version,
            self._check_storage_space,
        ]
        for check_fn in checks:
            try:
                check_result = check_fn()
                result["checks"].append(check_result)
            except Exception as e:
                result["checks"].append({
                    "name": check_fn.__name__,
                    "status": "error",
                    "details": str(e),
                })
        unhealthy = [c for c in result["checks"] if c.get("status") in ("unhealthy", "error")]
        if unhealthy:
            result["overall_status"] = "unhealthy"
        elif any(c.get("status") == "degraded" for c in result["checks"]):
            result["overall_status"] = "degraded"
        return result

    def _check_database_integrity(self) -> dict:
        try:
            conn = sqlite3.connect(str(self._db_path))
            row = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            return {
                "name": "database_integrity",
                "status": "healthy" if row[0] == "ok" else "unhealthy",
                "details": row[0],
            }
        except Exception as e:
            return {"name": "database_integrity", "status": "error", "details": str(e)}

    def _check_database_access(self) -> dict:
        try:
            conn = sqlite3.connect(str(self._db_path))
            conn.execute("SELECT 1").fetchone()
            conn.close()
            return {"name": "database_access", "status": "healthy", "details": "Accessible"}
        except Exception as e:
            return {"name": "database_access", "status": "unhealthy", "details": str(e)}

    def _check_schema_version(self) -> dict:
        try:
            conn = sqlite3.connect(str(self._db_path))
            conn.row_factory = sqlite3.Row
            try:
                row = conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
                version = row["value"] if row else "unknown"
            except Exception:
                version = "unknown"
            conn.close()
            return {"name": "schema_version", "status": "healthy", "details": f"Version {version}"}
        except Exception as e:
            return {"name": "schema_version", "status": "error", "details": str(e)}

    def _check_storage_space(self) -> dict:
        try:
            stat = os.statvfs(str(self._db_path.parent))
            free_gb = (stat.f_bavail * stat.f_frsize) / (1024 ** 3)
            return {
                "name": "storage_space",
                "status": "healthy" if free_gb > 1 else "degraded",
                "details": f"{free_gb:.1f}GB free",
            }
        except Exception as e:
            return {"name": "storage_space", "status": "error", "details": str(e)}


class RecoveryWizard:
    """Recovers database from backup."""

    def __init__(self, backup_path: str | Path, target_path: str | Path):
        self._backup_path = Path(backup_path)
        self._target_path = Path(target_path)

    def run(self) -> dict:
        """Run recovery wizard."""
        result = {"success": False, "steps": []}
        try:
            if not self._backup_path.exists():
                result["error"] = "Backup file not found"
                return result
            result["steps"].append("backup_verified")
            integrity = self._verify_integrity()
            if not integrity["ok"]:
                result["error"] = f"Backup integrity failed: {integrity['error']}"
                return result
            result["steps"].append("integrity_verified")
            shutil.copy2(str(self._backup_path), str(self._target_path))
            result["steps"].append("restore_completed")
            post_verify = self._verify_restored()
            if not post_verify["ok"]:
                result["error"] = f"Post-restore verification failed: {post_verify['error']}"
                return result
            result["steps"].append("verification_passed")
            result["success"] = True
        except Exception as e:
            result["error"] = str(e)
        return result

    def _verify_integrity(self) -> dict:
        try:
            conn = sqlite3.connect(str(self._backup_path))
            row = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            if row and row[0] == "ok":
                return {"ok": True}
            return {"ok": False, "error": row[0] if row else "unknown"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _verify_restored(self) -> dict:
        try:
            conn = sqlite3.connect(str(self._target_path))
            row = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            if row and row[0] == "ok":
                return {"ok": True}
            return {"ok": False, "error": row[0] if row else "unknown"}
        except Exception as e:
            return {"ok": False, "error": str(e)}


class SupportPackageGenerator:
    """Generates support package for troubleshooting."""

    def __init__(self, base_path: str | Path):
        self._base_path = Path(base_path)

    def generate(self) -> dict:
        """Generate support package."""
        result = {"success": False, "files": []}
        try:
            pkg_dir = self._base_path / "support_package"
            pkg_dir.mkdir(exist_ok=True)
            readme = pkg_dir / "README.txt"
            readme.write_text(
                "LabReceiptSystem Support Package\n"
                f"Generated: {datetime.now().isoformat()}\n"
                "Include this package when contacting support.\n"
            )
            result["files"].append(str(readme))
            result["success"] = True
        except Exception as e:
            result["error"] = str(e)
        return result


class FieldReadinessChecker:
    """Checks field readiness for deployment."""

    def __init__(self, db_path: str | Path):
        self._db_path = Path(db_path)

    def check(self) -> dict:
        """Run field readiness checks."""
        checklist = [
            self._check_database_exists,
            self._check_database_integrity,
            self._check_backup_directory,
            self._check_logs_directory,
        ]
        results = []
        for check_fn in checklist:
            try:
                results.append(check_fn())
            except Exception as e:
                results.append({"item": check_fn.__name__, "ready": False, "details": str(e)})
        overall_ready = all(r.get("ready", False) for r in results)
        return {"checklist": results, "overall_ready": overall_ready}

    def check_concurrent_readiness(self) -> dict:
        """Check if system is ready for concurrent users."""
        try:
            conn = sqlite3.connect(str(self._db_path))
            conn.execute("PRAGMA journal_mode=WAL")
            row = conn.execute("PRAGMA journal_mode").fetchone()
            conn.close()
            return {"ready": row[0] == "wal", "details": f"Journal mode: {row[0]}"}
        except Exception as e:
            return {"ready": False, "details": str(e)}

    def _check_database_exists(self) -> dict:
        return {
            "item": "database_exists",
            "ready": self._db_path.exists(),
            "details": str(self._db_path),
        }

    def _check_database_integrity(self) -> dict:
        try:
            conn = sqlite3.connect(str(self._db_path))
            row = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            return {
                "item": "database_integrity",
                "ready": row[0] == "ok",
                "details": row[0],
            }
        except Exception as e:
            return {"item": "database_integrity", "ready": False, "details": str(e)}

    def _check_backup_directory(self) -> dict:
        backup_dir = self._db_path.parent / "backups"
        return {
            "item": "backup_directory",
            "ready": backup_dir.exists(),
            "details": str(backup_dir),
        }

    def _check_logs_directory(self) -> dict:
        logs_dir = self._db_path.parent / "logs"
        return {
            "item": "logs_directory",
            "ready": logs_dir.exists(),
            "details": str(logs_dir),
        }


class DisasterRecoveryValidator:
    """Validates disaster recovery readiness."""

    def __init__(self, db_path: str | Path, backup_path: str | Path):
        self._db_path = Path(db_path)
        self._backup_path = Path(backup_path)

    def validate(self) -> dict:
        """Validate disaster recovery readiness."""
        result = {"ready": False, "checks": []}
        checks = [
            self._check_backup_exists,
            self._check_backup_integrity,
            self._check_restore_capability,
        ]
        for check_fn in checks:
            try:
                result["checks"].append(check_fn())
            except Exception as e:
                result["checks"].append({"name": check_fn.__name__, "passed": False, "error": str(e)})
        result["ready"] = all(c.get("passed", False) for c in result["checks"])
        return result

    def _check_backup_exists(self) -> dict:
        return {
            "name": "backup_exists",
            "passed": self._backup_path.exists(),
            "details": str(self._backup_path),
        }

    def _check_backup_integrity(self) -> dict:
        try:
            conn = sqlite3.connect(str(self._backup_path))
            row = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            return {
                "name": "backup_integrity",
                "passed": row[0] == "ok",
                "details": row[0],
            }
        except Exception as e:
            return {"name": "backup_integrity", "passed": False, "error": str(e)}

    def _check_restore_capability(self) -> dict:
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
                tmp_path = tmp.name
            shutil.copy2(str(self._backup_path), tmp_path)
            conn = sqlite3.connect(tmp_path)
            row = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            os.unlink(tmp_path)
            return {
                "name": "restore_capability",
                "passed": row[0] == "ok",
                "details": "Restore test successful",
            }
        except Exception as e:
            return {"name": "restore_capability", "passed": False, "error": str(e)}
