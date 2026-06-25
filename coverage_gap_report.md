# COVERAGE GAP REPORT — V5.0

**Date:** 2026-06-19
**Commit:** `249de5f`
**Test Command:** `pytest --cov=lab_system --cov=backend --cov-report=json`

---

## EXECUTIVE SUMMARY

| Category | Total | Covered | Missed | Coverage | Target | Gap |
|----------|-------|---------|--------|----------|--------|-----|
| Business Logic | 1,207 | 1,031 | 176 | **85.4%** | 95% | -9.6% |
| Infrastructure | 269 | 239 | 30 | **88.8%** | 95% | -6.2% |
| UI | 290 | 108 | 182 | **37.2%** | Exempt | — |
| **OVERALL** | **1,766** | **1,378** | **388** | **78.0%** | 90% | -12.0% |

---

## BUSINESS LOGIC — COVERAGE GAPS (sorted by missed lines)

| File | Total | Covered | Missed | Coverage | Priority |
|------|-------|---------|--------|----------|----------|
| services/recovery_service.py | 225 | 172 | 53 | 76.4% | **CRITICAL** |
| sync/service.py | 136 | 113 | 23 | 83.1% | **CRITICAL** |
| services/desktop_settings_service.py | 22 | 0 | 22 | 0.0% | HIGH |
| services/receipt_service.py | 230 | 208 | 22 | 90.4% | **CRITICAL** |
| services/dashboard_service.py | 17 | 0 | 17 | 0.0% | HIGH |
| database/repository.py | 25 | 15 | 10 | 60.0% | HIGH |
| services/auth_service.py | 65 | 57 | 8 | 87.7% | **CRITICAL** |
| services/backup_listing_service.py | 8 | 0 | 8 | 0.0% | MEDIUM |
| services/desktop_audit_service.py | 8 | 0 | 8 | 0.0% | MEDIUM |

**Total Business Logic Missed: 176 lines**

---

## INFRASTRUCTURE — COVERAGE GAPS

| File | Total | Covered | Missed | Coverage | Priority |
|------|-------|---------|--------|----------|----------|
| database/db.py | 153 | 127 | 26 | 83.0% | **CRITICAL** |
| settings/config.py | 31 | 29 | 2 | 93.5% | MEDIUM |
| utils/logging.py | 28 | 26 | 2 | 92.9% | MEDIUM |

**Total Infrastructure Missed: 30 lines**

---

## UI MODULES (Exempt from coverage target)

| File | Total | Covered | Missed | Coverage |
|------|-------|---------|--------|----------|
| di.py | 148 | 0 | 148 | 0.0% |
| diagnostics/startup.py | 142 | 108 | 34 | 76.1% |

**Total UI Missed: 182 lines**

---

## PATHS TO 95% BUSINESS LOGIC COVERAGE

**Current:** 1,031 / 1,207 = 85.4%
**Target:** 1,207 × 0.95 = 1,147 covered
**Need:** 116 additional lines covered

### Highest Impact Fixes:
1. **recovery_service.py** (+53 lines) → Would reach 100%
2. **sync/service.py** (+23 lines) → Would reach 100%
3. **receipt_service.py** (+22 lines) → Would reach 100%
4. **repository.py** (+10 lines) → Would reach 100%
5. **auth_service.py** (+8 lines) → Would reach 100%

**Total if all fixed: 1,031 + 116 = 1,147 = 95.0%**
