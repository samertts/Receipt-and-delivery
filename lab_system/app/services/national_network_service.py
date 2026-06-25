"""
National Network Service — Multi-Laboratory Federation

Provides laboratory registry, node registry, referral framework,
federation contracts, and national sample identifier.
"""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from lab_system.app.settings.config import CONFIG


class LabType:
    PRIMARY_HEALTH = "primary_health"
    HOSPITAL = "hospital"
    PUBLIC_HEALTH = "public_health"
    REFERENCE = "reference"
    ALL_TYPES = [PRIMARY_HEALTH, HOSPITAL, PUBLIC_HEALTH, REFERENCE]


class ReferralStatus:
    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    COMPLETED = "completed"
    REJECTED = "rejected"
    ALL_STATUSES = [PENDING, ACCEPTED, IN_TRANSIT, RECEIVED, COMPLETED, REJECTED]


class NationalNetworkService:
    """Multi-laboratory federation and national sample tracking."""

    def __init__(self, db_path: str | Path | None = None):
        self._db_path = str(db_path or CONFIG.db_path)

    def _get_conn(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def initialize_schema(self):
        conn = self._get_conn()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS laboratories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    code TEXT UNIQUE NOT NULL,
                    lab_type TEXT NOT NULL CHECK(lab_type IN (
                        'primary_health','hospital','public_health','reference'
                    )),
                    governorate TEXT DEFAULT '',
                    address TEXT DEFAULT '',
                    phone TEXT DEFAULT '',
                    email TEXT DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active','Inactive')),
                    registered_at TEXT NOT NULL,
                    metadata_json TEXT DEFAULT '{}'
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS laboratory_nodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lab_id INTEGER NOT NULL,
                    node_id TEXT UNIQUE NOT NULL,
                    node_name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'online' CHECK(status IN ('online','offline','degraded')),
                    last_heartbeat TEXT DEFAULT '',
                    ip_address TEXT DEFAULT '',
                    version TEXT DEFAULT '',
                    registered_at TEXT NOT NULL,
                    FOREIGN KEY(lab_id) REFERENCES laboratories(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referral_no TEXT UNIQUE NOT NULL,
                    sample_id INTEGER NOT NULL,
                    nsid TEXT DEFAULT '',
                    from_lab_id INTEGER NOT NULL,
                    to_lab_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN (
                        'pending','accepted','in_transit','received','completed','rejected'
                    )),
                    priority TEXT NOT NULL DEFAULT 'normal' CHECK(priority IN ('low','normal','high','urgent')),
                    created_by INTEGER REFERENCES users(id),
                    created_at TEXT NOT NULL,
                    accepted_at TEXT DEFAULT '',
                    in_transit_at TEXT DEFAULT '',
                    received_at TEXT DEFAULT '',
                    completed_at TEXT DEFAULT '',
                    rejected_at TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    metadata_json TEXT DEFAULT '{}',
                    FOREIGN KEY(from_lab_id) REFERENCES laboratories(id),
                    FOREIGN KEY(to_lab_id) REFERENCES laboratories(id)
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_referrals_status ON referrals(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_referrals_from_lab ON referrals(from_lab_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_referrals_to_lab ON referrals(to_lab_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_referrals_nsid ON referrals(nsid)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_lab_nodes_status ON laboratory_nodes(status)"
            )
            conn.commit()
        finally:
            conn.close()

    def generate_nsid(self, lab_code: str, sample_seq: int) -> str:
        ts = datetime.now().strftime("%Y%m%d")
        return f"NSID-{lab_code}-{ts}-{sample_seq:06d}"

    def generate_referral_no(self, from_lab_code: str) -> str:
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        short_id = uuid.uuid4().hex[:6].upper()
        return f"REF-{from_lab_code}-{ts}-{short_id}"

    def register_laboratory(
        self,
        name: str,
        code: str,
        lab_type: str,
        governorate: str = "",
        address: str = "",
        phone: str = "",
        email: str = "",
        metadata: dict | None = None,
    ) -> dict:
        result = {"success": False, "error": None, "lab_id": None}
        if lab_type not in LabType.ALL_TYPES:
            result["error"] = f"Invalid lab_type: {lab_type}. Valid: {LabType.ALL_TYPES}"
            return result
        import json
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                """INSERT INTO laboratories
                   (name, code, lab_type, governorate, address, phone, email,
                    status, registered_at, metadata_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'Active', ?, ?)""",
                (
                    name, code, lab_type, governorate, address, phone, email,
                    datetime.now().isoformat(timespec="seconds"),
                    json.dumps(metadata or {}),
                ),
            )
            conn.commit()
            result["success"] = True
            result["lab_id"] = cursor.lastrowid
        except sqlite3.IntegrityError:
            result["error"] = f"Laboratory with code '{code}' already exists"
        except Exception as e:
            result["error"] = str(e)
        finally:
            conn.close()
        return result

    def get_laboratory(self, lab_id: int) -> dict | None:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM laboratories WHERE id=?", (lab_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_laboratories(self, lab_type: str = "", status: str = "") -> list[dict]:
        conn = self._get_conn()
        try:
            query = "SELECT * FROM laboratories WHERE 1=1"
            params = []
            if lab_type:
                query += " AND lab_type=?"
                params.append(lab_type)
            if status:
                query += " AND status=?"
                params.append(status)
            query += " ORDER BY name"
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def discover_laboratories(self, lab_type: str = "", governorate: str = "") -> list[dict]:
        conn = self._get_conn()
        try:
            query = "SELECT * FROM laboratories WHERE status='Active'"
            params = []
            if lab_type:
                query += " AND lab_type=?"
                params.append(lab_type)
            if governorate:
                query += " AND governorate=?"
                params.append(governorate)
            query += " ORDER BY name"
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def register_node(
        self,
        lab_id: int,
        node_name: str,
        ip_address: str = "",
        version: str = "",
    ) -> dict:
        result = {"success": False, "error": None, "node_id": None}
        node_id = f"NODE-{lab_id}-{uuid.uuid4().hex[:8].upper()}"
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT INTO laboratory_nodes
                   (lab_id, node_id, node_name, status, last_heartbeat,
                    ip_address, version, registered_at)
                   VALUES (?, ?, ?, 'online', ?, ?, ?, ?)""",
                (
                    lab_id, node_id, node_name,
                    datetime.now().isoformat(timespec="seconds"),
                    ip_address, version,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            conn.commit()
            result["success"] = True
            result["node_id"] = node_id
        except Exception as e:
            result["error"] = str(e)
        finally:
            conn.close()
        return result

    def update_node_heartbeat(self, node_id: str, status: str = "online") -> bool:
        conn = self._get_conn()
        try:
            conn.execute(
                """UPDATE laboratory_nodes SET status=?,
                   last_heartbeat=? WHERE node_id=?""",
                (status, datetime.now().isoformat(timespec="seconds"), node_id),
            )
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    def get_node_health(self) -> list[dict]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT n.*, l.name as lab_name, l.code as lab_code
                   FROM laboratory_nodes n
                   JOIN laboratories l ON n.lab_id = l.id
                   ORDER BY l.name"""
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def create_referral(
        self,
        sample_id: int,
        from_lab_id: int,
        to_lab_id: int,
        user_id: int,
        nsid: str = "",
        priority: str = "normal",
        notes: str = "",
    ) -> dict:
        result = {"success": False, "error": None, "referral_no": None}
        if priority not in ["low", "normal", "high", "urgent"]:
            result["error"] = f"Invalid priority: {priority}"
            return result
        from_lab = self.get_laboratory(from_lab_id)
        if not from_lab:
            result["error"] = f"Source lab {from_lab_id} not found"
            return result
        to_lab = self.get_laboratory(to_lab_id)
        if not to_lab:
            result["error"] = f"Destination lab {to_lab_id} not found"
            return result
        referral_no = self.generate_referral_no(from_lab["code"])
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT INTO referrals
                   (referral_no, sample_id, nsid, from_lab_id, to_lab_id,
                    status, priority, created_by, created_at, notes)
                   VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)""",
                (
                    referral_no, sample_id, nsid,
                    from_lab_id, to_lab_id, priority, user_id,
                    datetime.now().isoformat(timespec="seconds"), notes,
                ),
            )
            conn.commit()
            result["success"] = True
            result["referral_no"] = referral_no
        except Exception as e:
            result["error"] = str(e)
        finally:
            conn.close()
        return result

    def update_referral_status(self, referral_no: str, new_status: str) -> dict:
        result = {"success": False, "error": None}
        if new_status not in ReferralStatus.ALL_STATUSES:
            result["error"] = f"Invalid status: {new_status}"
            return result
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT status FROM referrals WHERE referral_no=?",
                (referral_no,),
            ).fetchone()
            if not row:
                result["error"] = f"Referral {referral_no} not found"
                return result
            now = datetime.now().isoformat(timespec="seconds")
            timestamp_field = f"{new_status}_at" if new_status != "pending" else ""
            conn.execute(
                f"UPDATE referrals SET status=?, {timestamp_field}=? WHERE referral_no=?",
                (new_status, now, referral_no),
            )
            conn.commit()
            result["success"] = True
        except Exception as e:
            result["error"] = str(e)
        finally:
            conn.close()
        return result

    def get_referral(self, referral_no: str) -> dict | None:
        conn = self._get_conn()
        try:
            row = conn.execute(
                """SELECT r.*, fl.name as from_lab_name, fl.code as from_lab_code,
                          tl.name as to_lab_name, tl.code as to_lab_code
                   FROM referrals r
                   JOIN laboratories fl ON r.from_lab_id = fl.id
                   JOIN laboratories tl ON r.to_lab_id = tl.id
                   WHERE r.referral_no=?""",
                (referral_no,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_referrals(self, status: str = "", lab_id: int = 0) -> list[dict]:
        conn = self._get_conn()
        try:
            query = """
                SELECT r.*, fl.name as from_lab_name, tl.name as to_lab_name
                FROM referrals r
                JOIN laboratories fl ON r.from_lab_id = fl.id
                JOIN laboratories tl ON r.to_lab_id = tl.id
                WHERE 1=1
            """
            params = []
            if status:
                query += " AND r.status=?"
                params.append(status)
            if lab_id:
                query += " AND (r.from_lab_id=? OR r.to_lab_id=?)"
                params.extend([lab_id, lab_id])
            query += " ORDER BY r.created_at DESC"
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_network_statistics(self) -> dict:
        conn = self._get_conn()
        try:
            stats = {}
            row = conn.execute("SELECT COUNT(*) as cnt FROM laboratories WHERE status='Active'").fetchone()
            stats["active_laboratories"] = row["cnt"] if row else 0
            row = conn.execute("SELECT COUNT(*) as cnt FROM laboratories").fetchone()
            stats["total_laboratories"] = row["cnt"] if row else 0
            for lab_type in LabType.ALL_TYPES:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM laboratories WHERE lab_type=? AND status='Active'",
                    (lab_type,),
                ).fetchone()
                stats[f"{lab_type}_labs"] = row["cnt"] if row else 0
            row = conn.execute("SELECT COUNT(*) as cnt FROM laboratory_nodes").fetchone()
            stats["total_nodes"] = row["cnt"] if row else 0
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM laboratory_nodes WHERE status='online'"
            ).fetchone()
            stats["online_nodes"] = row["cnt"] if row else 0
            row = conn.execute("SELECT COUNT(*) as cnt FROM referrals").fetchone()
            stats["total_referrals"] = row["cnt"] if row else 0
            for status in ReferralStatus.ALL_STATUSES:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM referrals WHERE status=?",
                    (status,),
                ).fetchone()
                stats[f"referrals_{status}"] = row["cnt"] if row else 0
            return stats
        finally:
            conn.close()

    def get_national_readiness_report(self) -> dict:
        stats = self.get_network_statistics()
        readiness_score = 0
        if stats["total_laboratories"] > 0:
            readiness_score += 25
        if stats["total_nodes"] > 0:
            readiness_score += 25
        if stats["total_referrals"] > 0:
            readiness_score += 25
        if stats["active_laboratories"] >= 2:
            readiness_score += 25
        return {
            "readiness_score": readiness_score,
            "statistics": stats,
            "federation_ready": stats["total_laboratories"] > 0,
            "referral_ready": stats["total_referrals"] > 0 or stats["total_laboratories"] >= 2,
            "node_registry_ready": stats["total_nodes"] > 0,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
