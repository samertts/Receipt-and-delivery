"""Tests for Phase 4: Policy Engine V7 — Extended policy types, versioning, audit."""
from __future__ import annotations

from unified_platform.policy import (
    PolicyAudit,
    PolicyEngineV2,
    PolicyRule,
    PolicyStatus,
    PolicyType,
    PolicyVersion,
)


class TestPolicyTypeV7:
    def test_new_policy_types_exist(self) -> None:
        assert PolicyType.REGULATORY.value == "regulatory"
        assert PolicyType.LABORATORY.value == "laboratory"
        assert PolicyType.WORKFORCE.value == "workforce"
        assert PolicyType.PRIVACY.value == "privacy"
        assert PolicyType.DATA_SOVEREIGNTY.value == "data_sovereignty"

    def test_all_policy_types_count(self) -> None:
        assert len(PolicyType) == 11


class TestPolicyVersion:
    def test_creation(self) -> None:
        v = PolicyVersion(version_id="v1", policy_id="p1", version=1, changes=["activated"])
        assert v.policy_id == "p1"
        assert v.changes == ["activated"]


class TestPolicyAudit:
    def test_creation(self) -> None:
        a = PolicyAudit(audit_id="a1", policy_id="p1", action="create", actor="admin")
        assert a.action == "create"
        assert a.actor == "admin"


class TestPolicyEngineV2:
    def test_create_policy(self) -> None:
        engine = PolicyEngineV2()
        p = engine.create_policy("p1", "Test", PolicyType.SECURITY)
        assert p.policy_id == "p1"
        assert p.status == PolicyStatus.DRAFT

    def test_activate_records_version(self) -> None:
        engine = PolicyEngineV2()
        engine.create_policy("p1", "Test", PolicyType.SECURITY)
        assert engine.activate_policy("p1") is True
        history = engine.get_policy_history("p1")
        assert len(history) == 1
        assert history[0].version == 1

    def test_deactivate_records_version(self) -> None:
        engine = PolicyEngineV2()
        engine.create_policy("p1", "Test", PolicyType.SECURITY)
        engine.activate_policy("p1")
        engine.deactivate_policy("p1")
        history = engine.get_policy_history("p1")
        assert len(history) == 2

    def test_audit_policy(self) -> None:
        engine = PolicyEngineV2()
        engine.create_policy("p1", "Test", PolicyType.SECURITY)
        audit = engine.audit_policy("p1", "created", "admin", "Initial creation")
        assert audit.action == "created"
        assert audit.actor == "admin"

    def test_get_policy_audits(self) -> None:
        engine = PolicyEngineV2()
        engine.create_policy("p1", "Test", PolicyType.SECURITY)
        engine.audit_policy("p1", "created", "admin")
        engine.audit_policy("p1", "updated", "admin")
        audits = engine.get_policy_audits("p1")
        assert len(audits) == 2

    def test_get_policy_audits_empty(self) -> None:
        engine = PolicyEngineV2()
        assert engine.get_policy_audits("nonexistent") == []

    def test_evaluate_all(self) -> None:
        engine = PolicyEngineV2()
        engine.create_policy("p1", "P1", PolicyType.SECURITY)
        engine.add_rule("p1", PolicyRule(rule_id="r1", condition="authenticated", action="allow"))
        engine.activate_policy("p1")
        engine.create_policy("p2", "P2", PolicyType.AUDIT)
        engine.add_rule("p2", PolicyRule(rule_id="r2", condition="logged", action="record"))
        engine.activate_policy("p2")
        results = engine.evaluate_all({"authenticated": True, "logged": True})
        assert results["p1"] is True
        assert results["p2"] is True

    def test_evaluate_all_with_failures(self) -> None:
        engine = PolicyEngineV2()
        engine.create_policy("p1", "P1", PolicyType.SECURITY)
        engine.add_rule("p1", PolicyRule(rule_id="r1", condition="mfa_enabled", action="allow"))
        engine.activate_policy("p1")
        results = engine.evaluate_all({})
        assert results["p1"] is False

    def test_compliance_report(self) -> None:
        engine = PolicyEngineV2()
        engine.create_policy("p1", "P1", PolicyType.SECURITY)
        engine.activate_policy("p1")
        engine.create_policy("p2", "P2", PolicyType.PRIVACY)
        engine.audit_policy("p1", "created", "admin")
        report = engine.get_compliance_report()
        assert report["total_policies"] == 2
        assert report["active_policies"] == 1
        assert report["total_audits"] == 1
        assert report["compliance_score"] == 50.0

    def test_new_policy_type_creation(self) -> None:
        engine = PolicyEngineV2()
        p = engine.create_policy("reg1", "Regulatory Policy", PolicyType.REGULATORY)
        assert p.policy_type == PolicyType.REGULATORY

    def test_laboratory_policy(self) -> None:
        engine = PolicyEngineV2()
        engine.create_policy("lab1", "Lab Policy", PolicyType.LABORATORY)
        engine.add_rule("lab1", PolicyRule(rule_id="r1", condition="accredited", action="operate"))
        engine.activate_policy("lab1")
        passed, actions = engine.evaluate("lab1", {"accredited": True})
        assert passed is True
        assert "operate" in actions
