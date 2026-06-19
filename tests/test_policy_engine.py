
from unified_platform.policy import (
    Policy,
    PolicyEngine,
    PolicyRule,
    PolicyStatus,
    PolicyType,
)


class TestEnums:
    def test_policy_type_values(self):
        assert PolicyType.SECURITY.value == "security"
        assert PolicyType.ACCESS_CONTROL.value == "access_control"
        assert PolicyType.DATA_RETENTION.value == "data_retention"
        assert PolicyType.AUDIT.value == "audit"
        assert PolicyType.BACKUP.value == "backup"
        assert PolicyType.COMPLIANCE.value == "compliance"

    def test_policy_status_values(self):
        assert PolicyStatus.DRAFT.value == "draft"
        assert PolicyStatus.ACTIVE.value == "active"
        assert PolicyStatus.DEPRECATED.value == "deprecated"
        assert PolicyStatus.ENFORCED.value == "enforced"


class TestPolicyDataclass:
    def test_defaults(self):
        p = Policy(policy_id="p1", name="Test", policy_type=PolicyType.SECURITY)
        assert p.status == PolicyStatus.DRAFT
        assert p.rules == []
        assert p.version == 1
        assert p.description == ""

    def test_rule_defaults(self):
        r = PolicyRule(rule_id="r1", condition="is_admin", action="deny")
        assert r.priority == 0
        assert r.enabled is True


class TestPolicyEngine:
    def _engine(self):
        return PolicyEngine()

    def _rule(self, rid="r1", condition="is_admin", action="deny", priority=0, enabled=True):
        return PolicyRule(rule_id=rid, condition=condition, action=action, priority=priority, enabled=enabled)

    def test_create_policy(self):
        engine = self._engine()
        p = engine.create_policy("p1", "Security Policy", PolicyType.SECURITY, "desc")
        assert p.policy_id == "p1"
        assert p.status == PolicyStatus.DRAFT
        assert p.description == "desc"

    def test_get_policy(self):
        engine = self._engine()
        engine.create_policy("p1", "Pol", PolicyType.AUDIT)
        assert engine.get_policy("p1") is not None
        assert engine.get_policy("missing") is None

    def test_add_rule(self):
        engine = self._engine()
        engine.create_policy("p1", "Pol", PolicyType.SECURITY)
        assert engine.add_rule("p1", self._rule()) is True
        assert len(engine.get_policy("p1").rules) == 1

    def test_add_rule_missing_policy(self):
        engine = self._engine()
        assert engine.add_rule("nope", self._rule()) is False

    def test_remove_rule(self):
        engine = self._engine()
        engine.create_policy("p1", "Pol", PolicyType.SECURITY)
        engine.add_rule("p1", self._rule(rid="r1"))
        engine.add_rule("p1", self._rule(rid="r2"))
        assert engine.remove_rule("p1", "r1") is True
        assert len(engine.get_policy("p1").rules) == 1
        assert engine.get_policy("p1").rules[0].rule_id == "r2"

    def test_remove_rule_not_found(self):
        engine = self._engine()
        engine.create_policy("p1", "Pol", PolicyType.SECURITY)
        assert engine.remove_rule("p1", "nonexistent") is False

    def test_activate_policy(self):
        engine = self._engine()
        engine.create_policy("p1", "Pol", PolicyType.BACKUP)
        assert engine.activate_policy("p1") is True
        assert engine.get_policy("p1").status == PolicyStatus.ACTIVE

    def test_activate_enforced_fails(self):
        engine = self._engine()
        engine.create_policy("p1", "Pol", PolicyType.BACKUP)
        engine._policies["p1"].status = PolicyStatus.ENFORCED
        assert engine.activate_policy("p1") is False

    def test_deactivate_policy(self):
        engine = self._engine()
        engine.create_policy("p1", "Pol", PolicyType.AUDIT)
        engine.activate_policy("p1")
        assert engine.deactivate_policy("p1") is True
        assert engine.get_policy("p1").status == PolicyStatus.DEPRECATED

    def test_deactivate_draft_fails(self):
        engine = self._engine()
        engine.create_policy("p1", "Pol", PolicyType.AUDIT)
        assert engine.deactivate_policy("p1") is False

    def test_evaluate_all_conditions_met(self):
        engine = self._engine()
        engine.create_policy("p1", "Pol", PolicyType.ACCESS_CONTROL)
        engine.add_rule("p1", self._rule(condition="is_admin", action="grant_access", priority=10))
        engine.add_rule("p1", self._rule(rid="r2", condition="has_token", action="allow", priority=5))
        passed, actions = engine.evaluate("p1", {"is_admin": True, "has_token": True})
        assert passed is True
        assert "grant_access" in actions
        assert "allow" in actions

    def test_evaluate_condition_not_met(self):
        engine = self._engine()
        engine.create_policy("p1", "Pol", PolicyType.ACCESS_CONTROL)
        engine.add_rule("p1", self._rule(condition="is_admin", action="deny"))
        passed, actions = engine.evaluate("p1", {"other": True})
        assert passed is False
        assert actions == []

    def test_evaluate_disabled_rule_ignored(self):
        engine = self._engine()
        engine.create_policy("p1", "Pol", PolicyType.COMPLIANCE)
        engine.add_rule("p1", self._rule(condition="encrypted", action="allow", enabled=False))
        passed, actions = engine.evaluate("p1", {"encrypted": True})
        assert passed is True
        assert actions == []

    def test_evaluate_missing_policy(self):
        engine = self._engine()
        passed, actions = engine.evaluate("nope", {})
        assert passed is False
        assert actions == []

    def test_list_policies_by_type(self):
        engine = self._engine()
        engine.create_policy("p1", "Sec", PolicyType.SECURITY)
        engine.create_policy("p2", "Aud", PolicyType.AUDIT)
        engine.create_policy("p3", "Sec2", PolicyType.SECURITY)
        sec = engine.list_policies(policy_type=PolicyType.SECURITY)
        assert len(sec) == 2

    def test_list_policies_by_status(self):
        engine = self._engine()
        engine.create_policy("p1", "A", PolicyType.SECURITY)
        engine.create_policy("p2", "B", PolicyType.AUDIT)
        engine.activate_policy("p2")
        active = engine.list_policies(status=PolicyStatus.ACTIVE)
        assert len(active) == 1
        assert active[0].policy_id == "p2"

    def test_policy_report(self):
        engine = self._engine()
        engine.create_policy("p1", "A", PolicyType.SECURITY)
        engine.create_policy("p2", "B", PolicyType.AUDIT)
        engine.activate_policy("p1")
        engine.add_rule("p2", self._rule())
        report = engine.get_policy_report()
        assert report["total_policies"] == 2
        assert report["total_rules"] == 1
        assert report["by_status"]["active"] == 1
        assert report["by_status"]["draft"] == 1
