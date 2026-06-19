"""
Platform AI — Base contracts for AI operations.

Phase 4: AI Operations Assistant
Constitution: Principle 33 (AI Governance), Principle 34 (Explainable AI)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AIRecommendationType(Enum):
    ERROR_ANALYSIS = "error_analysis"
    ROOT_CAUSE = "root_cause"
    LOG_ANALYSIS = "log_analysis"
    PERFORMANCE = "performance"
    SECURITY = "security"
    BACKUP = "backup"
    RECOVERY = "recovery"
    CAPACITY = "capacity"
    RISK_PREDICTION = "risk_prediction"
    ARCHITECTURE = "architecture"
    TECHNICAL_DEBT = "technical_debt"
    DEPLOYMENT_READINESS = "deployment_readiness"


class ConfidenceLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class AIRecommendation:
    """An AI-generated recommendation with explanation and evidence."""
    recommendation_id: str
    type: AIRecommendationType
    title: str
    summary: str
    explanation: str
    evidence: list[str] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    suggested_actions: list[str] = field(default_factory=list)
    affected_components: list[str] = field(default_factory=list)
    risk_level: str = "medium"
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.recommendation_id,
            "type": self.type.value,
            "title": self.title,
            "summary": self.summary,
            "explanation": self.explanation,
            "evidence": self.evidence,
            "confidence": self.confidence.value,
            "suggested_actions": self.suggested_actions,
            "affected_components": self.affected_components,
            "risk_level": self.risk_level,
            "created_at": self.created_at.isoformat(),
        }


from unified_platform.ai.assistant import AIAssistant, AIAnalysisReport  # noqa: E402

__all__ = [
    "AIRecommendationType",
    "ConfidenceLevel",
    "AIRecommendation",
    "AIAssistant",
    "AIAnalysisReport",
]
