"""
Generate a large test dataset for performance benchmarking.

Creates:
  - 500 organizations
  - 50 users
  - 10,000 receipts (spanning 5 years, 2019–2024)
  - ~100,000 receipt_items

Usage:
    python scripts/generate_large_dataset.py [db_path]
"""

import random
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lab_system.app.database import db as _db
from lab_system.app.auth.security import hash_password

NUM_ORGS = 500
NUM_USERS = 50
NUM_RECEIPTS = 10_000
# items will be ~10 per receipt

GOVERNORATES = [
    "بغداد", "نينوى", "البصرة", "أربيل", "كركوك", "النجف", "كربلاء",
    "السليمانية", "دهوك", "بابل", "ميسان", "القادسية", "واسط",
    "صلاح الدين", "الأنبار", "المثنى", "ذي قار", "حلبجة",
]

ORG_TYPES = [
    "Public Health Laboratory", "Hospital Laboratory", "Private Laboratory",
    "Blood Bank", "Research Center",
]

STATUSES = ["Draft", "Approved", "Approved", "Approved", "Rejected", "Archived", "Cancelled"]
USER_ROLES = ["Admin", "Supervisor", "User", "Auditor"]

IRAQI_NAMES = [
    "أحمد", "علي", "محمد", "حسن", "حسين", "مصطفى", "عبدالله", "كريم",
    "جعفر", "مهدي", "هادي", "عباس", "نور", "زهراء", "فاطمة", "مريم",
    "سارة", "رقية", "زينب", "خديجة",
]

SAMPLE_NAMES = [
    ("دم كامل", "Hematology"),
    ("مصل", "Serology"),
    ("بول", "Urinalysis"),
    ("مسحة أنف", "Microbiology"),
    ("بلغم", "Microbiology"),
    ("براز", "Parasitology"),
    ("سائل نخاعي", "CSF Analysis"),
    ("عينة نسيج", "Histopathology"),
    ("لعاب", "Molecular"),
    ("دم وريدي", "Biochemistry"),
]

TX_TYPES = ["استلام", "تسليم", "إعادة", "تحويل داخلي", "إعارة"]


def _ts(start: datetime, end: datetime) -> str:
    delta = end - start
    offset = random.random() * delta.total_seconds()
    return (start + timedelta(seconds=offset)).isoformat(timespec="seconds")


