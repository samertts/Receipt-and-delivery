"""
Mobile Readiness Service — Mobile Contracts and Offline Support

Provides mobile API contracts, offline data management,
sync protocol contracts, and push notification readiness.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from lab_system.app.settings.config import CONFIG


class MobileReceiptContract:
    """Contract for mobile receipt operations."""

    @staticmethod
    def create_receipt_data(receipt: dict, items: list[dict]) -> dict:
        return {
            "contract_version": "1.0",
            "operation": "create_receipt",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "data": {
                "receipt": receipt,
                "items": items,
            },
            "offline_id": receipt.get("offline_id"),
            "device_id": receipt.get("device_id"),
        }

    @staticmethod
    def update_receipt_data(receipt_id: int, updates: dict) -> dict:
        return {
            "contract_version": "1.0",
            "operation": "update_receipt",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "receipt_id": receipt_id,
            "updates": updates,
        }

    @staticmethod
    def receipt_response(receipt: dict, success: bool, error: str = "") -> dict:
        return {
            "contract_version": "1.0",
            "success": success,
            "receipt": receipt,
            "error": error,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }


class OfflineDataStore:
    """Offline-first data management for mobile."""

    def __init__(self, db_path: str | Path | None = None):
        self._db_path = str(db_path or CONFIG.db_path)

    def _get_conn(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 5000;")
        return conn

    def initialize_offline_schema(self):
        conn = self._get_conn()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS offline_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id INTEGER DEFAULT 0,
                    payload TEXT NOT NULL,
                    device_id TEXT DEFAULT '',
                    offline_id TEXT UNIQUE NOT NULL,
                    created_at TEXT NOT NULL,
                    synced_at TEXT DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','synced','failed')),
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    error_message TEXT DEFAULT ''
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_offline_status ON offline_queue(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_offline_entity ON offline_queue(entity_type, entity_id)"
            )
            conn.commit()
        finally:
            conn.close()

    def queue_offline_operation(
        self,
        operation: str,
        entity_type: str,
        entity_id: int,
        payload: dict,
        device_id: str = "",
        offline_id: str = "",
    ) -> dict:
        result = {"success": False, "offline_id": offline_id, "error": None}
        if not offline_id:
            offline_id = f"{device_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT INTO offline_queue
                   (operation, entity_type, entity_id, payload, device_id,
                    offline_id, created_at, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')""",
                (
                    operation,
                    entity_type,
                    entity_id,
                    json.dumps(payload),
                    device_id,
                    offline_id,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            conn.commit()
            result["success"] = True
            result["offline_id"] = offline_id
        except Exception as e:
            result["error"] = str(e)
        finally:
            conn.close()
        return result

    def get_pending_operations(self, device_id: str = "") -> list[dict]:
        conn = self._get_conn()
        try:
            if device_id:
                rows = conn.execute(
                    "SELECT * FROM offline_queue WHERE status='pending' AND device_id=? ORDER BY id",
                    (device_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM offline_queue WHERE status='pending' ORDER BY id"
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def mark_synced(self, offline_id: str) -> bool:
        conn = self._get_conn()
        try:
            conn.execute(
                """UPDATE offline_queue SET status='synced',
                   synced_at=? WHERE offline_id=?""",
                (datetime.now().isoformat(timespec="seconds"), offline_id),
            )
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    def mark_failed(self, offline_id: str, error: str) -> bool:
        conn = self._get_conn()
        try:
            conn.execute(
                """UPDATE offline_queue SET status='failed',
                   error_message=error_message || ? || ' | ',
                   retry_count=retry_count+1 WHERE offline_id=?""",
                (error, offline_id),
            )
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    def get_sync_stats(self) -> dict:
        conn = self._get_conn()
        try:
            stats = {}
            for status in ["pending", "synced", "failed"]:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM offline_queue WHERE status=?",
                    (status,),
                ).fetchone()
                stats[status] = row["cnt"] if row else 0
            return stats
        finally:
            conn.close()


class SyncProtocolContract:
    """Contract for delta sync with conflict resolution."""

    @staticmethod
    def create_sync_request(
        entity_type: str,
        entity_id: int,
        action: str,
        payload: dict,
        client_timestamp: str,
        idempotency_key: str = "",
    ) -> dict:
        return {
            "contract_version": "1.0",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "payload": payload,
            "client_timestamp": client_timestamp,
            "idempotency_key": idempotency_key or f"{entity_type}_{entity_id}_{client_timestamp}",
        }

    @staticmethod
    def create_sync_response(
        success: bool,
        entity_type: str,
        entity_id: int,
        server_timestamp: str,
        conflict: bool = False,
        remote_data: dict | None = None,
    ) -> dict:
        return {
            "contract_version": "1.0",
            "success": success,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "server_timestamp": server_timestamp,
            "conflict": conflict,
            "remote_data": remote_data,
        }

    @staticmethod
    def create_conflict_resolution(
        strategy: str,
        local_data: dict,
        remote_data: dict,
        merged_data: dict,
    ) -> dict:
        return {
            "contract_version": "1.0",
            "strategy": strategy,
            "local_data": local_data,
            "remote_data": remote_data,
            "merged_data": merged_data,
            "resolved_at": datetime.now().isoformat(timespec="seconds"),
        }


class NotificationContract:
    """Contract for push notification readiness."""

    @staticmethod
    def create_notification(
        title: str,
        body: str,
        notification_type: str,
        entity_type: str = "",
        entity_id: int = 0,
        priority: str = "normal",
    ) -> dict:
        return {
            "contract_version": "1.0",
            "title": title,
            "body": body,
            "type": notification_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "priority": priority,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }

    @staticmethod
    def create_notification_batch(notifications: list[dict]) -> dict:
        return {
            "contract_version": "1.0",
            "count": len(notifications),
            "notifications": notifications,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }


class AttachmentContract:
    """Contract for mobile attachment handling."""

    @staticmethod
    def create_attachment_request(
        receipt_id: int,
        file_name: str,
        file_type: str,
        file_size: int,
        file_hash: str,
        category: str = "",
    ) -> dict:
        return {
            "contract_version": "1.0",
            "receipt_id": receipt_id,
            "file_name": file_name,
            "file_type": file_type,
            "file_size": file_size,
            "file_hash": file_hash,
            "category": category,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }

    @staticmethod
    def create_attachment_response(
        success: bool,
        attachment_id: int = 0,
        file_path: str = "",
        error: str = "",
    ) -> dict:
        return {
            "contract_version": "1.0",
            "success": success,
            "attachment_id": attachment_id,
            "file_path": file_path,
            "error": error,
        }


def get_mobile_readiness_report() -> dict:
    return {
        "contracts_ready": True,
        "offline_store_ready": True,
        "sync_protocol_ready": True,
        "notification_contract_ready": True,
        "attachment_contract_ready": True,
        "android_ready": False,
        "ios_ready": False,
        "tablet_ready": False,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
