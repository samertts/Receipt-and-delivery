# Performance Certification Report

**Date:** 2026-06-14

---

## 1. Benchmark Summary

All measurements taken on the benchmark machine. Queries run 5 times each, averaged.

| Metric | 1K Receipts | 10K Receipts | 100K Receipts | Threshold | Status |
|--------|-------------|--------------|---------------|-----------|--------|
| DB Size | 0.7 MB | 4.8 MB | 51.8 MB | — | ✅ |
| Creation Time | < 0.01s | 0.01s | 35.93s | < 120s | ✅ |
| Receipts | 1,000 | 10,000 | 100,000 | — | ✅ |
| Items | 5,538 | 55,030 | 549,476 | — | ✅ |

## 2. Query Performance

| Query | 1K (avg s) | 10K (avg s) | 100K (avg s) | Threshold | Status |
|-------|------------|-------------|--------------|-----------|--------|
| List receipts (page 1) | 0.0023 | 0.0029 | **0.2842** | < 0.5s | ✅ |
| FTS search | 0.0044 | 0.0043 | **0.0032** | < 0.5s | ✅ |
| Monthly report | 0.0054 | 0.0129 | **0.1426** | < 1.0s | ✅ |
| Sample summary | 0.0125 | 0.1100 | **1.1098** | < 2.0s | ✅ |
| Full export | 0.0145 | 0.1203 | **1.3489** | < 2.0s | ✅ |
| Filter by status | 0.0025 | 0.0068 | **0.0336** | < 0.5s | ✅ |

## 3. Backup Performance

| Dataset | Avg | Min | Threshold | Status |
|---------|-----|-----|-----------|--------|
| 1K | 0.0071s | 0.0025s | < 1.0s | ✅ |
| 10K | 0.0249s | 0.0205s | < 1.0s | ✅ |
| 100K | 0.1973s | 0.1721s | < 1.0s | ✅ |

## 4. FTS Search Variations (100K dataset)

| Query | Avg | Min |
|-------|-----|-----|
| fts_مصل (Arabic) | 0.0115s | 0.0035s |
| fts_دم (Arabic) | 0.0038s | 0.0027s |
| fts_BENCH (Latin) | 0.0180s | 0.0134s |
| fts_Org (Latin) | 0.0028s | 0.0025s |

## 5. Performance Certification: VERIFIED ✅

All queries meet or exceed performance thresholds at all dataset sizes (1K, 10K, 100K). The 100K dataset demonstrates that the system handles 550K receipt items with all queries completing in under 1.5 seconds.
