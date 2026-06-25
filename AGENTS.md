# AGENTS.md — Agent Operating Instructions for Receipt-and-Delivery

**Governing Document: [CONSTITUTION.md](./CONSTITUTION.md) — V4.0**

---

## Supremacy

All agents operating on this codebase must comply with [CONSTITUTION.md](./CONSTITUTION.md) as the supreme governing standard. The Constitution supersedes all previous constitutions, guidelines, standards, and architectural directives.

---

## Mandatory Workflow

### Before Making Any Change

1. Read the relevant section of CONSTITUTION.md
2. Identify which principles apply to the change
3. Verify the change does not violate any principle
4. Implement the change
5. Verify compliance

### Commit Requirements

- All tests must pass (`python3 -m pytest tests/ -q`)
- All lint checks must pass (`python3 -m ruff check .`)
- Every bug fix must include a regression test
- Every security finding must include a security test
- All decisions must be supported by evidence (tests, metrics, benchmarks)

### Service Boundary Enforcement (Principle 3)

The only approved execution flow is:

```
UI → Application Services → Domain Services → Repositories → Database
```

Direct database access outside approved repositories is prohibited.

### Zero Trust Security (Principle 4)

Every request must be authenticated, authorized, audited, and validated.

- Fail Closed is mandatory
- No exceptions

### Data Sovereignty (Principle 1)

All data remains owned by the organization.

No feature, service, update, integration, migration, or deployment may compromise:

- Data ownership
- Data integrity
- Data recoverability
- Data traceability

### Zero Data Loss (Principle 2)

Priority Order:

1. Data Integrity
2. Data Availability
3. Operational Continuity
4. Features

---

## Testing Requirements

### Every Defect Produces a Test (Principle 14)

No bug may be closed without a regression test.

### Every Security Finding Produces a Security Test (Principle 15)

Security issues must never reappear undetected.

### Measurable Engineering (Principle 16)

No claim may be accepted without evidence.

All decisions must be supported by:

- Tests
- Metrics
- Benchmarks
- Reports

---

## Resilience Requirements

### Recovery Before Features (Principle 17)

Backup and recovery capability takes precedence over feature development.

### Continuous Disaster Preparedness (Principle 18)

The platform must regularly validate recovery from:

- Database corruption
- Storage failure
- Unexpected shutdown
- Power loss
- Synchronization interruption

### Observability First (Principle 19)

Every production issue must be diagnosable through:

- Logs
- Metrics
- Traces
- Audit Evidence

---

## Release and Deployment

### No Release Without Certification (Principle 22)

Certification reports are mandatory.

### No Deployment With Critical Findings (Principle 23)

- Critical Findings > 0 = Deployment Blocked
- High Findings > 0 = Deployment Blocked

---

## Architecture

### Service Boundary Enforcement (Principle 3)

Direct database access outside approved repositories is prohibited.

### Shared Data Contracts (Principle 12)

All future integrations must use standardized APIs, DTOs, schemas, and versioned contracts.

### National Platform Compatibility (Principle 13)

Every architectural decision must be evaluated against future:

- Multi-site deployment
- Province-wide deployment
- National deployment

Architectural choices that block national expansion are prohibited.

---

## AI Readiness (Principle 8)

Every new service must be designed for future AI integration.

All services must expose structured contracts.

All critical events must be machine-readable.

---

## Event-Driven Readiness (Principle 9)

Critical business operations must be capable of producing events.

**Examples:**

- `ReceiptCreated`
- `ReceiptUpdated`
- `ReceiptDeleted`
- `ReceiptRestored`
- `BackupCreated`
- `RecoveryExecuted`
- `SyncConflictDetected`

---

## Continuous Architecture Evolution (Principle 24)

Architecture is not static.

The platform must continuously evolve toward:

- Better scalability
- Better maintainability
- Better reliability
- Better security
- Better intelligence

---

## Long-Term Vision (Principle 10)

Receipt-and-delivery shall serve as the foundational operational core of a future unified enterprise ecosystem.

Future expansion shall require configuration, integration, and scaling rather than complete system replacement.

The platform shall continuously evolve toward:

- Enterprise Platform
- Laboratory Platform
- Government Operations Platform
- National Health Operations Platform

without architectural redesign.

---

## 15-Phase Execution Order

The Constitution defines 15 phases for platform evolution. Each phase must be completed with full evidence before proceeding to the next. See [PHASE_EXECUTION_PLAN.md](./PHASE_EXECUTION_PLAN.md) for detailed execution steps.

### Phase Status

| Phase | Name | Status | Evidence |
|-------|------|--------|----------|
| 1 | Platform Core Extraction | COMPLETE | 11 services in `unified_platform/core/` |
| 2 | Unified Ecosystem Architecture | COMPLETE | 6 registries in `unified_platform/registry/` |
| 3 | Operational Intelligence Engine | COMPLETE | 10 score calculators in `unified_platform/intelligence/` |
| 4 | AI Operations Assistant | COMPLETE | 12 AI capabilities in `unified_platform/ai/` |
| 5 | Event Platform | COMPLETE | Event bus + 15 events in `unified_platform/events/` |
| 6 | Observability Platform | COMPLETE | 7 components in `unified_platform/observability/` |
| 7 | National Scale Readiness | COMPLETE | UUID, API versioning, nodes in `unified_platform/national/` |
| 8 | Mobile Ecosystem Readiness | COMPLETE | 7 contract types in `unified_platform/mobile/` |
| 9 | Self-Improvement Framework | COMPLETE | 5 detectors in `unified_platform/intelligence/` |
| 10 | Pilot Deployment Program | COMPLETE | V12.0 certification, 1372 tests passing |
| 11 | Platform Governance | COMPLETE | Governance framework in `unified_platform/governance/` |
| 12 | Future Ecosystem Consolidation | COMPLETE | 13 shared components in `unified_platform/consolidation/` |
| 13 | National Laboratory Platform Readiness | COMPLETE | Lab contracts in `unified_platform/laboratory/` |
| 14 | Certification Governance | COMPLETE | Certification framework in `unified_platform/certification/` |
| 15 | Evolution Guarantee | COMPLETE | Fitness/debt/future engines in `unified_platform/evolution/` |
