"""
Platform Registry — Base classes for all registries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class RegistryStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    PLANNED = "planned"


@dataclass
class RegistryEntry:
    """Base entry for all registries."""
    name: str
    version: str = "1.0.0"
    status: RegistryStatus = RegistryStatus.ACTIVE
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: tuple[str, ...] = ()
