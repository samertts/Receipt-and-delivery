"""
Platform Policy Engine — Rule-based policy management and evaluation
for security, access control, data retention, audit, backup, and compliance.

Phase 17: Policy Engine
Constitution: Principle 4 (Zero Trust Security),
              Principle 1 (Data Sovereignty),
              Principle 14 (Every Defect Produces a Test)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# ============================================================================
# Enums
# ============================================================================

class PolicyType(Enum):
    """Categories of policies the engine enforces."""
    SECURITY = "security"
    ACCESS_CONTROL = "access_control"
    DATA_RETENTION = "data_retention"
    AUDIT = "audit"
    BACKUP = "backup"
    COMPLIANCE = "compliance"


class PolicyStatus(Enum):
    """Lifecycle status of a policy."""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ENFORCED = "enforced"


# ============================================================================
# Data Contracts
# ============================================================================

@dataclass
class PolicyRule:
    """A single rule within a policy."""
    rule_id: str
    condition: str
    action: str
    priority: int = 0
    enabled: bool = True


@dataclass
class Policy:
    """A versioned policy containing zero or more rules."""
    policy_id: str
    name: str
    policy_type: PolicyType
    status: PolicyStatus = PolicyStatus.DRAFT
    rules: list[PolicyRule] = field(default_factory=list)
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    description: str = ""


# ============================================================================
# Policy Engine
# ============================================================================

class PolicyEngine:
    """Centralized engine for creating, managing, and evaluating policies.

    Supports activation, deactivation, rule management, and context-based
    evaluation of policy rules.
    """

    def __init__(self) -> None:
        self._policies: dict[str, Policy] = {}

    def create_policy(
        self,
        policy_id: str,
        name: str,
        policy_type: PolicyType,
        description: str = "",
    ) -> Policy:
        """Create a new policy in DRAFT status.

        Args:
            policy_id: Unique identifier for the policy.
            name: Human-readable policy name.
            policy_type: The category of policy.
            description: Optional description.

        Returns:
            The created Policy.
        """
        policy = Policy(
            policy_id=policy_id,
            name=name,
            policy_type=policy_type,
            description=description,
        )
        self._policies[policy_id] = policy
        return policy

    def add_rule(self, policy_id: str, rule: PolicyRule) -> bool:
        """Add a rule to an existing policy.

        Args:
            policy_id: The policy to modify.
            rule: The rule to add.

        Returns:
            True if the rule was added successfully.
        """
        policy = self._policies.get(policy_id)
        if policy is None:
            return False
        policy.rules.append(rule)
        policy.updated_at = datetime.utcnow()
        return True

    def remove_rule(self, policy_id: str, rule_id: str) -> bool:
        """Remove a rule from a policy.

        Args:
            policy_id: The policy to modify.
            rule_id: The rule to remove.

        Returns:
            True if the rule was found and removed.
        """
        policy = self._policies.get(policy_id)
        if policy is None:
            return False
        original_count = len(policy.rules)
        policy.rules = [r for r in policy.rules if r.rule_id != rule_id]
        if len(policy.rules) < original_count:
            policy.updated_at = datetime.utcnow()
            return True
        return False

    def activate_policy(self, policy_id: str) -> bool:
        """Transition a policy to ACTIVE status.

        Args:
            policy_id: The policy to activate.

        Returns:
            True if activation succeeded.
        """
        policy = self._policies.get(policy_id)
        if policy is None or policy.status == PolicyStatus.ENFORCED:
            return False
        policy.status = PolicyStatus.ACTIVE
        policy.updated_at = datetime.utcnow()
        return True

    def deactivate_policy(self, policy_id: str) -> bool:
        """Transition a policy to DEPRECATED status.

        Args:
            policy_id: The policy to deactivate.

        Returns:
            True if deprecation succeeded.
        """
        policy = self._policies.get(policy_id)
        if policy is None or policy.status == PolicyStatus.DRAFT:
            return False
        policy.status = PolicyStatus.DEPRECATED
        policy.updated_at = datetime.utcnow()
        return True

    def evaluate(
        self, policy_id: str, context: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """Evaluate all enabled rules in a policy against a context.

        Each rule's condition is checked as a simple key-in-context membership
        test.  If every enabled condition is satisfied the overall result is
        True; otherwise False.

        Args:
            policy_id: The policy to evaluate.
            context: Key-value pairs representing the evaluation context.

        Returns:
            Tuple of (passed, list_of_actions) where actions are from
            rules whose conditions were met.
        """
        policy = self._policies.get(policy_id)
        if policy is None:
            return False, []

        actions: list[str] = []
        enabled_rules = sorted(
            [r for r in policy.rules if r.enabled],
            key=lambda r: r.priority,
            reverse=True,
        )

        all_passed = True
        for rule in enabled_rules:
            if rule.condition in context:
                actions.append(rule.action)
            else:
                all_passed = False

        return all_passed, actions

    def get_policy(self, policy_id: str) -> Policy | None:
        """Retrieve a policy by ID."""
        return self._policies.get(policy_id)

    def list_policies(
        self,
        policy_type: PolicyType | None = None,
        status: PolicyStatus | None = None,
    ) -> list[Policy]:
        """List policies with optional filters."""
        policies = list(self._policies.values())
        if policy_type is not None:
            policies = [p for p in policies if p.policy_type == policy_type]
        if status is not None:
            policies = [p for p in policies if p.status == status]
        return policies

    def get_policy_report(self) -> dict[str, Any]:
        """Return a summary report of all policies.

        Returns:
            Dictionary with counts by type and status.
        """
        policies = list(self._policies.values())
        return {
            "total_policies": len(policies),
            "total_rules": sum(len(p.rules) for p in policies),
            "by_type": {
                pt.value: sum(1 for p in policies if p.policy_type == pt)
                for pt in PolicyType
            },
            "by_status": {
                ps.value: sum(1 for p in policies if p.status == ps)
                for ps in PolicyStatus
            },
        }


__all__ = [
    "PolicyType",
    "PolicyStatus",
    "PolicyRule",
    "Policy",
    "PolicyEngine",
]
