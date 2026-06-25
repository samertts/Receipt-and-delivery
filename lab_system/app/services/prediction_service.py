"""
Predictive Intelligence Service — Prediction Engine

Predicts backup failures, recovery failures, sync failures,
capacity growth, database growth, storage exhaustion, and
performance degradation.
"""

import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from lab_system.app.settings.config import CONFIG


class RiskLevel:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PredictiveIntelligenceService:
    """Predicts failures and generates risk forecasts."""

    def __init__(self, db_path: str | Path | None = None):
        self._db_path = str(db_path or CONFIG.db_path)

    def _get_conn(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 5000;")
        return conn

    def predict_backup_failure(self) -> dict:
        risk = RiskLevel.LOW
        confidence = 50
        evidence = []
        try:
            conn = self._get_conn()
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM backups WHERE created_at >= datetime('now', '-7 days')"
            ).fetchone()
            recent_backups = row["cnt"] if row else 0
            row2 = conn.execute(
                "SELECT COUNT(*) as cnt FROM backups WHERE created_at >= datetime('now', '-30 days')"
            ).fetchone()
            monthly_backups = row2["cnt"] if row2 else 0
            conn.close()
            evidence.append(f"Last 7 days: {recent_backups} backups")
            evidence.append(f"Last 30 days: {monthly_backups} backups")
            if recent_backups == 0:
                risk = RiskLevel.HIGH
                confidence = 80
                evidence.append("No backups in last 7 days")
            elif monthly_backups < 4:
                risk = RiskLevel.MEDIUM
                confidence = 65
                evidence.append("Low monthly backup count")
            else:
                confidence = 30
                evidence.append("Backup frequency is healthy")
        except Exception as e:
            risk = RiskLevel.MEDIUM
            confidence = 50
            evidence.append(f"Error checking backup history: {e}")
        return {
            "risk_type": "backup_failure",
            "risk_level": risk,
            "confidence": confidence,
            "evidence": evidence,
            "recommendation": self._get_recommendation("backup_failure", risk),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

    def predict_sync_failure(self) -> dict:
        risk = RiskLevel.LOW
        confidence = 50
        evidence = []
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
            row3 = conn.execute(
                "SELECT COUNT(*) as cnt FROM sync_queue WHERE status='pending' "
                "AND retry_count >= 3"
            ).fetchone()
            max_retry = row3["cnt"] if row3 else 0
            conn.close()
            evidence.append(f"Pending: {pending}, Failed: {failed}, MaxRetry: {max_retry}")
            if failed > 10:
                risk = RiskLevel.HIGH
                confidence = 85
                evidence.append("High failure count")
            elif pending > 50:
                risk = RiskLevel.MEDIUM
                confidence = 70
                evidence.append("High pending queue depth")
            else:
                confidence = 25
                evidence.append("Sync queue is healthy")
        except Exception as e:
            risk = RiskLevel.MEDIUM
            confidence = 50
            evidence.append(f"Error: {e}")
        return {
            "risk_type": "sync_failure",
            "risk_level": risk,
            "confidence": confidence,
            "evidence": evidence,
            "recommendation": self._get_recommendation("sync_failure", risk),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

    def predict_storage_exhaustion(self) -> dict:
        risk = RiskLevel.LOW
        confidence = 50
        evidence = []
        try:
            storage = Path(CONFIG.storage_dir)
            usage = os.statvfs(str(storage))
            free_bytes = usage.f_bavail * usage.f_frsize
            total_bytes = usage.f_blocks * usage.f_frsize
            free_gb = free_bytes / (1024 ** 3)
            total_gb = total_bytes / (1024 ** 3)
            used_pct = ((total_bytes - free_bytes) / total_bytes) * 100
            evidence.append(f"Free: {free_gb:.1f}GB, Total: {total_gb:.1f}GB, Used: {used_pct:.1f}%")
            if free_gb < 1:
                risk = RiskLevel.CRITICAL
                confidence = 95
                evidence.append("Less than 1GB free")
            elif free_gb < 5:
                risk = RiskLevel.HIGH
                confidence = 80
                evidence.append("Less than 5GB free")
            elif used_pct > 80:
                risk = RiskLevel.MEDIUM
                confidence = 65
                evidence.append("Disk usage above 80%")
            else:
                confidence = 20
                evidence.append("Storage is healthy")
        except Exception as e:
            risk = RiskLevel.MEDIUM
            confidence = 50
            evidence.append(f"Error: {e}")
        return {
            "risk_type": "storage_exhaustion",
            "risk_level": risk,
            "confidence": confidence,
            "evidence": evidence,
            "recommendation": self._get_recommendation("storage_exhaustion", risk),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

    def predict_database_growth(self) -> dict:
        risk = RiskLevel.LOW
        confidence = 50
        evidence = []
        try:
            db_path = Path(self._db_path)
            if db_path.exists():
                size_mb = db_path.stat().st_size / (1024 * 1024)
                evidence.append(f"Current DB size: {size_mb:.1f}MB")
                if size_mb > 500:
                    risk = RiskLevel.HIGH
                    confidence = 75
                    evidence.append("Database is large")
                elif size_mb > 200:
                    risk = RiskLevel.MEDIUM
                    confidence = 60
                    evidence.append("Database is moderately sized")
                else:
                    confidence = 25
                    evidence.append("Database size is healthy")
            else:
                evidence.append("Database file not found")
        except Exception as e:
            risk = RiskLevel.MEDIUM
            confidence = 50
            evidence.append(f"Error: {e}")
        return {
            "risk_type": "database_growth",
            "risk_level": risk,
            "confidence": confidence,
            "evidence": evidence,
            "recommendation": self._get_recommendation("database_growth", risk),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

    def predict_performance_degradation(self) -> dict:
        risk = RiskLevel.LOW
        confidence = 50
        evidence = []
        try:
            conn = self._get_conn()
            start = time.monotonic()
            conn.execute("SELECT COUNT(*) FROM sqlite_master")
            query_ms = (time.monotonic() - start) * 1000
            evidence.append(f"Schema query: {query_ms:.2f}ms")
            if query_ms > 100:
                risk = RiskLevel.HIGH
                confidence = 80
                evidence.append("Schema query is slow")
            elif query_ms > 50:
                risk = RiskLevel.MEDIUM
                confidence = 60
                evidence.append("Schema query is moderately slow")
            else:
                confidence = 20
                evidence.append("Query performance is healthy")
            conn.close()
        except Exception as e:
            risk = RiskLevel.MEDIUM
            confidence = 50
            evidence.append(f"Error: {e}")
        return {
            "risk_type": "performance_degradation",
            "risk_level": risk,
            "confidence": confidence,
            "evidence": evidence,
            "recommendation": self._get_recommendation("performance_degradation", risk),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

    def predict_recovery_failure(self) -> dict:
        risk = RiskLevel.LOW
        confidence = 50
        evidence = []
        try:
            conn = self._get_conn()
            row = conn.execute("PRAGMA integrity_check;").fetchone()
            conn.close()
            if row and row[0] == "ok":
                confidence = 20
                evidence.append("Database integrity is healthy")
            else:
                risk = RiskLevel.CRITICAL
                confidence = 90
                evidence.append(f"Integrity check failed: {row}")
        except Exception as e:
            risk = RiskLevel.HIGH
            confidence = 75
            evidence.append(f"Integrity check error: {e}")
        return {
            "risk_type": "recovery_failure",
            "risk_level": risk,
            "confidence": confidence,
            "evidence": evidence,
            "recommendation": self._get_recommendation("recovery_failure", risk),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

    def get_all_predictions(self) -> dict:
        predictions = {
            "backup_failure": self.predict_backup_failure(),
            "sync_failure": self.predict_sync_failure(),
            "storage_exhaustion": self.predict_storage_exhaustion(),
            "database_growth": self.predict_database_growth(),
            "performance_degradation": self.predict_performance_degradation(),
            "recovery_failure": self.predict_recovery_failure(),
        }
        risk_counts = {RiskLevel.LOW: 0, RiskLevel.MEDIUM: 0, RiskLevel.HIGH: 0, RiskLevel.CRITICAL: 0}
        for pred in predictions.values():
            risk_counts[pred["risk_level"]] = risk_counts.get(pred["risk_level"], 0) + 1
        overall_risk = RiskLevel.LOW
        if risk_counts[RiskLevel.CRITICAL] > 0:
            overall_risk = RiskLevel.CRITICAL
        elif risk_counts[RiskLevel.HIGH] > 0:
            overall_risk = RiskLevel.HIGH
        elif risk_counts[RiskLevel.MEDIUM] > 0:
            overall_risk = RiskLevel.MEDIUM
        return {
            "overall_risk": overall_risk,
            "risk_distribution": risk_counts,
            "predictions": predictions,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

    def _get_recommendation(self, risk_type: str, risk_level: str) -> str:
        recommendations = {
            "backup_failure": {
                RiskLevel.HIGH: "Immediately create a backup and investigate backup service",
                RiskLevel.MEDIUM: "Schedule manual backup and verify backup configuration",
                RiskLevel.LOW: "Continue monitoring backup schedule",
            },
            "sync_failure": {
                RiskLevel.HIGH: "Clear failed sync queue entries and restart sync service",
                RiskLevel.MEDIUM: "Review sync queue and resolve conflicts",
                RiskLevel.LOW: "Continue monitoring sync queue depth",
            },
            "storage_exhaustion": {
                RiskLevel.CRITICAL: "Free disk space immediately. Remove old backups/logs.",
                RiskLevel.HIGH: "Clean up old backups and logs to free space",
                RiskLevel.MEDIUM: "Monitor disk usage closely",
                RiskLevel.LOW: "Storage is adequate",
            },
            "database_growth": {
                RiskLevel.HIGH: "Review and archive old records. Consider vacuum.",
                RiskLevel.MEDIUM: "Monitor growth trend and plan archiving",
                RiskLevel.LOW: "Database size is healthy",
            },
            "performance_degradation": {
                RiskLevel.HIGH: "Run PRAGMA optimize and review slow queries",
                RiskLevel.MEDIUM: "Monitor query performance",
                RiskLevel.LOW: "Performance is healthy",
            },
            "recovery_failure": {
                RiskLevel.CRITICAL: "Database corruption detected. Restore from backup immediately.",
                RiskLevel.HIGH: "Run integrity check and prepare for recovery",
                RiskLevel.LOW: "Recovery capability is healthy",
            },
        }
        return recommendations.get(risk_type, {}).get(risk_level, "Monitor situation")
