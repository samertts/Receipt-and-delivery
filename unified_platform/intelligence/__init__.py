"""
Platform Intelligence — Operational intelligence engine for the unified platform.
"""

from unified_platform.intelligence.scores import (
    BackupScoreCalculator,
    DataIntegrityScoreCalculator,
    HealthScoreCalculator,
    PerformanceScoreCalculator,
    RecoveryScoreCalculator,
    ReliabilityScoreCalculator,
    ScoreLevel,
    ScoreResult,
    SecurityScoreCalculator,
    SyncScoreCalculator,
)
from unified_platform.intelligence.engine import IntelligenceEngine, IntelligenceReport
from unified_platform.intelligence.self_improvement import (
    SelfImprovementEngine,
    Recommendation,
    RecommendationType,
    RiskLevel,
)

__all__ = [
    "BackupScoreCalculator",
    "DataIntegrityScoreCalculator",
    "HealthScoreCalculator",
    "PerformanceScoreCalculator",
    "RecoveryScoreCalculator",
    "ReliabilityScoreCalculator",
    "ScoreLevel",
    "ScoreResult",
    "SecurityScoreCalculator",
    "SyncScoreCalculator",
    "IntelligenceEngine",
    "IntelligenceReport",
    "SelfImprovementEngine",
    "Recommendation",
    "RecommendationType",
    "RiskLevel",
]
