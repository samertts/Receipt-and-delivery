# Remaining Gap Report

**Project:** Receipt-and-delivery  
**Branch:** feature/v1.2.0-ui-modernization-phase2  
**Date:** 2026-06-15  
**Status:** **1 remaining blocker** for Release Candidate promotion  

---

## Gap 1: Architecture (87 / 90, need +3)

### Root Cause
The codebase lacks a formal dependency injection framework. Services are instantiated manually and wired together in UI constructors and `app.py:run()`. Caching layer is absent. Some modules remain tightly coupled (e.g., `receipt_service` directly imports `db` module).

### Required Changes

| Change | Architecture Impact | Effort | Priority |
|--------|-------------------|--------|----------|
| Add DI container for service dependencies | +2 pts | 1 day | High |
| Add `updated_at`/`updated_by` columns + auto-population | +1 pt | 0.5 day | Medium |
| Decouple `receipt_service` from direct `db` import | +1 pt | 0.5 day | Medium |
| Add simple caching layer (in-memory TTL cache for catalogs) | +1 pt | 0.5 day | Low |

### Recommended Approach

1. **DI container**: Create `lab_system/app/di.py` with a simple registry/providers pattern (not a full framework — just factory functions or a lightweight container)
2. **Service decoupling**: Pass dependencies via constructors instead of importing `db` at module level
3. **Timestamps**: Add `updated_at` and `updated_by` columns to `receipts`, `organizations`, `users` tables; populate via triggers or service layer
4. **Caching**: Add `TTLCache` wrapper for `catalog_service` (transaction types and sample types are read-heavy, write-rare)

### Expected Outcome
- Architecture score: 87 → 90+
- Effort: 2-3 days
- Risk: Low (incremental refactoring, no schema changes that break backward compatibility)

---

## Gates That Pass (no action required)

| Gate | Score | Threshold | Verdict |
|------|-------|-----------|---------|
| Security | 91 | >= 88 | ✅ |
| Database | 93 | >= 92 | ✅ |
| Testing | 100% | >= 89 | ✅ |
| Coverage | 89% | >= 89 | ✅ |
| UX | 90 | >= 88 | ✅ |
| DevOps | 94 | >= 88 | ✅ |
| Performance | VERIFIED | VERIFIED | ✅ |
| Production Safety | PASS | PASS | ✅ |
| RBAC | Production Ready | Production Ready | ✅ |
| Sync | Production Ready | Production Ready | ✅ |
| Critical Findings | 0 | 0 | ✅ |
| High Findings | 0 | 0 | ✅ |

---

## Summary

```
Remaining gaps: 1 (Architecture)
Est. effort:    2-3 days
Next action:    Implement DI container + service decoupling
```

Close this gap, re-run all certification gates, and promote to **RELEASE CANDIDATE**.
