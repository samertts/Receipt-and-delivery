# Database Resilience Report

**Project:** Receipt-and-delivery
**Date:** 2026-06-18
**Scope:** Database destruction and recovery testing
**Classification:** ULTIMATE CERTIFICATION — PHASE 3

---

## Executive Summary

Simulated catastrophic database failures. Found **2 Critical**, **3 Medium**, and **1 Low** findings.

| Severity | Count |
|----------|-------|
| Critical | 2 |
| High | 0 |
| Medium | 3 |
| Low | 1 |
| **Total** | **6** |

---

## Test Results

| Scenario | Recovery | Data Loss | Status |
|----------|----------|-----------|--------|
| Corrupted database header | Auto-recovery from backup | None | PASS |
| Missing WAL file | WAL replay on next open | Uncommitted only | PASS |
| Missing indexes | Startup check detects | None | PASS |
| Broken migrations | Migration lock prevents | None | PASS |
| Partial restore | Pre-restore snapshot | None | PASS |
| Interrupted backup | Atomic SQLite backup | None | PASS |
| Interrupted recovery | Rollback to .corrupted | None | PASS |
| Disk-full condition | SQLITE_FULL error | Uncommitted only | PASS |
| 50 simultaneous connections | All succeed | None | PASS |

---

## Critical Findings

### 1. Stale Migration Lock Bricks Application
- **Location:** `db.py:445-451`
- **Impact:** If `init_db()` crashes while holding the lock, the app permanently fails on restart
- **Fix:** Add staleness check (>5 min) with auto-clear

### 2. Backup Integrity Check Misses Byte-Level Tampering
- **Location:** `recovery_service.py:48`
- **Impact:** `PRAGMA integrity_check` doesn't detect content corruption at offset 1024
- **Fix:** Add SHA-256 checksum verification on backup creation and restore

---

## Medium Findings

### 3. SQLite Header Corruption Lenient
- SQLite is lenient about header corruption
- File can still be opened even with minor corruption

### 4. Restore Path Hardcoded
- `restore_from_backup()` hardcodes backup directory path
- Blocks recovery from external locations

### 5. FTS Rebuild Uses Global Config
- `rebuild_fts()` uses global `CONFIG.db_path`
- Fails during recovery redirection

---

## Low Finding

### 6. FTS DELETE Triggers Are No-Ops
- Acknowledged SQLite < 3.39 bug
- Causes phantom search results

---

## What's Solid

- WAL mode
- Foreign keys
- Migration lock
- Pre-migration backups
- SAVEPOINT-based table recreation
- Atomic SQLite backup
- CHECK constraints
- Audit hash chain
- Connection lifecycle management
- FTS5 rebuild
- Deadlock prevention
- Concurrent connection handling

---

**END OF DATABASE RESILIENCE REPORT**
