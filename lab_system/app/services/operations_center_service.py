"""
Operations Center Service — Automated Anomaly Detection and Recovery

Provides automatic anomaly detection, recovery recommendations,
maintenance recommendations, and operations dashboard.
"""

import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from lab_system.app.settings.config import CONFIG


class OperationsCenter:
    """Automated operations center for monitoring and recovery."""

    def __init__(self, db_path: str | Path | None = None):
        self._db_path = str(db_path or CONFIG.db_path)

    def detect_anomalies(self) -> dict:
        """Detect system anomalies."""
        anomalies = []
        db_check = self._check_database_anomalies()
        if db_check["anomaly"]:
            anomalies.append(db_check)
        storage_check = self._check_storage_anomalies()
        if storage_check["anomaly"]:
            anomalies.append(storage_check)
        performance_check = self._check_performance_anomalies()
        if performance_check["anomaly"]:
            anomalies.append(performance_check)
        return {
            "anomalies": anomalies,
            "count": len(anomalies),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

    def get_recovery_recommendations(self) -> list[dict]:
        """Get recovery recommendations."""
        recommendations = []
        try:
            conn = sqlite3.connect(self._db_path, timeout=1)
            row = conn.execute("PRAGMA journal_mode").fetchone()
            mode = row[0] if row else "unknown"
            conn.close()
            if mode != "wal":
                recommendations.append({
                    "type": "database_mode",
                    "severity": "medium",
                    "recommendation": "Switch to WAL mode for better concurrency",
                    "action": "PRAGMA journal_mode=WAL",
                })
        except Exception:
            recommendations.append({
                "type": "database_access",
                "severity": "high",
                "recommendation": "Check database accessibility",
                "action": "Verify database file permissions",
            })
        try:
            if os.path.exists(self._db_path):
                size_mb = os.path.getsize(self._db_path) / (1024 * 1024)
                if size_mb > 1000:
                    recommendations.append({
                        "type": "database_size",
                        "severity": "medium",
                        "recommendation": f"Database size is {size_mb:.0f}MB, consider VACUUM",
                        "action": "VACUUM",
                    })
        except Exception:
            pass
        return recommendations

    def get_maintenance_recommendations(self) -> list[dict]:
        """Get maintenance recommendations."""
        recommendations = []
        recommendations.append({
            "type": "backup",
            "frequency": "daily",
            "recommendation": "Perform daily backups",
            "priority": "high",
        })
        recommendations.append({
            "type": "vacuum",
            "frequency": "weekly",
            "recommendation": "Run VACUUM to optimize database",
            "priority": "medium",
        })
        recommendations.append({
            "type": "integrity_check",
            "frequency": "daily",
            "recommendation": "Run integrity check",
            "priority": "high",
        })
        recommendations.append({
            "type": "log_rotation",
            "frequency": "weekly",
            "recommendation": "Rotate and compress logs",
            "priority": "low",
        })
        return recommendations

    def get_system_health(self) -> dict:
        """Get comprehensive system health status."""
        subsystems = {}
        db_health = self._get_database_health()
        subsystems["database"] = db_health
        storage_health = self._get_storage_health()
        subsystems["storage"] = storage_health
        overall_status = "healthy"
        for _, health in subsystems.items():
            if health.get("status") == "unhealthy":
                overall_status = "unhealthy"
                break
            elif health.get("status") == "degraded":
                overall_status = "degraded"
        return {
            "overall_status": overall_status,
            "subsystems": subsystems,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

    def get_dashboard(self) -> dict:
        """Get operations dashboard data."""
        health = self.get_system_health()
        anomalies = self.detect_anomalies()
        recommendations = self.get_recovery_recommendations()
        return {
            "health": health,
            "anomalies": anomalies,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

    def _check_database_anomalies(self) -> dict:
        result = {"name": "database", "anomaly": False, "details": ""}
        try:
            conn = sqlite3.connect(self._db_path, timeout=1)
            row = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            if row and row[0] != "ok":
                result["anomaly"] = True
                result["details"] = f"Integrity check failed: {row[0]}"
                result["severity"] = "high"
        except sqlite3.OperationalError as e:
            result["anomaly"] = True
            result["details"] = f"Database access error: {e}"
            result["severity"] = "high"
        except Exception as e:
            result["anomaly"] = True
            result["details"] = str(e)
            result["severity"] = "medium"
        return result

    def _check_storage_anomalies(self) -> dict:
        result = {"name": "storage", "anomaly": False, "details": ""}
        try:
            stat = os.statvfs(os.path.dirname(self._db_path) or ".")
            free_gb = (stat.f_bavail * stat.f_frsize) / (1024 ** 3)
            if free_gb < 1:
                result["anomaly"] = True
                result["details"] = f"Low disk space: {free_gb:.1f}GB free"
                result["severity"] = "high"
            elif free_gb < 5:
                result["anomaly"] = True
                result["details"] = f"Disk space getting low: {free_gb:.1f}GB free"
                result["severity"] = "medium"
        except Exception as e:
            result["anomaly"] = True
            result["details"] = str(e)
            result["severity"] = "low"
        return result

    def _check_performance_anomalies(self) -> dict:
        result = {"name": "performance", "anomaly": False, "details": ""}
        try:
            start = time.time()
            conn = sqlite3.connect(self._db_path, timeout=1)
            conn.execute("SELECT 1").fetchone()
            conn.close()
            elapsed = (time.time() - start) * 1000
            if elapsed > 1000:
                result["anomaly"] = True
                result["details"] = f"Slow database response: {elapsed:.0f}ms"
                result["severity"] = "medium"
        except Exception as e:
            result["anomaly"] = True
            result["details"] = str(e)
            result["severity"] = "medium"
        return result

    def _get_database_health(self) -> dict:
        try:
            conn = sqlite3.connect(self._db_path, timeout=1)
            row = conn.execute("PRAGMA integrity_check").fetchone()
            size = os.path.getsize(self._db_path) if os.path.exists(self._db_path) else 0
            conn.close()
            return {
                "status": "healthy" if row[0] == "ok" else "unhealthy",
                "integrity": row[0],
                "size_mb": size / (1024 * 1024),
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def _get_storage_health(self) -> dict:
        try:
            stat = os.statvfs(os.path.dirname(self._db_path) or ".")
            free_gb = (stat.f_bavail * stat.f_frsize) / (1024 ** 3)
            total_gb = (stat.f_blocks * stat.f_frsize) / (1024 ** 3)
            used_pct = ((total_gb - free_gb) / total_gb * 100) if total_gb > 0 else 0
            status = "healthy"
            if free_gb < 1:
                status = "unhealthy"
            elif free_gb < 5:
                status = "degraded"
            return {
                "status": status,
                "free_gb": free_gb,
                "total_gb": total_gb,
                "used_percent": used_pct,
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
