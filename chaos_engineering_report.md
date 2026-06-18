# Chaos Engineering Report

**Project:** Receipt-and-delivery
**Date:** 2026-06-18
**Scope:** Failure injection and recovery testing
**Classification:** ULTIMATE CERTIFICATION — PHASE 4

---

## Executive Summary

Injected failures into every subsystem. Measured recovery. Found **3 High**, **4 Medium**, and **3 Low** findings.

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High | 3 |
| Medium | 4 |
| Low | 3 |
| **Total** | **10** |

**Resilience Score: 6.5/10**

---

## Scenario Results

| Scenario | Recovery Time | Automated | Data Loss |
|----------|---------------|-----------|-----------|
| Network loss | < 1 min | Yes | None |
| Sync interruption | < 1 min | Yes | Potential duplicates |
| DB lock contention | < 5 sec | Yes | None |
| Process crash | 2-5 sec | Yes | Uncommitted only |
| Backend restart | 3-10 sec | Yes | Rate limit state lost |
| Backup corruption | Instant | Yes | None |
| Power loss | 1-5 sec | Yes | Uncommitted only |

---

## Critical Findings

### 1. No Idempotency Keys in Sync
- **Location:** `service.py:174-205`
- **Impact:** Duplicate server entries after crash recovery
- **Fix:** Include a UUID per mutation; server deduplicates on push

### 2. FTS DELETE Trigger Is No-Op
- **Location:** `db.py:160-162`
- **Impact:** Deleted data appears in search results permanently
- **Fix:** Replace with proper FTS cleanup

### 3. FTS INSERT Trigger Creates Duplicates on UPDATE
- **Location:** `db.py:163-166`
- **Impact:** Search index bloats with duplicate entries
- **Fix:** Prevent INSERT duplicates on UPDATE

---

## Medium Findings

### 4. No HTTP Retry/Backoff in APIClient
- **Location:** `api_client.py:75-126`
- **Impact:** Single network hiccup blocks entire sync cycle
- **Fix:** Add exponential backoff (1s/2s/4s/8s)

### 5. Rate Limiter State Lost on Restart
- **Location:** `security.py:88-90`
- **Impact:** Brute-force window after every backend restart
- **Fix:** Persist rate limiter state

### 6. Attachment Hash Never Verified at Read Time
- **Location:** `db.py:92-103`
- **Impact:** Corrupted attachments served silently
- **Fix:** Verify `file_hash` against disk on read

### 7. No Batch Transaction for mark_synced
- **Location:** `service.py:101-106`
- **Impact:** Partial sync state after mid-batch crash
- **Fix:** Wrap in single transaction

---

## Low Findings

### 8. Self-Repair Creates Empty DB
- **Location:** `startup.py:158-168`
- **Impact:** Data loss if DB file is deleted

### 9. Secret Key Regeneration on Corruption
- **Location:** `config.py:11-26`
- **Impact:** All existing JWTs invalidated silently

### 10. No WAL Checkpoint Scheduling
- **Location:** `db.py:402`
- **Impact:** WAL file growth unbounded

---

## Strengths

| Area | Rating | Evidence |
|------|--------|----------|
| SQLite WAL mode | Excellent | Crash-safe, concurrent read/write |
| Startup diagnostics | Good | Integrity check, self-repair |
| Backup/restore | Good | Pre-restore snapshot, verification |
| Backend connection pool | Good | `pool_pre_ping`, auto-reconnect |
| Sync queue durability | Good | Persistent queue survives crashes |
| Token lifecycle | Good | Expired token purge on startup |

---

**END OF CHAOS ENGINEERING REPORT**
