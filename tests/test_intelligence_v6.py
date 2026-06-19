"""
Tests for Intelligence Score Calculators — v6

Covers: UserExperienceScoreCalculator, DeploymentScoreCalculator
"""

from __future__ import annotations

from unified_platform.intelligence.scores import (
    DeploymentScoreCalculator,
    ScoreLevel,
    UserExperienceScoreCalculator,
)


# ---------------------------------------------------------------------------
# 1. TestUserExperienceScoreCalculator
# ---------------------------------------------------------------------------
class TestUserExperienceScoreCalculator:
    def setup_method(self) -> None:
        self.calc = UserExperienceScoreCalculator()

    def test_perfect_scores(self) -> None:
        result = self.calc.calculate(
            response_time_ms=200,
            error_rate_percent=0.1,
            task_completion_rate=0.99,
            user_satisfaction=5.0,
            load_time_ms=500,
        )
        assert result.score == 100.0
        assert result.level == ScoreLevel.EXCELLENT
        assert result.category == "user_experience"
        assert result.recommendations == []

    def test_all_critical(self) -> None:
        result = self.calc.calculate(
            response_time_ms=5000,
            error_rate_percent=15.0,
            task_completion_rate=0.2,
            user_satisfaction=1.0,
            load_time_ms=10000,
        )
        assert result.score == 0.0
        assert result.level == ScoreLevel.CRITICAL
        assert len(result.recommendations) >= 5

    def test_response_time_degradation(self) -> None:
        result = self.calc.calculate(
            response_time_ms=1500,
            error_rate_percent=0.0,
            task_completion_rate=1.0,
            user_satisfaction=5.0,
            load_time_ms=0,
        )
        assert result.score == 85.0
        assert result.level == ScoreLevel.GOOD
        assert any("Response time high" in r for r in result.recommendations)

    def test_error_rate_penalized(self) -> None:
        result = self.calc.calculate(
            response_time_ms=0,
            error_rate_percent=7.0,
            task_completion_rate=1.0,
            user_satisfaction=5.0,
            load_time_ms=0,
        )
        assert result.score == 85.0
        assert any("Error rate high" in r for r in result.recommendations)

    def test_task_completion_low(self) -> None:
        result = self.calc.calculate(
            response_time_ms=0,
            error_rate_percent=0.0,
            task_completion_rate=0.4,
            user_satisfaction=5.0,
            load_time_ms=0,
        )
        assert result.score == 80.0
        assert any("Task completion rate critically low" in r for r in result.recommendations)

    def test_satisfaction_low(self) -> None:
        result = self.calc.calculate(
            response_time_ms=0,
            error_rate_percent=0.0,
            task_completion_rate=1.0,
            user_satisfaction=2.5,
            load_time_ms=0,
        )
        assert result.score == 90.0
        assert any("User satisfaction low" in r for r in result.recommendations)

    def test_load_time_penalized(self) -> None:
        result = self.calc.calculate(
            response_time_ms=0,
            error_rate_percent=0.0,
            task_completion_rate=1.0,
            user_satisfaction=5.0,
            load_time_ms=4000,
        )
        assert result.score == 90.0
        assert any("Load time high" in r for r in result.recommendations)

    def test_details_populated(self) -> None:
        result = self.calc.calculate(
            response_time_ms=100,
            error_rate_percent=0.5,
            task_completion_rate=0.95,
            user_satisfaction=4.5,
            load_time_ms=1000,
        )
        assert "response_time_ms" in result.details
        assert "error_rate_percent" in result.details
        assert "task_completion_rate" in result.details
        assert "user_satisfaction" in result.details
        assert "load_time_ms" in result.details

    def test_mixed_medium_score(self) -> None:
        result = self.calc.calculate(
            response_time_ms=800,
            error_rate_percent=2.0,
            task_completion_rate=0.85,
            user_satisfaction=3.5,
            load_time_ms=2500,
        )
        assert 50 <= result.score <= 80
        assert result.level in (ScoreLevel.MEDIUM, ScoreLevel.GOOD)
        assert len(result.recommendations) == 5


