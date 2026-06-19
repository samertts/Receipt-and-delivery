
from unified_platform.knowledge import (
    EntityType,
    KnowledgeEntity,
    KnowledgeGraph,
    KnowledgeRelationship,
    RelationshipType,
)


class TestEnums:
    def test_entity_type_values(self):
        assert EntityType.USER.value == "user"
        assert EntityType.ORGANIZATION.value == "organization"
        assert EntityType.LABORATORY.value == "laboratory"
        assert EntityType.ASSET.value == "asset"
        assert EntityType.RECEIPT.value == "receipt"
        assert EntityType.INVENTORY.value == "inventory"
        assert EntityType.TRAINING.value == "training"
        assert EntityType.SURVEILLANCE.value == "surveillance"

    def test_relationship_type_values(self):
        assert RelationshipType.OWNS.value == "owns"
        assert RelationshipType.MANAGES.value == "manages"
        assert RelationshipType.WORKS_AT.value == "works_at"
        assert RelationshipType.PROCESSES.value == "processes"
        assert RelationshipType.STORES.value == "stores"
        assert RelationshipType.TRAINED_BY.value == "trained_by"
        assert RelationshipType.MONITORED_BY.value == "monitored_by"


class TestDataclasses:
    def test_entity_defaults(self):
        e = KnowledgeEntity(entity_id="e1", entity_type=EntityType.USER, name="Alice")
        assert e.attributes == {}
        assert e.created_at is not None

    def test_relationship_defaults(self):
        r = KnowledgeRelationship(source_id="a", target_id="b", relationship_type=RelationshipType.OWNS)
        assert r.weight == 1.0
        assert r.attributes == {}


