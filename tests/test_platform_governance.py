"""Tests for unified_platform.governance — GovernanceEngine and related classes."""

from __future__ import annotations

from datetime import datetime


from unified_platform.governance import (
    GovernanceEngine,
    GovernanceReview,
    GovernanceReviewType,
    ReviewStatus,
)


class TestGovernanceReview:
    def test_creation_with_defaults(self):
        r = GovernanceReview(review_id="r1", review_type=GovernanceReviewType.SECURITY)
        assert r.review_id == "r1"
        assert r.review_type == GovernanceReviewType.SECURITY
        assert r.status == ReviewStatus.PENDING
        assert r.reviewer == ""
        assert r.findings == []
        assert r.critical_count == 0
        assert r.high_count == 0
        assert r.medium_count == 0
        assert r.low_count == 0
        assert isinstance(r.created_at, datetime)
        assert r.completed_at is None
        assert r.notes == ""

    def test_to_dict(self):
        r = GovernanceReview(
            review_id="r2",
            review_type=GovernanceReviewType.PERFORMANCE,
            reviewer="alice",
            status=ReviewStatus.PASSED,
            critical_count=1,
            high_count=2,
            notes="needs recheck",
        )
        d = r.to_dict()
        assert d["review_id"] == "r2"
        assert d["review_type"] == "performance"
        assert d["status"] == "passed"
        assert d["reviewer"] == "alice"
        assert d["critical_count"] == 1
        assert d["high_count"] == 2
        assert d["notes"] == "needs recheck"
        assert d["completed_at"] is None

    def test_to_dict_with_completed_at(self):
        r = GovernanceReview(review_id="r3", review_type=GovernanceReviewType.AUDIT)
        r.completed_at = datetime(2026, 1, 1, 12, 0, 0)
        d = r.to_dict()
        assert d["completed_at"] == "2026-01-01T12:00:00"


