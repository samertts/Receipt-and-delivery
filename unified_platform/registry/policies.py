"""
Platform Registry — Policy Registry

Centralized policy management for business rules.
Constitution: Principle 79 (Policy Driven Operations), Principle 80 (Central Policy Repository)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from unified_platform.registry.base import RegistryEntry, RegistryStatus


@dataclass
class PolicyEntry(RegistryEntry):
    """A registered policy in the platform."""
    policy_id: str = ""
    policy_type: str = ""  # security, data, access, retention, compliance
    module: str = ""
    rules: dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    is_enforceable: bool = True
    is_auditable: bool = True
    effective_date: str = ""
    expiry_date: str = ""


class PolicyRegistry:
    """Central registry for all platform policies."""

    def __init__(self) -> None:
        self._policies: dict[str, PolicyEntry] = {}

    def register(self, policy: PolicyEntry) -> None:
        """Register a policy."""
        self._policies[policy.name] = policy

    def unregister(self, name: str) -> bool:
        """Unregister a policy."""
        if name in self._policies:
            del self._policies[name]
            return True
        return False

    def get(self, name: str) -> PolicyEntry | None:
        """Get a policy by name."""
        return self._policies.get(name)

    def list_all(self) -> list[PolicyEntry]:
        """List all registered policies."""
        return list(self._policies.values())

    def list_by_type(self, policy_type: str) -> list[PolicyEntry]:
        """List all policies of a specific type."""
        return [p for p in self._policies.values() if p.policy_type == policy_type]

    def list_by_module(self, module: str) -> list[PolicyEntry]:
        """List all policies for a module."""
        return [p for p in self._policies.values() if p.module == module]

    def list_enforceable(self) -> list[PolicyEntry]:
        """List all enforceable policies."""
        return [p for p in self._policies.values() if p.is_enforceable]

    def list_active(self) -> list[PolicyEntry]:
        """List all active (non-expired) policies."""
        now = datetime.utcnow().isoformat()
        return [
            p for p in self._policies.values()
            if p.status == RegistryStatus.ACTIVE
            and (not p.expiry_date or p.expiry_date > now)
        ]

    def evaluate(self, policy_name: str, context: dict[str, Any]) -> dict[str, Any]:
        """Evaluate a policy against a context."""
        policy = self._policies.get(policy_name)
        if not policy:
            return {"allowed": False, "reason": "Policy not found"}
        if policy.status != RegistryStatus.ACTIVE:
            return {"allowed": False, "reason": "Policy inactive"}
        return {
            "allowed": True,
            "policy": policy.name,
            "rules": policy.rules,
            "context": context,
        }

    def export_registry(self) -> dict[str, Any]:
        """Export the full registry."""
        return {
            name: {
                "name": p.name,
                "policy_type": p.policy_type,
                "module": p.module,
                "priority": p.priority,
                "is_enforceable": p.is_enforceable,
                "is_auditable": p.is_auditable,
                "status": p.status.value,
                "effective_date": p.effective_date,
                "expiry_date": p.expiry_date,
            }
            for name, p in self._policies.items()
        }
