# GULA Sample Custody Contract

## Purpose

This contract defines the boundary between sample movement and clinical processing. Receipt-and-delivery owns custody events; GULA owns clinical order context and result approval.

## Required event fields

| Field | Requirement |
|---|---|
| `sample_id` | Stable identifier for the physical sample |
| `actor_id` | Authenticated user or service identity |
| `from_state` | State observed immediately before the transition |
| `to_state` | Explicitly allowed next state |
| `occurred_at` | Timezone-aware timestamp |
| `idempotency_key` | Unique key for the attempted transition |
| `reason` | Required for rejection or loss |

## State rules

The authoritative transition map is implemented in `backend/app/domain/chain_of_custody.py`. A caller must not infer transitions from UI state or accept an unknown target. Invalid transitions are hard failures and must produce an audit record in the persistence layer.

The terminal states are `completed`, `rejected`, `lost`, and `cancelled`. A terminal sample cannot be reopened or silently edited. Any correction must be represented by a new auditable event or an explicit resolution workflow.

## Integration boundary

Receipt-and-delivery emits custody events. GULA consumes them to update the sample context. Neither receipt processing nor a custody event may approve a clinical result. Result approval remains restricted to the authorized clinical workflow in GULA.

## Delivery requirements

Implementing an HTTP or event transport must preserve the idempotency key, reject stale versions, use authenticated service identities, and retain the before/after state in the audit record. Offline synchronization must replay events in order and surface conflicts instead of overwriting them.
