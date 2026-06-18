# Production Hardening Roadmap

**Date:** 2026-06-17
**Branch:** feature/v1.2.0-ui-modernization-phase2
**Version:** 1.2.0-dev

## Current State

| Aspect | Status |
|--------|--------|
| Database | PostgreSQL 16 (web), SQLite (desktop) |
| Caching | None (in-memory rate limiter) |
| Job Scheduling | None |
| Event System | None |
| Configuration | Environment variables |
| Logging | Structured JSON |
| Metrics | None |

## Hardening Recommendations

### 1. PostgreSQL Migration Path

**Current:** Already using PostgreSQL for web backend.
**Enhancement:** Add connection pooling, read replicas.

| Task | Priority | Effort |
|------|----------|--------|
| PgBouncer connection pooling | HIGH | 1 day |
| Read replica for reports | MEDIUM | 2 days |
| Connection pool monitoring | LOW | 0.5 days |

### 2. Redis Integration Path

**Current:** In-memory rate limiter with Redis fallback.
**Enhancement:** Full Redis integration for caching and sessions.

| Task | Priority | Effort |
|------|----------|--------|
| Redis session store | HIGH | 1 day |
| Redis cache layer | MEDIUM | 2 days |
| Redis rate limiter | HIGH | 0.5 days |
| Redis pub/sub for events | LOW | 1 day |

### 3. Background Job Scheduler

**Current:** No background job processing.
**Enhancement:** Add Celery or ARQ for async tasks.

| Task | Priority | Effort |
|------|----------|--------|
| Celery/ARQ setup | HIGH | 2 days |
| Sync job scheduling | MEDIUM | 1 day |
| Backup job scheduling | MEDIUM | 1 day |
| Report generation jobs | LOW | 1 day |

### 4. Event-Driven Audit Stream

**Current:** Synchronous audit logging.
**Enhancement:** Event-driven audit with message queue.

| Task | Priority | Effort |
|------|----------|--------|
| Event bus implementation | MEDIUM | 2 days |
| Audit event publishing | MEDIUM | 1 day |
| Event consumers | LOW | 2 days |
| Event replay | LOW | 1 day |

### 5. Centralized Configuration Management

**Current:** Environment variables + Pydantic Settings.
**Enhancement:** Consul/Vault for dynamic configuration.

| Task | Priority | Effort |
|------|----------|--------|
| Config server setup | LOW | 2 days |
| Dynamic config refresh | LOW | 1 day |
| Secret management | MEDIUM | 1 day |
| Config versioning | LOW | 0.5 days |

### 6. Structured Logging

**Current:** JSON logging with structlog patterns.
**Enhancement:** Full observability stack.

| Task | Priority | Effort |
|------|----------|--------|
| ELK stack integration | MEDIUM | 3 days |
| Log aggregation | MEDIUM | 1 day |
| Log-based alerts | LOW | 1 day |
| Distributed tracing | LOW | 2 days |

### 7. Metrics Collection

**Current:** No metrics collection.
**Enhancement:** Prometheus + Grafana.

| Task | Priority | Effort |
|------|----------|--------|
| Prometheus metrics | HIGH | 1 day |
| Grafana dashboards | MEDIUM | 2 days |
| Custom business metrics | MEDIUM | 1 day |
| Alert rules | LOW | 1 day |

## Implementation Priority

### Phase 1 (Immediate - 1 week)
1. Redis integration for rate limiting and caching
2. Prometheus metrics collection
3. Connection pooling

### Phase 2 (Short-term - 2 weeks)
1. Background job scheduler
2. ELK stack for logging
3. Grafana dashboards

### Phase 3 (Medium-term - 1 month)
1. Event-driven audit stream
2. Centralized configuration
3. Distributed tracing

## Estimated Total Effort

| Phase | Effort |
|-------|--------|
| Phase 1 | 5 days |
| Phase 2 | 8 days |
| Phase 3 | 10 days |
| **Total** | **23 days** |

## Conclusion

The current architecture is production-ready for v1.2.0. The hardening roadmap provides a clear path for scaling to enterprise-grade operations. Priority should be given to Redis integration and metrics collection for immediate operational visibility.
