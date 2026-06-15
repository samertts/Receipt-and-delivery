# National Laboratory Platform Readiness Report — Phase 10.6

**Date:** 2026-06-14  
**Program:** v1.2.0 Enterprise Evolution  
**Branch:** feature/v1.2.0-ui-modernization-phase2  
**Commit:** 97abb36

---

## 1. Assessment Scope

Evaluate the platform's readiness for national-scale multi-laboratory deployment covering:
- Multi-site deployment architecture
- Central administration
- National reporting
- Specimen tracking across laboratories
- Synchronization between sites
- Integration APIs

---

## 2. Current Architecture

```
┌─────────────────────────────────┐
│     Desktop App (PySide6)       │
│  ┌───────────┐ ┌──────────────┐ │
│  │ SQLite DB │ │ Local Storage│ │
│  └───────────┘ └──────────────┘ │
└─────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│     Backend API (FastAPI)       │
│  ┌───────────┐ ┌──────────────┐ │
│  │PostgreSQL │ │   File Store │ │
│  └───────────┘ └──────────────┘ │
└─────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│     Frontend (Vue.js)           │
└─────────────────────────────────┘
```

**Assessment:** The current architecture is **single-site** — one SQLite database per desktop installation, one PostgreSQL database per backend instance, no multi-tenancy or site-aware routing.

---

## 3. Multi-Laboratory Requirements

### 3.1 Site Identity

| Requirement | Status | Details |
|------------|--------|---------|
| Site/branch ID | ✅ Present | `set_branch_id()` / `get_branch_id()` in `device.py` |
| Site-aware data scoping | ❌ Missing | No `laboratory_id` or `site_id` foreign keys on entities |
| Site configuration | ❌ Missing | No per-site settings (name, address, contact) |
| Cross-site references | ❌ Missing | No mechanism to reference entities from other sites |

**Finding:** Site identity infrastructure exists at the device level but is not wired into the data model. No entity carries a site identifier.

### 3.2 Central Administration

| Requirement | Status | Details |
|------------|--------|---------|
| Central user management | ❌ Missing | Each desktop instance manages its own users |
| Central organization directory | ❌ Missing | Organizations are local to each instance |
| Central settings management | ❌ Missing | Settings are local to each SQLite DB |
| Multi-tenancy | ❌ Missing | No tenant isolation in data model |

**Finding:** Each desktop installation is fully autonomous with no central administration capability. Backend API has single PostgreSQL database with no tenant context.

### 3.3 National Reporting

| Requirement | Status | Details |
|------------|--------|---------|
| Aggregated reports | ❌ Missing | Reports are local to each SQLite instance |
| Standardized report templates | ⚠️ Partial | Desktop has PDF export; no national format |
| Data warehouse export | ❌ Missing | No ETL or data export for central analytics |
| Dashboard KPIs | ⚠️ Partial | Local dashboard only; no cross-site comparison |

**Finding:** National reporting would require a central data aggregation system that pulls data from all sites.

---

## 4. Specimen Tracking

| Requirement | Status | Details |
|------------|--------|---------|
| Unique specimen ID | ❌ Missing | Receipt numbers are local (`LAB-2026-000001`) with no site prefix |
| Inter-laboratory transfer | ❌ Missing | No workflow for sending specimens between labs |
| Chain of custody | ⚠️ Partial | Receipt has sender/receiver; no custody timestamps |
| Barcode/RFID support | ❌ Missing | No barcode generation or scanning |
| Specimen status tracking | ⚠️ Partial | Receipt-level status (Draft/Approved/Rejected); no per-specimen status |

**Finding:** Specimens are tracked at the receipt level only. No globally unique specimen identifier exists for cross-site tracking.

---

## 5. Synchronization

See Phase 9 (Sync Readiness Report) for detailed assessment.

| Component | Readiness | Gap |
|-----------|-----------|-----|
| Sync schema | ✅ Ready | Queue table exists |
| Sync execution | ❌ Missing | No backend endpoints, no service wiring |
| Conflict resolution | ❌ Missing | Stub implementation |
| Offline operation | ⚠️ Partial | Desktop works offline but no sync when online |

**Key Gap for National Deployment:** Without operational sync, each site operates as an isolated island. Consolidation requires manual data export/import.

---

## 6. Integration APIs

### 6.1 Existing Backend API

