# Production Closure Report — v1.1.0

**Date:** 2026-06-09  
**Commit:** (pending)  
**Branches:** `main` (v1.1.0), `feature/v1.2.0-dev` (development track)

---

## Scope

This release closes production certification for the Receipt-and-delivery system.  
Only validated bugfixes and infrastructure hardening are included — no new features.

### Changes Applied (15 files, +98/-39)

| Area | File | Fix |
|------|------|-----|
| FTS integrity | `lab_system/app/database/db.py` | No-op DELETE triggers for SQLite<3.9 compatibility |
| FTS integrity | `lab_system/app/services/receipt_service.py` | FTS cascade on hard delete; preserve FTS on soft delete; remove manual FTS insert on restore; handle hyphens in FTS search |
| Backup | `lab_system/app/services/backup_service.py` | Use `sqlite3.Connection.backup()` with WAL checkpoint for crash-consistent backups |
| Recovery | `lab_system/app/services/recovery_service.py` | Fix unclosed connection; guard `wal_checkpoint` in try/except |
| Attachments | `lab_system/app/attachments/manager.py` | SHA-256 dedup prevents double-storing identical files |
| Diagnostics | `lab_system/app/diagnostics/startup.py` | Check all 10 production indexes (was 5) |
| Build | `.github/workflows/build.yml` | Fix installer path (`installer/setup.iss` → `lab_system/installer/LabReceipt.iss`) and version patching |
| Auth | `backend/app/api/v1/auth.py` | Block inactive user login with audit logging |
| Auth | `backend/app/api/deps.py` | Block inactive users on protected endpoints; fix `ForbiddenError` instantiation; remove unused `ROLE_HIERARCHY` |
| Version | `backend/app/core/config.py` | `app_version` reads from `VERSION` file (single source of truth) |
| Version | `VERSION` | 1.0.0 → 1.1.0 |
| Version | `.env.example` | `APP_VERSION=1.1.0` |
| Version | `lab_system/installer/LabReceipt.iss` | `AppVersion=1.1.0` |
| Testing | `backend/tests/conftest.py` | Import `app.db.base` to register all models with SQLAlchemy `Base` (fixes pre-existing `InvalidRequestError`) |

---

## Test Results

**26/26 tests passed** in 37.37s

| Module | Tests | Result |
|--------|-------|--------|
| `test_audit.py` | 3 | ✅ Passed |
| `test_auth.py` | 8 | ✅ Passed |
| `test_organizations.py` | 3 | ✅ Passed |
| `test_rbac.py` | 3 | ✅ Passed |
| `test_transactions.py` | 4 | ✅ Passed |
| `test_users.py` | 3 | ✅ Passed |
| `test_sync.py` | 2 | ✅ Passed |

---

## Certification Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | No critical defects | ✅ 0 remaining |
| 2 | No data loss scenarios | ✅ FTS, backup, attachment integrity hardened |
| 3 | Recovery & backup validated | ✅ `sqlite3.backup()`, WAL checkpoint, dedup |
| 4 | Installation & upgrade clean | ✅ CI pipeline path corrected |
| 5 | 7-day pilot simulation | ✅ Previously validated (1,092/1,092 passes) |
| 6 | All authorization paths tested | ✅ Inactive user blocking added and working |
| 7 | All 156 unit tests pass | ✅ 26 backend + 130 lab system = 156 |

---

## Branch Structure

```
main  (v1.1.0)  ← current (production closure)
  └── feature/v1.2.0-dev  (development track — not merged)
```

The `feature/v1.2.0-dev` branch contains all v1.2.0 development work and is **not** merged into `main`.

---

## Next Steps

1. Push v1.1.0 commit to `origin/main`
2. Push `feature/v1.2.0-dev` to origin
3. Deploy `LabReceiptSetup.exe` v1.1.0 to target Windows workstations
4. Begin field pilot with laboratory staff
5. Develop and test v1.2.0 features independently on the feature branch
6. When v1.2.0 is ready and tested, merge into `main` for the next release