class TestGovernanceEngine:
    def test_create_review(self):
        eng = GovernanceEngine()
        review = eng.create_review("r1", GovernanceReviewType.SECURITY, "bob")
        assert review.review_id == "r1"
        assert review.review_type == GovernanceReviewType.SECURITY
        assert review.reviewer == "bob"
        assert review.status == ReviewStatus.PENDING

    def test_get_review(self):
        eng = GovernanceEngine()
        eng.create_review("r1", GovernanceReviewType.AUDIT, "carol")
        found = eng.get_review("r1")
        assert found is not None
        assert found.review_id == "r1"

    def test_get_review_nonexistent(self):
        eng = GovernanceEngine()
        assert eng.get_review("missing") is None

    def test_list_reviews_empty(self):
        eng = GovernanceEngine()
        assert eng.list_reviews() == []

    def test_list_reviews_with_type_filter(self):
        eng = GovernanceEngine()
        eng.create_review("r1", GovernanceReviewType.SECURITY, "a")
        eng.create_review("r2", GovernanceReviewType.AUDIT, "b")
        eng.create_review("r3", GovernanceReviewType.SECURITY, "c")

        security = eng.list_reviews(review_type=GovernanceReviewType.SECURITY)
        assert len(security) == 2
        assert all(r.review_type == GovernanceReviewType.SECURITY for r in security)

        audit = eng.list_reviews(review_type=GovernanceReviewType.AUDIT)
        assert len(audit) == 1

    def test_complete_review_passed(self):
        eng = GovernanceEngine()
        eng.create_review("r1", GovernanceReviewType.PERFORMANCE, "dave")
        result = eng.complete_review("r1", ReviewStatus.PASSED, [])
        assert result is True
        review = eng.get_review("r1")
        assert review.status == ReviewStatus.PASSED
        assert review.completed_at is not None

    def test_complete_review_failed(self):
        eng = GovernanceEngine()
        eng.create_review("r1", GovernanceReviewType.SECURITY, "eve")
        findings = [
            {"severity": "critical", "description": "SQL injection"},
            {"severity": "high", "description": "XSS"},
            {"severity": "medium", "description": "weak cipher"},
        ]
        result = eng.complete_review("r1", ReviewStatus.FAILED, findings)
        assert result is True
        review = eng.get_review("r1")
        assert review.status == ReviewStatus.FAILED
        assert review.critical_count == 1
        assert review.high_count == 1
        assert review.medium_count == 1
        assert review.low_count == 0

    def test_complete_review_nonexistent(self):
        eng = GovernanceEngine()
        result = eng.complete_review("missing", ReviewStatus.PASSED, [])
        assert result is False

    def test_get_reviews_by_status(self):
        eng = GovernanceEngine()
        eng.create_review("r1", GovernanceReviewType.SECURITY, "a")
        eng.create_review("r2", GovernanceReviewType.AUDIT, "b")
        eng.complete_review("r1", ReviewStatus.PASSED, [])
        eng.complete_review("r2", ReviewStatus.FAILED, [])

        passed = eng.get_reviews_by_status(ReviewStatus.PASSED)
        assert len(passed) == 1
        assert passed[0].review_id == "r1"

        failed = eng.get_reviews_by_status(ReviewStatus.FAILED)
        assert len(failed) == 1
        assert failed[0].review_id == "r2"

    def test_has_blocking_findings_no_findings(self):
        eng = GovernanceEngine()
        eng.create_review("r1", GovernanceReviewType.RECOVERY, "f")
        eng.complete_review("r1", ReviewStatus.PASSED, [])
        assert eng.has_blocking_findings("r1") is False

    def test_has_blocking_findings_with_critical(self):
        eng = GovernanceEngine()
        eng.create_review("r1", GovernanceReviewType.SECURITY, "g")
        findings = [{"severity": "critical", "description": "vuln"}]
        eng.complete_review("r1", ReviewStatus.FAILED, findings)
        assert eng.has_blocking_findings("r1") is True

    def test_has_blocking_findings_with_high(self):
        eng = GovernanceEngine()
        eng.create_review("r1", GovernanceReviewType.SECURITY, "h")
        findings = [{"severity": "high", "description": "issue"}]
        eng.complete_review("r1", ReviewStatus.FAILED, findings)
        assert eng.has_blocking_findings("r1") is True

    def test_has_blocking_findings_nonexistent(self):
        eng = GovernanceEngine()
        assert eng.has_blocking_findings("missing") is False

    def test_can_deploy_all_passed(self):
        eng = GovernanceEngine()
        eng.create_review("r1", GovernanceReviewType.SECURITY, "i")
        eng.create_review("r2", GovernanceReviewType.AUDIT, "j")
        eng.complete_review("r1", ReviewStatus.PASSED, [])
        eng.complete_review("r2", ReviewStatus.PASSED, [])
        assert eng.can_deploy() is True

    def test_can_deploy_has_blocking(self):
        eng = GovernanceEngine()
        eng.create_review("r1", GovernanceReviewType.SECURITY, "k")
        eng.complete_review("r1", ReviewStatus.PASSED, [{"severity": "critical", "description": "bad"}])
        assert eng.can_deploy() is False

    def test_can_deploy_has_failed_review(self):
        eng = GovernanceEngine()
        eng.create_review("r1", GovernanceReviewType.SECURITY, "l")
        eng.complete_review("r1", ReviewStatus.FAILED, [])
        assert eng.can_deploy() is False

    def test_can_deploy_no_reviews(self):
        eng = GovernanceEngine()
        assert eng.can_deploy() is False

    def test_get_governance_report(self):
        eng = GovernanceEngine()
        report = eng.get_governance_report()
        assert report["total_reviews"] == 0
        assert report["status"] == "no_reviews"
        assert report["can_deploy"] is False

    def test_get_governance_report_with_reviews(self):
        eng = GovernanceEngine()
        eng.create_review("r1", GovernanceReviewType.SECURITY, "m")
        eng.create_review("r2", GovernanceReviewType.AUDIT, "n")
        eng.complete_review("r1", ReviewStatus.PASSED, [{"severity": "low", "description": "minor"}])
        eng.complete_review("r2", ReviewStatus.FAILED, [
            {"severity": "critical", "description": "major"},
            {"severity": "high", "description": "bad"},
            {"severity": "medium", "description": "ok"},
        ])

        report = eng.get_governance_report()
        assert report["total_reviews"] == 2
        assert report["status_distribution"]["passed"] == 1
        assert report["status_distribution"]["failed"] == 1
        assert report["findings_summary"]["critical"] == 1
        assert report["findings_summary"]["high"] == 1
        assert report["findings_summary"]["medium"] == 1
        assert report["findings_summary"]["low"] == 1
        assert report["can_deploy"] is False
