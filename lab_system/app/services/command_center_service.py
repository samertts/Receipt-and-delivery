"""
Command Center Service — Operational Command Dashboard

Provides laboratory operations command center with health scoring,
reliability metrics, security metrics, and operational alerts.
"""

import sqlite3
import time
from datetime import datetime
from pathlib import Path
from lab_system.app.settings.config import CONFIG


class CommandCenterService:
    """Laboratory Operations Command Center with health scoring."""

    def __init__(self, db_path: str | Path | None = None):
        self._db_path = str(db_path or CONFIG.db_path)

    def _get_conn(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 5000;")
        return conn

    def get_database_health(self) -> dict:
        score = 100
        details = []
        try:
            conn = self._get_conn()
            row = conn.execute("PRAGMA integrity_check;").fetchone()
            if not row or row[0] != "ok":
                score -= 50
                details.append("Integrity check failed")
            else:
                details.append("Integrity OK")
            row2 = conn.execute("PRAGMA page_count;").fetchone()
            pages = row2[0] if row2 else 0
            row3 = conn.execute("PRAGMA page_size;").fetchone()
            page_size = row3[0] if row3 else 0
            size_mb = (pages * page_size) / (1024 * 1024)
            details.append(f"Size: {size_mb:.1f}MB")
            if size_mb > 500:
                score -= 20
                details.append("Database is large")
            conn.close()
        except Exception as e:
            score -= 30
            details.append(f"Error: {e}")
        return {"score": max(0, score), "details": details}

    def get_backup_health(self) -> dict:
        score = 100
        details = []
        try:
            backup_dir = Path(CONFIG.storage_dir) / "backups"
            if not backup_dir.exists():
                score -= 30
                details.append("Backup directory missing")
                return {"score": max(0, score), "details": details}
            db_files = list(backup_dir.glob("*.db"))
            details.append(f"{len(db_files)} backups found")
            if not db_files:
                score -= 40
                details.append("No backups exist")
            else:
                latest = max(db_files, key=lambda f: f.stat().st_mtime)
                age_hours = (time.time() - latest.stat().st_mtime) / 3600
                details.append(f"Latest: {age_hours:.1f}h ago")
                if age_hours > 48:
                    score -= 30
                    details.append("Last backup is old")
                elif age_hours > 24:
                    score -= 15
                    details.append("Last backup is >24h old")
        except Exception as e:
            score -= 20
            details.append(f"Error: {e}")
        return {"score": max(0, score), "details": details}

    def get_recovery_health(self) -> dict:
        score = 100
        details = []
        try:
            conn = self._get_conn()
            row = conn.execute("PRAGMA integrity_check;").fetchone()
            if row and row[0] == "ok":
                details.append("Recovery capability: OK")
            else:
                score -= 50
                details.append("Integrity check failed")
            snapshot_dir = Path(CONFIG.storage_dir) / "snapshots"
            if snapshot_dir.exists():
                snapshots = list(snapshot_dir.glob("*.db"))
                details.append(f"{len(snapshots)} snapshots")
                if not snapshots:
                    score -= 10
            else:
                score -= 10
                details.append("No snapshot directory")
            conn.close()
        except Exception as e:
            score -= 20
            details.append(f"Error: {e}")
        return {"score": max(0, score), "details": details}

    def get_sync_health(self) -> dict:
        score = 100
        details = []
        try:
            conn = self._get_conn()
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM sync_queue WHERE status='pending'"
            ).fetchone()
            pending = row["cnt"] if row else 0
            row2 = conn.execute(
                "SELECT COUNT(*) as cnt FROM sync_queue WHERE status='failed'"
            ).fetchone()
            failed = row2["cnt"] if row2 else 0
            details.append(f"Pending: {pending}, Failed: {failed}")
            if failed > 0:
                score -= min(30, failed * 5)
                details.append(f"{failed} failed sync entries")
            if pending > 100:
                score -= 20
                details.append("High queue depth")
            elif pending > 50:
                score -= 10
            conn.close()
        except Exception as e:
            score -= 20
            details.append(f"Error: {e}")
        return {"score": max(0, score), "details": details}

    def get_security_health(self) -> dict:
        score = 100
        details = []
        try:
            conn = self._get_conn()
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM login_attempts WHERE success=0 "
                "AND attempted_at >= datetime('now', '-24 hours')"
            ).fetchone()
            failed_logins = row["cnt"] if row else 0
            details.append(f"Failed logins (24h): {failed_logins}")
            if failed_logins > 20:
                score -= 30
                details.append("High failed login count")
            elif failed_logins > 10:
                score -= 15
            row2 = conn.execute(
                "SELECT COUNT(*) as cnt FROM audit_logs "
                "WHERE timestamp >= datetime('now', '-24 hours')"
            ).fetchone()
            audit_count = row2["cnt"] if row2 else 0
            details.append(f"Audit events (24h): {audit_count}")
            conn.close()
        except Exception as e:
            score -= 10
            details.append(f"Error: {e}")
        return {"score": max(0, score), "details": details}

    def get_performance_health(self) -> dict:
        score = 100
        details = []
        try:
            conn = self._get_conn()
            start = time.monotonic()
            conn.execute("SELECT COUNT(*) FROM sqlite_master")
            query_ms = (time.monotonic() - start) * 1000
            details.append(f"Schema query: {query_ms:.2f}ms")
            if query_ms > 100:
                score -= 30
            elif query_ms > 50:
                score -= 15
            conn.close()
        except Exception as e:
            score -= 20
            details.append(f"Error: {e}")
        return {"score": max(0, score), "details": details}

    def get_user_activity_health(self) -> dict:
        score = 100
        details = []
        try:
            conn = self._get_conn()
            row = conn.execute(
                "SELECT COUNT(DISTINCT user_id) as cnt FROM audit_logs "
                "WHERE timestamp >= datetime('now', '-24 hours')"
            ).fetchone()
            active_users = row["cnt"] if row else 0
            details.append(f"Active users (24h): {active_users}")
            if active_users == 0:
                score -= 10
                details.append("No user activity in 24h")
            conn.close()
        except Exception as e:
            score -= 10
            details.append(f"Error: {e}")
        return {"score": max(0, score), "details": details}

    def get_operational_alerts(self) -> list[dict]:
        alerts = []
        db_health = self.get_database_health()
        if db_health["score"] < 80:
            alerts.append({
                "severity": "high" if db_health["score"] < 50 else "medium",
                "category": "database",
                "message": "Database health is degraded",
                "details": db_health["details"],
            })
        backup_health = self.get_backup_health()
        if backup_health["score"] < 80:
            alerts.append({
                "severity": "high" if backup_health["score"] < 50 else "medium",
                "category": "backup",
                "message": "Backup health is degraded",
                "details": backup_health["details"],
            })
        sync_health = self.get_sync_health()
        if sync_health["score"] < 80:
            alerts.append({
                "severity": "medium",
                "category": "sync",
                "message": "Sync queue has issues",
                "details": sync_health["details"],
            })
        sec_health = self.get_security_health()
        if sec_health["score"] < 80:
            alerts.append({
                "severity": "high" if sec_health["score"] < 50 else "medium",
                "category": "security",
                "message": "Security concerns detected",
                "details": sec_health["details"],
            })
        return alerts

    def get_command_center_report(self) -> dict:
        db = self.get_database_health()
        backup = self.get_backup_health()
        recovery = self.get_recovery_health()
        sync = self.get_sync_health()
        security = self.get_security_health()
        perf = self.get_performance_health()
        activity = self.get_user_activity_health()

        weights = {
            "database": 0.25,
            "backup": 0.20,
            "recovery": 0.15,
            "sync": 0.10,
            "security": 0.15,
            "performance": 0.10,
            "activity": 0.05,
        }
        scores = {
            "database": db["score"],
            "backup": backup["score"],
            "recovery": recovery["score"],
            "sync": sync["score"],
            "security": security["score"],
            "performance": perf["score"],
            "activity": activity["score"],
        }
        overall_score = sum(scores[k] * weights[k] for k in weights)

        return {
            "overall_health_score": round(overall_score, 1),
            "overall_status": (
                "healthy" if overall_score >= 80
                else "degraded" if overall_score >= 60
                else "unhealthy"
            ),
            "scores": {
                "database": {"score": db["score"], "weight": weights["database"], "details": db["details"]},
                "backup": {"score": backup["score"], "weight": weights["backup"], "details": backup["details"]},
                "recovery": {"score": recovery["score"], "weight": weights["recovery"], "details": recovery["details"]},
                "sync": {"score": sync["score"], "weight": weights["sync"], "details": sync["details"]},
                "security": {"score": security["score"], "weight": weights["security"], "details": security["details"]},
                "performance": {"score": perf["score"], "weight": weights["performance"], "details": perf["details"]},
                "activity": {"score": activity["score"], "weight": weights["activity"], "details": activity["details"]},
            },
            "alerts": self.get_operational_alerts(),
            "alert_count": len(self.get_operational_alerts()),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
