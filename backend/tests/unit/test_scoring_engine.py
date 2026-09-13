"""Tests for the scoring engine."""
from __future__ import annotations

import pytest
from app.schemas.validation import (
    CheckCategory,
    CheckSeverity,
    CheckStatus,
    ValidationCheck,
    ValidationRunResult,
)
from app.services.scoring.engine import ScoringEngine


def make_validation_result(checks: list[ValidationCheck]) -> ValidationRunResult:
    passed = sum(1 for c in checks if c.status == CheckStatus.PASS)
    failed = sum(1 for c in checks if c.status == CheckStatus.FAIL)
    warnings = sum(1 for c in checks if c.status == CheckStatus.WARNING)
    critical = [c.check_id for c in checks if c.status == CheckStatus.FAIL and c.severity == CheckSeverity.ERROR]

    return ValidationRunResult(
        generation_run_id="test-run",
        checks=checks,
        total_checks=len(checks),
        passed=passed,
        failed=failed,
        warnings=warnings,
        not_applicable=0,
        critical_failures=critical,
    )


def make_check(
    check_id: str,
    status: CheckStatus,
    category: CheckCategory,
    severity: CheckSeverity = CheckSeverity.ERROR,
) -> ValidationCheck:
    return ValidationCheck(
        check_id=check_id,
        category=category,
        status=status,
        severity=severity,
        message="Test check",
        source_rule="Test rule",
    )


class TestScoringEngine:
    def setup_method(self):
        self.engine = ScoringEngine()

    def test_perfect_score_all_pass(self):
        checks = [
            make_check(f"CHECK_{i}", CheckStatus.PASS, CheckCategory.ENTITY_ACCURACY)
            for i in range(5)
        ]
        result = make_validation_result(checks)
        score = self.engine.score(result)
        # Entity accuracy should be full marks (or close)
        cat = next(c for c in score.categories if c.category == "ENTITY_ACCURACY")
        assert cat.earned_points == cat.max_points

    def test_all_fail_gives_low_score(self):
        checks = [
            make_check(f"CHECK_{i}", CheckStatus.FAIL, CheckCategory.ENTITY_ACCURACY)
            for i in range(5)
        ]
        result = make_validation_result(checks)
        score = self.engine.score(result)
        cat = next(c for c in score.categories if c.category == "ENTITY_ACCURACY")
        assert cat.earned_points == 0.0

    def test_score_never_exceeds_100(self):
        checks = [
            make_check(f"CHECK_{i}", CheckStatus.PASS, CheckCategory.COMPLETENESS)
            for i in range(10)
        ]
        result = make_validation_result(checks)
        score = self.engine.score(result)
        assert score.overall_score <= 100.0

    def test_score_never_below_0(self):
        checks = [
            make_check(f"CHECK_{i}", CheckStatus.FAIL, cat, CheckSeverity.ERROR)
            for i, cat in enumerate(
                [c for c in CheckCategory.__members__.values()] * 5
            )
        ]
        result = make_validation_result(checks)
        score = self.engine.score(result)
        assert score.overall_score >= 0.0
        for cat in score.categories:
            assert cat.earned_points >= 0.0

    def test_grade_assignment(self):
        from app.schemas.evaluation import EvaluationScore
        assert EvaluationScore.grade_from_score(95) == "A"
        assert EvaluationScore.grade_from_score(80) == "B"
        assert EvaluationScore.grade_from_score(65) == "C"
        assert EvaluationScore.grade_from_score(50) == "D"
        assert EvaluationScore.grade_from_score(30) == "F"

    def test_deductions_documented(self):
        checks = [
            make_check("CASE_NUMBER_CONSISTENT", CheckStatus.FAIL, CheckCategory.CONSISTENCY),
        ]
        result = make_validation_result(checks)
        score = self.engine.score(result)
        cat = next(c for c in score.categories if c.category == "CONSISTENCY")
        assert len(cat.deductions) > 0
        assert "CASE_NUMBER_CONSISTENT" in cat.deductions[0]

    def test_warning_severity_half_deduction(self):
        checks_error = [
            make_check("CHECK_1", CheckStatus.FAIL, CheckCategory.STRUCTURE, CheckSeverity.ERROR)
        ]
        checks_warning = [
            make_check("CHECK_1", CheckStatus.FAIL, CheckCategory.STRUCTURE, CheckSeverity.WARNING)
        ]
        score_error = self.engine.score(make_validation_result(checks_error))
        score_warning = self.engine.score(make_validation_result(checks_warning))
        cat_error = next(c for c in score_error.categories if c.category == "STRUCTURE")
        cat_warning = next(c for c in score_warning.categories if c.category == "STRUCTURE")
        # Warning should deduct less than error
        assert cat_warning.earned_points > cat_error.earned_points