| Feature | Status | National Requirement |
|---------|--------|---------------------|
| REST endpoints | ✅ Present | 21 endpoints covering CRUD |
| OpenAPI specification | ✅ Present | `/api/docs`, `/api/redoc`, `/api/openapi.json` |
| JWT authentication | ✅ Present | Standard Bearer tokens |
| Webhooks | ❌ Missing | No event-driven integration |
| Batch operations | ❌ Missing | No bulk create/update/delete |
| Data export (CSV/JSON) | ❌ Missing | No format-agnostic data export |

### 6.2 National Integration Requirements

| Integration | Required | Current State |
|------------|----------|---------------|
| HL7 FHIR (healthcare) | Potential future | Not supported |
| National ID / Civil Registry | Potential future | Not supported |
| Government reporting API | Potential future | Not supported |
| Central dashboard API | Short-term | Not supported |

---

## 7. Scalability Assessment

| Dimension | Current Limit | National Requirement | Gap |
|-----------|--------------|---------------------|-----|
| Desktop users per site | 1 (single-user) | 5-50 per lab | Major — no multi-user desktop |
| Backend concurrent users | 100+ | 1,000+ | Minor — FastAPI scales with workers |
| Database size | SQLite practical limit ~1GB | 10GB+ per site | Major — need PostgreSQL at each site or central |
| Sites supported | 1 | 10-500 | Major — no multi-site architecture |
| Data latency | Real-time local | Near-real-time central | Major — no sync pipeline |

---

## 8. Scoring

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| Multi-site Architecture | 15/100 | No site-awareness in data model, no multi-tenancy |
| Central Administration | 20/100 | Each site is fully autonomous |
| Specimen Tracking | 25/100 | Local receipt tracking only; no global IDs |
| Synchronization | 25/100 | Schema exists; execution missing |
| Integration APIs | 50/100 | Good REST API; no national standard support |
| Scalability | 30/100 | Single-user desktop is primary bottleneck |

**Overall National Platform Readiness: 28/100**

---

## 9. Gap Closure Roadmap

### Phase 1: Foundation (4-6 months)
1. **Add site ID to all entities** — `laboratory_id` foreign key on receipts, users, organizations
2. **Site-aware authentication** — JWT includes `lab_id` claim
3. **Complete sync system** — bidirectional sync between desktop instances and central server
4. **Central directory service** — users, organizations, settings managed centrally

### Phase 2: Multi-User Desktop (3-4 months)
5. **Desktop multi-user support** — network-attached SQLite or embedded PostgreSQL
6. **Concurrent editing** — conflict resolution for simultaneous edits
7. **Role-based site administration** — site-level admin separate from system admin

### Phase 3: National Features (4-6 months)
8. **Globally unique specimen ID** — site-prefixed receipt numbers (`LAB-KHOBAR-2026-000001`)
9. **Inter-laboratory transfer workflow** — send/receive specimens between sites
10. **Central dashboard** — aggregated KPIs across all sites
11. **National reporting** — standardized PDF/Excel reports with government branding

### Phase 4: Advanced Integration (6-8 months)
12. **HL7 FHIR adapter** — standard healthcare data exchange
13. **Barcode/RFID integration** — specimen tracking with scanners
14. **Chain of custody** — complete audit trail for every specimen movement
15. **Data warehouse export** — ETL pipeline for national analytics

**Total estimated effort: 19-24 developer-months**

---

## 10. Architectural Recommendation

For national deployment, the platform should evolve to a **hub-and-spoke architecture**:

```
┌─────────────────────────────────────────┐
│          Central Server (Cloud)          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │  Master  │ │  Central │ │  Admin   ││
│  │   DB     │ │  API     │ │  Portal  ││
│  └──────────┘ └──────────┘ └──────────┘│
└─────────────────────────────────────────┘
          ↕ sync ↕         ↕ sync ↕
┌──────────────┐      ┌──────────────┐
│  Lab A Site  │      │  Lab B Site  │
│  (Desktop)   │      │  (Desktop)   │
│  + Backend   │      │  + Backend   │
│  + Frontend  │      │  + Frontend  │
└──────────────┘      └──────────────┘
```

Each laboratory runs its own local instance (desktop or web-based) with a sync agent that communicates with the central server. The central server aggregates data for national reporting and enables inter-laboratory workflows.

---

## 11. Conclusion

The platform is **not ready for national multi-laboratory deployment** in its current form. The single-user desktop architecture, lack of site-awareness in the data model, and incomplete sync system are fundamental blockers. However, the clean REST API, existing sync schema, and role-based access system provide a solid foundation. Achieving national readiness requires a **multi-year investment** focused on multi-site architecture, sync completion, and central administration features.

**National Platform Readiness Score: 28/100**
