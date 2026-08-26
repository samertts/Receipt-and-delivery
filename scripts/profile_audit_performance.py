from __future__ import annotations

import json
import statistics
import tempfile
import time
from dataclasses import replace
from pathlib import Path


def measure(fn, repetitions: int = 5) -> list[float]:
    values = []
    for _ in range(repetitions):
        start = time.perf_counter()
        fn()
        values.append((time.perf_counter() - start) * 1000)
    return values


def summarize(values: list[float]) -> dict[str, float]:
    return {
        "min_ms": round(min(values), 3),
        "median_ms": round(statistics.median(values), 3),
        "p95_ms": round(sorted(values)[min(len(values) - 1, int(len(values) * 0.95))], 3),
        "max_ms": round(max(values), 3),
    }


def main() -> None:
    from lab_system.app.database import db as database
    from lab_system.app.diagnostics import startup

    with tempfile.TemporaryDirectory(prefix="receipt_audit_profile_") as tmp:
        root = Path(tmp)
        storage = root / "storage"
        config = replace(
            database.CONFIG,
            storage_dir=storage,
            db_path=storage / "database" / "lab_system.db",
        )
        database.CONFIG = config
        startup.CONFIG = config
        config.db_path.parent.mkdir(parents=True, exist_ok=True)
        startup.STORAGE_DIR = storage

        database.init_db()
        database.init_db()  # warm path after schema is current

        startup_timings = {
            "self_repair": summarize(measure(startup.self_repair)),
            "init_db_warm": summarize(measure(database.init_db)),
            "run_all_checks": summarize(measure(startup.run_all_checks)),
            "check_integrity": summarize(measure(startup.check_integrity)),
            "check_indexes": summarize(measure(startup.check_indexes)),
        }

        with database.get_conn() as conn:
            conn.executemany(
                "INSERT INTO organizations(name,code) VALUES(?,?)",
                [(f"Organization {i}", f"ORG-{i}") for i in (1, 2)],
            )
            conn.execute("INSERT INTO transaction_types(name) VALUES('Receipt')")
            conn.execute(
                "INSERT INTO users(full_name,username,password_hash,role,status) VALUES(?,?,?,?,?)",
                ("Benchmark User", "benchmark", "not-a-password", "Admin", "Active"),
            )
            conn.executemany(
                """INSERT INTO receipts(
                    receipt_no,tx_type_id,sender_org_id,receiver_org_id,
                    sender_name,receiver_name,created_at,status,created_by
                ) VALUES(?,?,?,?,?,?,?,?,?)""",
                [
                    (
                        f"LAB-{i:06d}",
                        1,
                        1,
                        2,
                        f"Sender {i}",
                        f"Receiver {i}",
                        "2026-08-26T00:00:00",
                        "Draft",
                        1,
                    )
                    for i in range(1, 1001)
                ],
            )
            conn.execute("INSERT INTO receipts_fts(receipts_fts) VALUES('rebuild')")

        def fts_search() -> None:
            with database.get_conn() as conn:
                conn.execute(
                    "SELECT rowid FROM receipts_fts WHERE receipts_fts MATCH ? LIMIT 50",
                    ("Sender 0500",),
                ).fetchall()

        def indexed_status() -> None:
            with database.get_conn() as conn:
                conn.execute(
                    "SELECT id FROM receipts WHERE status=? ORDER BY created_at DESC LIMIT 50",
                    ("Draft",),
                ).fetchall()

        performance = {
            "dataset": {"receipts": 1000},
            "local_fts_search": summarize(measure(fts_search, repetitions=20)),
            "indexed_status_query": summarize(measure(indexed_status, repetitions=20)),
        }

        output = {
            "environment": {"python": "runtime", "database": "SQLite", "network": "disabled"},
            "startup": startup_timings,
            "database_queries": performance,
            "notes": [
                "Measurements are isolated local-process timings, not a production SLO claim.",
                "The benchmark uses a controlled 1,000-receipt dataset and excludes Qt painting and login UI.",
            ],
        }
        output_path = Path(__file__).parents[1] / "docs" / "performance" / "startup_profile.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
