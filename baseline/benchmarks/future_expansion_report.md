# Future Expansion Readiness Report

**Date:** 2026-06-14
**Classification:** Assessment Only — No implementation

---

## 1. Android Client

**Current state:** No mobile API, no mobile client.
**Requirements:** REST API exists but no mobile-optimized endpoints (no pagination, no lightweight responses, no push notifications).
**Assessment:** Requires new mobile API layer + Android client from scratch.
**Effort estimate:** 6-9 months.

---

## 2. Regional Sync Nodes

**Current state:** Sync service is desktop-to-server (single central server). No multi-region support, no node discovery, no data partitioning.
**Requirements:** Geo-distributed sync nodes with eventual consistency, node registry, conflict-free replicated data types (CRDTs) or similar.
**Assessment:** Architectural foundation is too simple (single queue, LWW resolution). Requires fundamental redesign.
**Effort estimate:** 12-18 months.

---

## 3. Central Reporting

**Current state:** Backend has REST API with transaction/audit endpoints. No aggregated reporting views, no data warehouse, no scheduled report generation.
**Requirements:** Data aggregation across branches, scheduled PDF/CSV generation, drill-down dashboards.
**Assessment:** Backend API can serve as foundation but needs reporting-specific endpoints + scheduled job infrastructure.
**Effort estimate:** 3-6 months.

---

## 4. National Laboratory Platform

**Current state:** Single-organization system with no multi-tenancy, no role hierarchy, no data isolation between organizations.
**Requirements:** Multi-tenant with org-level data isolation, national-level roles, cross-org reporting, compliance with national laboratory standards.
**Assessment:** Requires complete architectural overhaul. Current flat organization model, single-database-per-instance, and client-side SQLite architecture are incompatible.
**Effort estimate:** 24-36 months.

---

## Expansion Readiness Summary

| Target | Readiness | Effort | Dependencies |
|--------|-----------|--------|-------------|
| Android Client | LOW | 6-9 months | Mobile API layer |
| Regional Sync Nodes | VERY LOW | 12-18 months | CRDT/distributed sync redesign |
| Central Reporting | MEDIUM | 3-6 months | Aggregation endpoints |
| National Platform | VERY LOW | 24-36 months | Multi-tenancy, org isolation |

**Overall Assessment:** The current architecture is suitable for single-lab/single-organization deployment. Expansion to multi-site, mobile, or national scale requires significant architectural investment. The REST API backend provides a foundation for central reporting but not for distributed or multi-tenant scenarios.
