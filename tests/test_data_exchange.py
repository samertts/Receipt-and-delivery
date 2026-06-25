"""Tests for Phase 3: National Data Exchange Bus."""
from __future__ import annotations


from unified_platform.data_exchange import (
    DataExchangeBus,
    EventCheckpoint,
    EventSeverity,
    EventType,
    PersistedEvent,
    RoutingRule,
)


class TestEnums:
    def test_event_type_values(self) -> None:
        assert EventType.SYSTEM.value == "system"
        assert EventType.DOMAIN.value == "domain"
        assert EventType.INTEGRATION.value == "integration"
        assert EventType.AUDIT.value == "audit"

    def test_event_severity_values(self) -> None:
        assert EventSeverity.INFO.value == "info"
        assert EventSeverity.WARNING.value == "warning"
        assert EventSeverity.ERROR.value == "error"
        assert EventSeverity.CRITICAL.value == "critical"


class TestDataclasses:
    def test_persisted_event_defaults(self) -> None:
        e = PersistedEvent()
        assert e.event_id
        assert e.event_type == EventType.SYSTEM
        assert e.severity == EventSeverity.INFO
        assert e.processed is False
        assert e.retry_count == 0

    def test_persisted_event_custom(self) -> None:
        e = PersistedEvent(
            event_type=EventType.AUDIT,
            severity=EventSeverity.CRITICAL,
            source="test",
            topic="receipts",
            payload={"id": 1},
        )
        assert e.event_type == EventType.AUDIT
        assert e.source == "test"
        assert e.topic == "receipts"

    def test_routing_rule_defaults(self) -> None:
        r = RoutingRule(rule_id="r1", source_pattern="*", topic_pattern="*", target_handler="h1")
        assert r.priority == 0
        assert r.enabled is True

    def test_event_checkpoint_defaults(self) -> None:
        c = EventCheckpoint(checkpoint_id="cp1")
        assert c.position == 0
        assert c.last_event_id == ""


class TestDataExchangeBus:
    def test_publish_event(self) -> None:
        bus = DataExchangeBus()
        e = PersistedEvent(topic="test")
        assert bus.publish_event(e) is True
        assert bus.get_event(e.event_id) is not None

    def test_get_event_missing(self) -> None:
        bus = DataExchangeBus()
        assert bus.get_event("nonexistent") is None

    def test_list_events_all(self) -> None:
        bus = DataExchangeBus()
        bus.publish_event(PersistedEvent(topic="a"))
        bus.publish_event(PersistedEvent(topic="b"))
        assert len(bus.list_events()) == 2

    def test_list_events_by_topic(self) -> None:
        bus = DataExchangeBus()
        bus.publish_event(PersistedEvent(topic="receipts"))
        bus.publish_event(PersistedEvent(topic="backups"))
        assert len(bus.list_events(topic="receipts")) == 1

    def test_list_events_by_type(self) -> None:
        bus = DataExchangeBus()
        bus.publish_event(PersistedEvent(event_type=EventType.SYSTEM))
        bus.publish_event(PersistedEvent(event_type=EventType.AUDIT))
        assert len(bus.list_events(event_type=EventType.AUDIT)) == 1

    def test_add_routing_rule(self) -> None:
        bus = DataExchangeBus()
        rule = RoutingRule(rule_id="r1", source_pattern="*", topic_pattern="*", target_handler="h1")
        assert bus.add_routing_rule(rule) is True

    def test_remove_routing_rule(self) -> None:
        bus = DataExchangeBus()
        bus.add_routing_rule(RoutingRule(rule_id="r1", source_pattern="*", topic_pattern="*", target_handler="h1"))
        assert bus.remove_routing_rule("r1") is True
        assert bus.remove_routing_rule("r1") is False

    def test_route_event_match(self) -> None:
        bus = DataExchangeBus()
        bus.add_routing_rule(
            RoutingRule(rule_id="r1", source_pattern="*", topic_pattern="receipt*", target_handler="handler1", priority=10)
        )
        bus.add_routing_rule(
            RoutingRule(rule_id="r2", source_pattern="*", topic_pattern="backup*", target_handler="handler2", priority=5)
        )
        e = PersistedEvent(source="svc", topic="receipts")
        handlers = bus.route_event(e)
        assert "handler1" in handlers
        assert "handler2" not in handlers

    def test_route_event_no_match(self) -> None:
        bus = DataExchangeBus()
        bus.add_routing_rule(
            RoutingRule(rule_id="r1", source_pattern="specific", topic_pattern="specific", target_handler="h1")
        )
        e = PersistedEvent(source="other", topic="other")
        assert bus.route_event(e) == []

    def test_route_disabled_rule_skipped(self) -> None:
        bus = DataExchangeBus()
        bus.add_routing_rule(
            RoutingRule(rule_id="r1", source_pattern="*", topic_pattern="*", target_handler="h1", enabled=False)
        )
        e = PersistedEvent(source="s", topic="t")
        assert bus.route_event(e) == []

    def test_create_checkpoint(self) -> None:
        bus = DataExchangeBus()
        bus.publish_event(PersistedEvent())
        cp = bus.create_checkpoint("cp1")
        assert cp.position == 1
        assert cp.last_event_id != ""

    def test_get_checkpoint(self) -> None:
        bus = DataExchangeBus()
        bus.create_checkpoint("cp1")
        cp = bus.get_checkpoint("cp1")
        assert cp is not None
        assert bus.get_checkpoint("cp2") is None

    def test_replay_from_checkpoint(self) -> None:
        bus = DataExchangeBus()
        bus.publish_event(PersistedEvent(topic="a"))
        bus.publish_event(PersistedEvent(topic="b"))
        bus.create_checkpoint("cp1")
        bus.publish_event(PersistedEvent(topic="c"))
        results: list[str] = []
        count = bus.replay_from_checkpoint("cp1", lambda e: results.append(e.topic) or True)
        assert count == 1
        assert results == ["c"]

    def test_get_bus_report(self) -> None:
        bus = DataExchangeBus()
        bus.publish_event(PersistedEvent(event_type=EventType.SYSTEM))
        bus.publish_event(PersistedEvent(event_type=EventType.AUDIT))
        bus.add_routing_rule(RoutingRule(rule_id="r1", source_pattern="*", topic_pattern="*", target_handler="h"))
        report = bus.get_bus_report()
        assert report["total_events"] == 2
        assert report["routing_rules"] == 1
        assert "system" in report["event_types"]