def generate(db_path: str) -> dict:
    start = time.time()
    random.seed(42)

    db_path = str(Path(db_path).resolve())

    print(f"[1/6] Creating database at {db_path} ...")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.executescript(_db.SCHEMA)
    cur = conn.cursor()

    print(f"[2/6] Inserting {NUM_ORGS} organizations ...")
    org_ids = []
    for i in range(NUM_ORGS):
        name = f"مختبر {i+1:03d}"
        code = f"LAB-{i+1:05d}"
        org_type = random.choice(ORG_TYPES)
        gov = random.choice(GOVERNORATES)
        cur.execute(
            "INSERT INTO organizations(name, code, org_type, governorate, address, phone, status) VALUES(?,?,?,?,?,?,'Active')",
            (name, code, org_type, gov, gov, f"+964{random.randint(7000000000, 7999999999)}"),
        )
        org_ids.append(cur.lastrowid)
    conn.commit()

    print("[3/6] Inserting transaction_types & sample_types ...")
    for name in TX_TYPES:
        cur.execute("INSERT OR IGNORE INTO transaction_types(name) VALUES(?)", (name,))
    tx_type_ids = [r["id"] for r in cur.execute("SELECT id FROM transaction_types").fetchall()]
    for name, cat in SAMPLE_NAMES:
        cur.execute(
            "INSERT OR IGNORE INTO sample_types(name, category, status) VALUES(?,?,'Active')",
            (name, cat),
        )
    sample_type_ids = [r["id"] for r in cur.execute("SELECT id FROM sample_types").fetchall()]
    conn.commit()

    print(f"[4/6] Inserting {NUM_USERS} users ...")
    user_ids = []
    for i in range(NUM_USERS):
        full_name = f"{random.choice(IRAQI_NAMES)} {random.choice(IRAQI_NAMES)}"
        username = f"user_{i+1:03d}"
        role = random.choice(USER_ROLES)
        inst = random.choice(org_ids)
        now = datetime.now().isoformat(timespec="seconds")
        cur.execute(
            "INSERT INTO users(full_name, username, password_hash, role, institution_id, status, password_changed_at) VALUES(?,?,?,?,?,?,?)",
            (full_name, username, hash_password("Test@123"), role, inst, "Active", now),
        )
        user_ids.append(cur.lastrowid)
    conn.commit()

    date_start = datetime(2019, 1, 1, 0, 0, 0)
    date_end = datetime(2024, 1, 1, 0, 0, 0)

    print(f"[5/6] Inserting {NUM_RECEIPTS} receipts and items ...")
    receipt_ids = []
    items_count = 0
    batch_size = 500
    for batch_start in range(0, NUM_RECEIPTS, batch_size):
        batch_end = min(batch_start + batch_size, NUM_RECEIPTS)
        items_batch = []
        for r in range(batch_start, batch_end):
            created = _ts(date_start, date_end)
            receipt_no = f"REC-{r+1:06d}"
            tx_id = random.choice(tx_type_ids)
            snd = random.choice(org_ids)
            rcv = random.choice(org_ids)
            sname = random.choice(IRAQI_NAMES)
            rname = random.choice(IRAQI_NAMES)
            st = random.choice(STATUSES)
            cb = random.choice(user_ids)
            cur.execute(
                "INSERT INTO receipts(receipt_no, tx_type_id, sender_org_id, receiver_org_id, sender_name, receiver_name, created_at, status, created_by) VALUES(?,?,?,?,?,?,?,?,?)",
                (receipt_no, tx_id, snd, rcv, sname, rname, created, st, cb),
            )
            rid = cur.lastrowid
            receipt_ids.append(rid)
            num_items = random.randint(5, 15)
            for _ in range(num_items):
                st_id = random.choice(sample_type_ids)
                total = random.randint(10, 500)
                valid = random.randint(int(total * 0.7), total)
                damaged = random.randint(0, max(0, total - valid))
                rejected = random.randint(0, max(0, total - valid - damaged))
                non_conf = random.randint(0, max(0, total - valid - damaged - rejected))
                items_batch.append((rid, st_id, total, valid, damaged, rejected, non_conf))
                items_count += 1
        cur.executemany(
            "INSERT INTO receipt_items(receipt_id, sample_type_id, total_count, valid_count, damaged_count, rejected_count, non_conforming_count) VALUES(?,?,?,?,?,?,?)",
            items_batch,
        )
        conn.commit()
        print(f"   receipts {batch_start+1}–{batch_end} / {NUM_RECEIPTS}  (items: ~{items_count})")

    print("[6/6] Rebuilding FTS indexes ...")
    cur.execute("DELETE FROM receipts_fts;")
    cur.execute(
        "INSERT INTO receipts_fts(rowid, receipt_no, sender_name, receiver_name) SELECT id, receipt_no, sender_name, receiver_name FROM receipts WHERE deleted_at IS NULL OR deleted_at = ''"
    )
    cur.execute("DELETE FROM organizations_fts;")
    cur.execute(
        "INSERT INTO organizations_fts(rowid, name, code) SELECT id, name, code FROM organizations"
    )
    conn.commit()
    conn.close()

    elapsed = time.time() - start
    return {
        "elapsed_seconds": round(elapsed, 1),
        "orgs": NUM_ORGS,
        "users": NUM_USERS,
        "receipts": NUM_RECEIPTS,
        "items": items_count,
        "db_path": db_path,
    }


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/lab_large_dataset.db"
    result = generate(db_path)
    print(f"\nDone! Generated {result['receipts']} receipts, {result['items']} items in {result['elapsed_seconds']}s")
    print(f"Database: {result['db_path']}")
