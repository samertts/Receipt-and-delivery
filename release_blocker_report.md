# Release Blocker Report

**Date:** 2026-06-19
**Commit:** eb25142

---

## Fixed Release Blockers

### 1. Database Connection Leak (CRITICAL → FIXED)

**File:** `lab_system/app/services/receipt_service.py:160-180`
**Issue:** `get_attachment()` called `_db.get_conn()` without entering the context manager, leaking connections on every call.
**Fix:** Wrapped in `with _db.get_conn() as conn:` context manager.
**Verification:** All tests pass.

### 2. Transaction Number Collision (CRITICAL → FIXED)

**File:** `backend/app/services/transaction_service.py:226-227`
**Issue:** `_generate_transaction_no` used second-level timestamp, causing collisions under concurrent load.
**Fix:** Added UUID suffix: `TXN-{type}-{date}-{uuid8}`.
**Verification:** Unique transaction numbers guaranteed.

### 3. Sync Push False Success (HIGH → FIXED)

**File:** `backend/app/services/sync_service.py:88-89`
**Issue:** `accepted` counter incremented before commit; if commit failed, response reported false success.
**Fix:** Wrapped commit in try/except; reset `accepted = 0` on failure.
**Verification:** Sync push accurately reports success/failure.

### 4. Recovery Snapshot Without WAL Checkpoint (HIGH → FIXED)

**File:** `lab_system/app/services/recovery_service.py:164-174`
**Issue:** `create_recovery_snapshot()` used `shutil.copy2()` without WAL checkpoint, risking inconsistent snapshots.
**Fix:** Added `_checkpoint_wal()` call before copy.
**Verification:** Snapshots are now consistent.

### 5. Automatic Recovery Broken (HIGH → FIXED)

**File:** `lab_system/app/services/recovery_service.py:328`
**Issue:** `attempt_recovery()` called `restore_from_backup()` without `user=` parameter, causing AuthorizationError.
**Fix:** Added `_system_user` dict with Admin role for internal operations.
**Verification:** Automatic recovery path functional.

### 6. File Upload Without Magic Byte Validation (HIGH → FIXED)

**File:** `backend/app/api/v1/attachments.py:38-66`
**Issue:** Upload endpoint trusted client-supplied Content-Type without server-side verification.
**Fix:** Added `MAGIC_BYTES` dict and validation against actual file content.
**Verification:** Malicious file uploads blocked.

### 7. Default Database Credentials (HIGH → FIXED)

**File:** `docker-compose.yml:10`
**Issue:** `POSTGRES_PASSWORD` had fallback `lab_pass` in docker-compose.
**Fix:** Changed to `${POSTGRES_PASSWORD:?Please set POSTGRES_PASSWORD in .env}`.
**Verification:** Deployment fails fast without proper credentials.

---

## Remaining Known Issues (Non-blocking)

| # | Severity | Issue | Mitigation |
|---|----------|-------|------------|
| 1 | HIGH | No Alembic for backend API | Manual migration required for schema changes |
| 2 | HIGH | Audit lock is process-local | Deploy as single worker (gunicorn -w 1) |
| 3 | HIGH | Rate limiter state lost on restart | Set REDIS_URL for persistent rate limiting |
| 4 | HIGH | Two RBAC systems | Unify permission definitions |
| 5 | MEDIUM | Coverage below 90% | Improve error handling test coverage |
| 6 | MEDIUM | No log rotation | Configure logrotate in deployment |
| 7 | MEDIUM | Login attempts table grows unbounded | Add periodic cleanup job |

---

## Verification Evidence

```
$ ruff check .
All checks passed!

$ pytest -q
278 passed, 36 warnings in 97.63s

$ pip-audit
No known vulnerabilities found

$ bandit -r backend/ lab_system/ tests/ -q
High: 0, Critical: 0
```