# ---------------------------------------------------------------------------
# 2. TestDeploymentScoreCalculator
# ---------------------------------------------------------------------------
class TestDeploymentScoreCalculator:
    def setup_method(self) -> None:
        self.calc = DeploymentScoreCalculator()

    def test_perfect_deployment(self) -> None:
        result = self.calc.calculate(
            test_pass_rate=1.0,
            coverage_percent=95.0,
            lint_errors=0,
            security_findings_high=0,
            security_findings_critical=0,
            rollback_available=True,
            deployment_history_success_rate=1.0,
        )
        assert result.score == 100.0
        assert result.level == ScoreLevel.EXCELLENT
        assert result.category == "deployment"
        assert result.recommendations == []

    def test_critical_security_findings(self) -> None:
        result = self.calc.calculate(
            test_pass_rate=1.0,
            coverage_percent=100.0,
            lint_errors=0,
            security_findings_high=0,
            security_findings_critical=2,
            rollback_available=True,
            deployment_history_success_rate=1.0,
        )
        assert result.score == 75.0
        assert result.level == ScoreLevel.GOOD
        assert any("Critical security" in r for r in result.recommendations)

    def test_low_test_pass_rate(self) -> None:
        result = self.calc.calculate(
            test_pass_rate=0.7,
            coverage_percent=100.0,
            lint_errors=0,
            security_findings_high=0,
            security_findings_critical=0,
            rollback_available=True,
            deployment_history_success_rate=1.0,
        )
        assert result.score == 80.0
        assert any("Test pass rate critically low" in r for r in result.recommendations)

    def test_no_rollback(self) -> None:
        result = self.calc.calculate(
            test_pass_rate=1.0,
            coverage_percent=100.0,
            lint_errors=0,
            security_findings_high=0,
            security_findings_critical=0,
            rollback_available=False,
            deployment_history_success_rate=1.0,
        )
        assert result.score == 90.0
        assert any("Rollback" in r for r in result.recommendations)

    def test_all_worst_case(self) -> None:
        result = self.calc.calculate(
            test_pass_rate=0.5,
            coverage_percent=30.0,
            lint_errors=30,
            security_findings_high=5,
            security_findings_critical=3,
            rollback_available=False,
            deployment_history_success_rate=0.5,
        )
        assert result.score == 0.0
        assert result.level == ScoreLevel.CRITICAL

    def test_details_populated(self) -> None:
        result = self.calc.calculate()
        assert "test_pass_rate" in result.details
        assert "coverage_percent" in result.details
        assert "lint_errors" in result.details
        assert "security_findings_high" in result.details
        assert "security_findings_critical" in result.details
        assert "rollback_available" in result.details
        assert "deployment_history_success_rate" in result.details

    def test_high_security_findings(self) -> None:
        result = self.calc.calculate(
            test_pass_rate=1.0,
            coverage_percent=100.0,
            lint_errors=0,
            security_findings_high=2,
            security_findings_critical=0,
            rollback_available=True,
            deployment_history_success_rate=1.0,
        )
        assert result.score == 85.0
        assert any("High security" in r for r in result.recommendations)

    def test_low_coverage_warning(self) -> None:
        result = self.calc.calculate(
            test_pass_rate=1.0,
            coverage_percent=75.0,
            lint_errors=0,
            security_findings_high=0,
            security_findings_critical=0,
            rollback_available=True,
            deployment_history_success_rate=1.0,
        )
        assert result.score == 95.0
        assert any("Coverage" in r for r in result.recommendations)

    def test_lint_errors_present(self) -> None:
        result = self.calc.calculate(
            test_pass_rate=1.0,
            coverage_percent=100.0,
            lint_errors=15,
            security_findings_high=0,
            security_findings_critical=0,
            rollback_available=True,
            deployment_history_success_rate=1.0,
        )
        assert result.score == 90.0
        assert any("Lint errors high" in r for r in result.recommendations)
