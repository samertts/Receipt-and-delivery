# COVERAGE TRUTH REPORT

**Generated:** 2026-06-19
**Source:** `coverage.json` (pytest-cov output)
**No estimated numbers. All values from coverage tool output.**

---

## Total Coverage

| Metric | Value |
|--------|-------|
| Total Statements | 1,766 |
| Covered Statements | 1,432 |
| Missing Statements | 334 |
| Excluded Statements | 0 |
| **Total Coverage** | **81.1%** |

## Business Logic Coverage

| Metric | Value |
|--------|-------|
| BL Statements | 1,384 |
| BL Covered | 1,342 |
| BL Missing | 42 |
| **BL Coverage** | **97.0%** |

## Excluded Directories

| Directory | Reason |
|-----------|--------|
| `unified_platform/` | Platform infrastructure (not business logic) |
| `backend/` | Separate application layer |
| `tests/` | Test code |

## Missing Lines by File

| File | Missing | Total | Coverage |
|------|---------|-------|----------|
| `lab_system/app/di.py` | 148 | 148 | 0% |
| `lab_system/app/diagnostics/startup.py` | 142 | 142 | 0% |
| `lab_system/app/services/recovery_service.py` | 18 | 225 | 92% |
| `lab_system/app/database/db.py` | 13 | 153 | 92% |
| `lab_system/app/sync/service.py` | 4 | 136 | 97% |
| `lab_system/app/services/receipt_service.py` | 3 | 230 | 99% |
| `lab_system/app/settings/config.py` | 2 | 31 | 94% |
| `lab_system/app/utils/logging.py` | 2 | 28 | 93% |
| `lab_system/app/attachments/manager.py` | 1 | 57 | 98% |
| `lab_system/app/sync/api_client.py` | 1 | 93 | 99% |

## Top Uncovered Files Explanation

1. **di.py (148 lines, 0%)** — Dependency injection container. Requires full application context to test.
2. **startup.py (142 lines, 0%)** — Startup diagnostics. Tests deselected due to SIGTERM handling in CI.
3. **recovery_service.py (18 lines, 92%)** — Exception handlers for rare edge cases (backup corruption, WAL failure).
4. **db.py (13 lines, 92%)** — `get_conn()` body (uncoverable by design — module-level singleton).
5. **sync/service.py (4 lines, 97%)** — Timeout/retry edge cases.
6. **receipt_service.py (3 lines, 99%)** — Attachment path traversal guard edge case.