class TestKnowledgeGraph:
    def _graph(self):
        return KnowledgeGraph()

    def _user(self, eid="u1", name="Alice"):
        return KnowledgeEntity(entity_id=eid, entity_type=EntityType.USER, name=name)

    def _org(self, eid="o1", name="Acme"):
        return KnowledgeEntity(entity_id=eid, entity_type=EntityType.ORGANIZATION, name=name)

    def test_add_and_get_entity(self):
        g = self._graph()
        g.add_entity(self._user("u1", "Alice"))
        e = g.get_entity("u1")
        assert e is not None
        assert e.name == "Alice"
        assert e.entity_type == EntityType.USER

    def test_get_entity_missing(self):
        assert self._graph().get_entity("nope") is None

    def test_update_entity(self):
        g = self._graph()
        g.add_entity(self._user("u1", "Alice"))
        g.add_entity(self._user("u1", "Alicia"))
        assert g.get_entity("u1").name == "Alicia"

    def test_list_entities_all(self):
        g = self._graph()
        g.add_entity(self._user("u1"))
        g.add_entity(self._org("o1"))
        assert len(g.list_entities()) == 2

    def test_list_entities_by_type(self):
        g = self._graph()
        g.add_entity(self._user("u1"))
        g.add_entity(self._user("u2"))
        g.add_entity(self._org("o1"))
        users = g.list_entities(EntityType.USER)
        assert len(users) == 2

    def test_add_relationship(self):
        g = self._graph()
        g.add_entity(self._user("u1"))
        g.add_entity(self._org("o1"))
        added = g.add_relationship(
            KnowledgeRelationship(source_id="u1", target_id="o1", relationship_type=RelationshipType.WORKS_AT)
        )
        assert added is True

    def test_add_relationship_missing_entity(self):
        g = self._graph()
        g.add_entity(self._user("u1"))
        added = g.add_relationship(
            KnowledgeRelationship(source_id="u1", target_id="missing", relationship_type=RelationshipType.WORKS_AT)
        )
        assert added is False

    def test_get_relationships(self):
        g = self._graph()
        g.add_entity(self._user("u1"))
        g.add_entity(self._org("o1"))
        g.add_relationship(
            KnowledgeRelationship(source_id="u1", target_id="o1", relationship_type=RelationshipType.WORKS_AT)
        )
        rels = g.get_relationships("u1")
        assert len(rels) == 1
        assert rels[0].relationship_type == RelationshipType.WORKS_AT

    def test_get_relationships_by_type(self):
        g = self._graph()
        g.add_entity(self._user("u1"))
        g.add_entity(self._org("o1"))
        g.add_entity(self._org("o2"))
        g.add_relationship(
            KnowledgeRelationship(source_id="u1", target_id="o1", relationship_type=RelationshipType.WORKS_AT)
        )
        g.add_relationship(
            KnowledgeRelationship(source_id="u1", target_id="o2", relationship_type=RelationshipType.OWNS)
        )
        works = g.get_relationships("u1", RelationshipType.WORKS_AT)
        assert len(works) == 1

    def test_get_neighbors(self):
        g = self._graph()
        g.add_entity(self._user("u1"))
        g.add_entity(self._org("o1"))
        g.add_entity(self._org("o2"))
        g.add_relationship(
            KnowledgeRelationship(source_id="u1", target_id="o1", relationship_type=RelationshipType.WORKS_AT)
        )
        g.add_relationship(
            KnowledgeRelationship(source_id="u1", target_id="o2", relationship_type=RelationshipType.OWNS)
        )
        neighbors = g.get_neighbors("u1")
        assert neighbors == ["o1", "o2"]

    def test_find_path_direct(self):
        g = self._graph()
        g.add_entity(self._user("u1"))
        g.add_entity(self._org("o1"))
        g.add_relationship(
            KnowledgeRelationship(source_id="u1", target_id="o1", relationship_type=RelationshipType.WORKS_AT)
        )
        paths = g.find_path("u1", "o1")
        assert paths == [["u1", "o1"]]

    def test_find_path_indirect(self):
        g = self._graph()
        g.add_entity(self._user("u1"))
        g.add_entity(self._org("o1"))
        g.add_entity(self._org("o2"))
        g.add_relationship(
            KnowledgeRelationship(source_id="u1", target_id="o1", relationship_type=RelationshipType.WORKS_AT)
        )
        g.add_relationship(
            KnowledgeRelationship(source_id="o1", target_id="o2", relationship_type=RelationshipType.MANAGES)
        )
        paths = g.find_path("u1", "o2")
        assert paths == [["u1", "o1", "o2"]]

    def test_find_path_same_entity(self):
        g = self._graph()
        g.add_entity(self._user("u1"))
        assert g.find_path("u1", "u1") == [["u1"]]

    def test_find_path_no_path(self):
        g = self._graph()
        g.add_entity(self._user("u1"))
        g.add_entity(self._user("u2"))
        assert g.find_path("u1", "u2") == []

    def test_find_path_missing_entity(self):
        g = self._graph()
        assert g.find_path("a", "b") == []

    def test_entity_and_relationship_counts(self):
        g = self._graph()
        assert g.get_entity_count() == 0
        assert g.get_relationship_count() == 0
        g.add_entity(self._user("u1"))
        g.add_entity(self._org("o1"))
        g.add_relationship(
            KnowledgeRelationship(source_id="u1", target_id="o1", relationship_type=RelationshipType.WORKS_AT)
        )
        assert g.get_entity_count() == 2
        assert g.get_relationship_count() == 1

    def test_graph_stats(self):
        g = self._graph()
        g.add_entity(self._user("u1"))
        g.add_entity(self._org("o1"))
        g.add_relationship(
            KnowledgeRelationship(source_id="u1", target_id="o1", relationship_type=RelationshipType.WORKS_AT)
        )
        stats = g.get_graph_stats()
        assert stats["total_entities"] == 2
        assert stats["total_relationships"] == 1
        assert stats["entities_by_type"]["user"] == 1
        assert stats["entities_by_type"]["organization"] == 1
        assert stats["relationships_by_type"]["works_at"] == 1

    def test_graph_stats_empty(self):
        stats = self._graph().get_graph_stats()
        assert stats["total_entities"] == 0
        assert stats["total_relationships"] == 0

    def test_bidirectional_neighbors(self):
        g = self._graph()
        g.add_entity(self._user("u1"))
        g.add_entity(self._org("o1"))
        g.add_relationship(
            KnowledgeRelationship(source_id="o1", target_id="u1", relationship_type=RelationshipType.MANAGES)
        )
        neighbors = g.get_neighbors("u1")
        assert "o1" in neighbors
        neighbors = g.get_neighbors("o1")
        assert "u1" in neighbors
