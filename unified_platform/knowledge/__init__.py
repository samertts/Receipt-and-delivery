"""
Platform Knowledge Graph — Entity-relationship graph for organizational,
laboratory, asset, and operational knowledge representation.

Phase 18: Knowledge Graph
Constitution: Principle 8 (AI Readiness),
              Principle 12 (Shared Data Contracts),
              Principle 13 (National Platform Compatibility)
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# ============================================================================
# Enums
# ============================================================================

class EntityType(Enum):
    """Types of entities represented in the knowledge graph."""
    USER = "user"
    ORGANIZATION = "organization"
    LABORATORY = "laboratory"
    ASSET = "asset"
    RECEIPT = "receipt"
    INVENTORY = "inventory"
    TRAINING = "training"
    SURVEILLANCE = "surveillance"


class RelationshipType(Enum):
    """Types of relationships between entities."""
    OWNS = "owns"
    MANAGES = "manages"
    WORKS_AT = "works_at"
    PROCESSES = "processes"
    STORES = "stores"
    TRAINED_BY = "trained_by"
    MONITORED_BY = "monitored_by"


# ============================================================================
# Data Contracts
# ============================================================================

@dataclass
class KnowledgeEntity:
    """A node in the knowledge graph."""
    entity_id: str
    entity_type: EntityType
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class KnowledgeRelationship:
    """A directed edge between two entities."""
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    attributes: dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0


# ============================================================================
# Knowledge Graph
# ============================================================================

class KnowledgeGraph:
    """In-memory knowledge graph supporting entities, relationships,
    neighbor queries, and path-finding.

    Designed for future integration with AI and graph-database backends.
    """

    def __init__(self) -> None:
        self._entities: dict[str, KnowledgeEntity] = {}
        self._relationships: list[KnowledgeRelationship] = []
        self._adjacency: dict[str, list[int]] = {}  # entity_id -> relationship indices

    def add_entity(self, entity: KnowledgeEntity) -> None:
        """Add or update an entity in the graph.

        Args:
            entity: The entity to store.
        """
        self._entities[entity.entity_id] = entity

    def get_entity(self, entity_id: str) -> KnowledgeEntity | None:
        """Retrieve an entity by ID."""
        return self._entities.get(entity_id)

    def list_entities(self, entity_type: EntityType | None = None) -> list[KnowledgeEntity]:
        """List entities, optionally filtered by type."""
        entities = list(self._entities.values())
        if entity_type is not None:
            entities = [e for e in entities if e.entity_type == entity_type]
        return entities

    def add_relationship(self, relationship: KnowledgeRelationship) -> bool:
        """Add a directed relationship between two entities.

        Args:
            relationship: The relationship to store.

        Returns:
            True if both source and target entities exist.
        """
        if (
            relationship.source_id not in self._entities
            or relationship.target_id not in self._entities
        ):
            return False

        idx = len(self._relationships)
        self._relationships.append(relationship)

        self._adjacency.setdefault(relationship.source_id, []).append(idx)
        self._adjacency.setdefault(relationship.target_id, []).append(idx)
        return True

    def get_relationships(
        self,
        entity_id: str,
        rel_type: RelationshipType | None = None,
    ) -> list[KnowledgeRelationship]:
        """Get all relationships involving an entity, optionally filtered by type."""
        indices = self._adjacency.get(entity_id, [])
        rels = [self._relationships[i] for i in indices]
        if rel_type is not None:
            rels = [r for r in rels if r.relationship_type == rel_type]
        return rels

    def get_neighbors(self, entity_id: str) -> list[str]:
        """Return IDs of all entities directly connected to the given entity."""
        neighbor_ids: set[str] = set()
        for rel in self.get_relationships(entity_id):
            if rel.source_id != entity_id:
                neighbor_ids.add(rel.source_id)
            if rel.target_id != entity_id:
                neighbor_ids.add(rel.target_id)
        return sorted(neighbor_ids)

    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5,
    ) -> list[list[str]]:
        """Find all paths between source and target up to max_depth hops.

        Uses BFS and returns a list of paths, where each path is a list
        of entity IDs from source to target.

        Args:
            source_id: Starting entity.
            target_id: Destination entity.
            max_depth: Maximum number of hops.

        Returns:
            List of paths found.
        """
        if source_id not in self._entities or target_id not in self._entities:
            return []

        if source_id == target_id:
            return [[source_id]]

        paths: list[list[str]] = []
        queue: deque[tuple[str, list[str]]] = deque([(source_id, [source_id])])

        while queue:
            current, path = queue.popleft()
            if len(path) > max_depth:
                continue

            for neighbor_id in self.get_neighbors(current):
                if neighbor_id == target_id:
                    paths.append(path + [neighbor_id])
                elif neighbor_id not in path:
                    queue.append((neighbor_id, path + [neighbor_id]))

        return paths

    def get_entity_count(self) -> int:
        """Return the total number of entities."""
        return len(self._entities)

    def get_relationship_count(self) -> int:
        """Return the total number of relationships."""
        return len(self._relationships)

    def get_graph_stats(self) -> dict[str, Any]:
        """Return summary statistics about the knowledge graph.

        Returns:
            Dictionary with entity/relationship counts and type breakdowns.
        """
        return {
            "total_entities": self.get_entity_count(),
            "total_relationships": self.get_relationship_count(),
            "entities_by_type": {
                et.value: sum(1 for e in self._entities.values() if e.entity_type == et)
                for et in EntityType
            },
            "relationships_by_type": {
                rt.value: sum(1 for r in self._relationships if r.relationship_type == rt)
                for rt in RelationshipType
            },
        }


__all__ = [
    "EntityType",
    "RelationshipType",
    "KnowledgeEntity",
    "KnowledgeRelationship",
    "KnowledgeGraph",
]
