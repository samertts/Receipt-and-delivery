"""
Platform Governance — Governance Review Engine

Phase 11: Platform Governance
Constitution: Principle 22 (No Release Without Certification), Principle 23 (No Deployment With Critical Findings)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class GovernanceReviewType(Enum):
    """Types of governance reviews."""
    SECURITY = "security"
    ARCHITECTURE = "architecture"
    PERFORMANCE = "performance"
    RECOVERY = "recovery"
    AUDIT = "audit"
    COMPLIANCE = "compliance"
    DEPLOYMENT = "deployment"


class ReviewStatus(Enum):
    """Status of a governance review."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class GovernanceReview:
    """A governance review with findings and status."""
    review_id: str
    review_type: GovernanceReviewType
    status: ReviewStatus = ReviewStatus.PENDING
    reviewer: str = ""
    findings: list[dict[str, Any]] = field(default_factory=list)
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "review_type": self.review_type.value,
            "status": self.status.value,
            "reviewer": self.reviewer,
            "findings": self.findings,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "notes": self.notes,
        }


class GovernanceEngine:
    """Manages governance reviews and deployment readiness."""

    def __init__(self) -> None:
        self._reviews: dict[str, GovernanceReview] = {}

    def create_review(
        self, review_id: str, review_type: GovernanceReviewType, reviewer: str
    ) -> GovernanceReview:
        """Create a new governance review."""
        review = GovernanceReview(
            review_id=review_id,
            review_type=review_type,
            reviewer=reviewer,
        )
        self._reviews[review_id] = review
        return review

    def complete_review(
        self, review_id: str, status: ReviewStatus, findings: list[dict[str, Any]]
    ) -> bool:
        """Complete a governance review with findings."""
        review = self.get_review(review_id)
        if not review:
            return False

        review.status = status
        review.findings = findings
        review.completed_at = datetime.utcnow()

        review.critical_count = sum(
            1 for f in findings if f.get("severity") == "critical"
        )
        review.high_count = sum(
            1 for f in findings if f.get("severity") == "high"
        )
        review.medium_count = sum(
            1 for f in findings if f.get("severity") == "medium"
        )
        review.low_count = sum(
            1 for f in findings if f.get("severity") == "low"
        )

        return True

    def get_review(self, review_id: str) -> GovernanceReview | None:
        """Get a review by ID."""
        return self._reviews.get(review_id)

    def list_reviews(
        self, review_type: GovernanceReviewType | None = None
    ) -> list[GovernanceReview]:
        """List reviews, optionally filtered by type."""
        reviews = list(self._reviews.values())
        if review_type:
            reviews = [r for r in reviews if r.review_type == review_type]
        return reviews

    def get_reviews_by_status(self, status: ReviewStatus) -> list[GovernanceReview]:
        """Get all reviews with a specific status."""
        return [r for r in self._reviews.values() if r.status == status]

    def has_blocking_findings(self, review_id: str) -> bool:
        """Check if a review has blocking findings (critical or high)."""
        review = self.get_review(review_id)
        if not review:
            return False
        return review.critical_count > 0 or review.high_count > 0

    def can_deploy(self, pilot_id: str | None = None) -> bool:
        """Check if deployment is allowed based on governance reviews."""
        reviews = self.list_reviews()
        if not reviews:
            return False

        for review in reviews:
            if review.status != ReviewStatus.PASSED:
                return False
            if self.has_blocking_findings(review.review_id):
                return False

        return True

    def get_governance_report(self) -> dict[str, Any]:
        """Get comprehensive governance report with statistics."""
        reviews = self.list_reviews()
        if not reviews:
            return {
                "total_reviews": 0,
                "status": "no_reviews",
                "can_deploy": False,
            }

        status_counts: dict[str, int] = {}
        for review in reviews:
            status = review.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        type_counts: dict[str, int] = {}
        for review in reviews:
            review_type = review.review_type.value
            type_counts[review_type] = type_counts.get(review_type, 0) + 1

        total_critical = sum(r.critical_count for r in reviews)
        total_high = sum(r.high_count for r in reviews)
        total_medium = sum(r.medium_count for r in reviews)
        total_low = sum(r.low_count for r in reviews)

        passed_reviews = [
            r for r in reviews if r.status == ReviewStatus.PASSED
        ]
        reviews_with_blocking = [
            r for r in passed_reviews if self.has_blocking_findings(r.review_id)
        ]

        can_deploy = self.can_deploy()

        return {
            "total_reviews": len(reviews),
            "status_distribution": status_counts,
            "type_distribution": type_counts,
            "findings_summary": {
                "critical": total_critical,
                "high": total_high,
                "medium": total_medium,
                "low": total_low,
            },
            "passed_reviews": len(passed_reviews),
            "reviews_with_blocking_findings": len(reviews_with_blocking),
            "can_deploy": can_deploy,
        }


__all__ = [
    "GovernanceReviewType",
    "ReviewStatus",
    "GovernanceReview",
    "GovernanceEngine",
]
