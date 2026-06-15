# Remaining Gap Report

## Current Classification: PRE-PRODUCTION

**Target**: RELEASE CANDIDATE  
**Date**: 2026-06-15  
**Version**: v1.2.0 RC Certification Cycle

---

## Gap 1: Architecture (87 / 90, need +3)

| Gap | Impact | Effort | Priority |
|-----|--------|--------|----------|
| Repository migration incomplete: Transaction handler still uses raw SQL | Data layer -1 | 1 day | High |
| No paginated responses on sync list endpoints | API design -1 | 0.5 day | High |
| No API response schema validation on all endpoints | API design -1 | 1 day | Medium |
| No DI framework for service dependencies | Architecture -2 | 3 days | Low |

**Effort to close**: 2-3 days

---

## Gap 2: UX (85 / 88, need +3)

| Gap | Impact | Effort | Priority |
|-----|--------|--------|----------|
| Global search across receipts, orgs, users | +2 | 3-5 days | High |
| Keyboard shortcuts (Ctrl+N, Ctrl+S, F5) | +1 | 1 day | Medium |
| Contextual help tooltips | +1 | 2 days | Medium |
| Saved filters on receipt list | +1 | 2 days | Low |

**Effort to close**: 1-2 weeks

---

## Gap 3: DevOps (80 / 88, need +8)

| Gap | Impact | Effort | Priority |
|-----|--------|--------|----------|
| GitHub Actions CI workflow | +5 | 1 day | High |
| Dockerfile + Docker Compose | +3 | 1 day | High |
| Pre-commit hooks (ruff, pytest) | +1 | 0.5 day | Medium |
| Coverage enforcement in CI | +1 | 0.5 day | Medium |
| Log rotation configuration | +1 | 0.5 day | Low |

**Effort to close**: 3-5 days

---

## Gap 4: RBAC (PARTIAL → Production Ready)

| Gap | Impact | Effort | Priority |
|-----|--------|--------|----------|
| Add `user=None` param + `@with_permission` to 26 unprotected functions | Security | 2 days | High |
| Update backup_page.py callers to pass `user=self.current_user` | Consistency | 0.5 day | High |
| Fix delegation bypass pattern (approve/reject wrappers) | Consistency | 1 day | Medium |
| Write privilege escalation regression tests | Verification | 1 day | Medium |

**Effort to close**: 2-3 days

---

## Gap 5: Sync (PARTIAL → Production Ready)

| Gap | Impact | Effort | Priority |
|-----|--------|--------|----------|
| Write E2E integration tests (all sync operations) | Verification | 2-3 days | High |
| Add queue size limit with configurable cap | Operations | 0.5 day | High |
| Add conflict resolution UI | UX | 3-5 days | Medium |
| Add thread safety guard to sync scheduler | Reliability | 0.5 day | Medium |
| Add `status` column to backend SyncLog | Operations | 1 day | Low |

**Effort to close**: 3-5 days

---

## Summary

| Domain | Gap | Effort to Close |
|--------|-----|----------------|
| Architecture | 87 → 90 | 2-3 days |
| UX | 85 → 88 | 1-2 weeks |
| DevOps | 80 → 88 | 3-5 days |
| RBAC | PARTIAL → Ready | 2-3 days |
| Sync | PARTIAL → Ready | 3-5 days |

**Total estimated effort**: 3-4 weeks for all 5 domains  
**Recommended priority**: Architecture → DevOps → RBAC → Sync → UX
