# AUTH TIMESTAMP FIX REPORT

**Date:** 2026-06-19
**Status:** RESOLVED

---

## Issue

`change_password()` used second-resolution timestamps which could cause test flakiness when comparing timestamps within the same second.

## Fix Applied

**File:** `lab_system/app/services/auth_service.py`
**Method:** `change_password()`
**Change:** Replaced `datetime.utcnow().isoformat()` with `datetime.utcnow().isoformat(timespec="microseconds")`

## Verification

| Test | Status |
|------|--------|
| test_change_password | ✅ PASS |
| test_change_password_wrong_old | ✅ PASS |
| test_change_password_no_session | ✅ PASS |

All `TestAuthServiceAdvanced` tests pass (11/11).

## Before State

Timestamp: `2026-06-19T12:00:00` (second resolution)
Test comparison: Could fail if same second

## After State

Timestamp: `2026-06-19T12:00:00.123456` (microsecond resolution)
Test comparison: Always distinct
