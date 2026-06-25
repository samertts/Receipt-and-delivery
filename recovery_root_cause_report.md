# RECOVERY SERVICE ROOT-CAUSE REPORT

**Date:** 2026-06-24
**Status:** RESOLVED

---

## Defect Summary

**Module:** `lab_system/app/services/recovery_service.py`
**Function:** `restore_from_backup()`, `_checkpoint_wal()`, `create_recovery_snapshot()`, `detect_corruption()`, `attempt_recovery()`
**Severity:** HIGH — Production data integrity risk
**Classification:** Import-Time Path Resolution (Time-of-Check vs Time-of-Use)

---

## Root Cause

`recovery_service.py` resolved `DB_PATH`, `BACKUP_DIR`, and `SNAPSHOT_DIR` as **module-level constants** at import time:

```python
# BEFORE (defective)
from lab_system.app.settings.config import DB_PATH, STORAGE_DIR

BACKUP_DIR = STORAGE_DIR / "backups"    # Resolved at import time
SNAPSHOT_DIR = STORAGE_DIR / "snapshots" # Resolved at import time
```

These constants were used directly in all recovery functions:
- `restore_from_backup()` line 107: `BACKUP_DIR` (import-time)
- `restore_from_backup()` line 119: `DB_PATH` (import-time)
- `_checkpoint_wal()` line 96: `DB_PATH` (import-time)
- `create_recovery_snapshot()` lines 167, 173: `SNAPSHOT_DIR`, `DB_PATH` (import-time)
- `detect_corruption()` lines 290, 297: `DB_PATH` (import-time)
- `attempt_recovery()` line 314: `DB_PATH` (import-time)

Meanwhile, `get_conn()` in `db.py` uses `CONFIG.db_path` (runtime-resolved), creating an inconsistency:

```python
@contextmanager
def get_conn():
    conn = sqlite3.connect(CONFIG.db_path)  # Runtime-resolved
```

---

## Failure Mode

When `CONFIG.db_path` or `CONFIG.storage_dir` changes at runtime (e.g., via `object.__setattr__()`):
1. `restore_from_backup()` copies backup to **import-time** `DB_PATH`
2. `rebuild_fts()` connects to **runtime** `CONFIG.db_path`
3. If these paths differ, FTS operates on a different database file
4. Post-restore verification may pass (if import-time path exists) but data integrity is compromised

---

## Affected Execution Paths

| Function | Line | Import-Time Path Used | Runtime Path Available |
|----------|------|----------------------|----------------------|
| `restore_from_backup()` | 107 | `BACKUP_DIR` | `_get_backup_dir()` |
| `restore_from_backup()` | 119 | `DB_PATH` | `_get_db_path()` |
| `_checkpoint_wal()` | 96 | `DB_PATH` | `_get_db_path()` |
| `create_recovery_snapshot()` | 167 | `SNAPSHOT_DIR` | `_get_snapshot_dir()` |
| `create_recovery_snapshot()` | 173 | `DB_PATH` | `_get_db_path()` |
| `list_backups()` | 65 | `BACKUP_DIR` | `_get_backup_dir()` |
| `list_snapshots()` | 181 | `SNAPSHOT_DIR` | `_get_snapshot_dir()` |
| `detect_corruption()` | 290 | `DB_PATH` | `_get_db_path()` |
| `detect_corruption()` | 297 | `DB_PATH` | `_get_db_path()` |
| `attempt_recovery()` | 314 | `DB_PATH` | `_get_db_path()` |

---

## Evidence

Test output with DEBUG logging confirmed runtime path divergence:

```
restore_from_backup: backup_path=/tmp/.../backups/good.db, db_path=/tmp/.../alt_db/test.db
create_recovery_snapshot: snapshot_dir=/tmp/.../snapshots, db_path=/tmp/.../alt_db/test.db
_checkpoint_wal: db_path=/tmp/.../alt_db/test.db
restore_from_backup: copying backup to /tmp/.../alt_db/test.db
restore_from_backup: SUCCESS restored to /tmp/.../alt_db/test.db
```

All paths resolve to runtime `CONFIG` values, not import-time constants.

---

## Impact

- **Data Integrity:** Critical — restore could write to wrong path
- **FTS Rebuild:** Could operate on stale database
- **Snapshot Creation:** Could snapshot wrong database
- **Corruption Detection:** Could check wrong database

---

## Conclusion

**No hardcoded path assumptions should exist.** All path resolution must occur at runtime via `CONFIG` object to support dynamic reconfiguration.
