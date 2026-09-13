"""
Scoring Engine — converts ValidationRunResult into EvaluationScore.
Transparent scoring: every deduction is documented.
"""
from __future__ import annotations

import structlog

from app.schemas.evaluation import CategoryScore, EvaluationScore, SCORING_CATEGORIES
from app.schemas.validation import (
    CheckCategory,
    CheckSeverity,
    CheckStatus,
    ValidationCheck,
    ValidationRunResult,
)

logger = structlog.get_logger(__name__)


class ScoringEngine:
    """
    Calculates category scores and overall score from validation check results.

    Scoring logic:
    - Each category starts at max points.
    - Each FAIL at ERROR severity deducts proportionally (max per check = max / check_count).
    - Each FAIL at WARNING severity deducts half the above.
    - PASS checks do not modify score.
    - No category goes below 0.
    - Unsupported content: each WARNING in that category deducts 2 points.
    """

    def score(self, validation_result: ValidationRunResult) -> EvaluationScore:
        log = logger.bind(run_id=validation_result.generation_run_id)
        log.info("scoring_start")

        checks_by_category: dict[str, list[ValidationCheck]] = {
            cat: [] for cat in SCORING_CATEGORIES
        }

        for check in validation_result.checks:
            cat = check.category.value if hasattr(check.category, "value") else check.category
            if cat in checks_by_category:
                checks_by_category[cat].append(check)

        category_scores: list[CategoryScore] = []
        total_earned = 0.0

        for category, max_pts in SCORING_CATEGORIES.items():
            checks = checks_by_category[category]
            if not checks:
                # No checks for this category — award full marks
                category_scores.append(
                    CategoryScore(
                        category=category,
                        max_points=max_pts,
                        earned_points=max_pts,
                        passed_checks=0,
                        failed_checks=0,
                        warnings=0,
                        deductions=[],
                        explanation=f"No checks defined for {category}. Full marks awarded.",
                    )
                )
                total_earned += max_pts
                continue

            error_checks = [
                c for c in checks
                if c.severity in (CheckSeverity.ERROR, "ERROR")
            ]
            points_per_error = max_pts / max(len(error_checks), 1)

            earned = float(max_pts)
            deductions: list[str] = []
            passed = 0
            failed = 0
            warns = 0

            for check in checks:
                if check.status in (CheckStatus.PASS, "PASS"):
                    passed += 1
                elif check.status in (CheckStatus.FAIL, "FAIL"):
                    failed += 1
                    severity = check.severity.value if hasattr(check.severity, "value") else check.severity
                    if severity == "ERROR":
                        deduction = points_per_error
                    elif severity == "WARNING":
                        deduction = points_per_error / 2
                    else:
                        deduction = 0.0

                    earned -= deduction
                    if deduction > 0:
                        deductions.append(
                            f"-{deduction:.1f}pt: {check.check_id} — {check.message}"
                        )
                elif check.status in (CheckStatus.WARNING, "WARNING"):
                    warns += 1
                    if category == "UNSUPPORTED_CONTENT":
                        earned -= 2.0
                        deductions.append(f"-2pt: {check.check_id} — {check.message}")

            earned = max(0.0, earned)
            total_earned += earned

            explanation = (
                f"{passed} passed, {failed} failed, {warns} warnings. "
                f"Earned {earned:.1f}/{max_pts} points."
            )
            if deductions:
                explanation += " Deductions: " + "; ".join(deductions[:3])

            category_scores.append(
                CategoryScore(
                    category=category,
                    max_points=max_pts,
                    earned_points=round(earned, 2),
                    passed_checks=passed,
                    failed_checks=failed,
                    warnings=warns,
                    deductions=deductions,
                    explanation=explanation,
                )
            )

        overall = min(100.0, round(total_earned, 2))
        percentage = overall  # max_score is 100

        grade = EvaluationScore.grade_from_score(overall)
        critical = len(validation_result.critical_failures)

        scoring_explanation = (
            f"Overall score: {overall:.1f}/100 ({grade}). "
            f"Critical failures: {critical}. "
            f"Passed: {validation_result.passed}/{validation_result.total_checks} checks. "
        )
        if critical:
            scoring_explanation += (
                f"Critical issues that must be addressed: {', '.join(validation_result.critical_failures[:5])}."
            )

        log.info("scoring_complete", score=overall, grade=grade)

        return EvaluationScore(
            overall_score=overall,
            percentage=percentage,
            grade=grade,
            categories=category_scores,
            critical_issues=critical,
            total_deductions=round(100.0 - overall, 2),
            scoring_explanation=scoring_explanation,
        )
