"""
Evaluation Reporter — generates JSON and Markdown reports from evaluation results.
"""
from __future__ import annotations

from datetime import datetime

import structlog

from app.schemas.evaluation import EvaluationReport, EvaluationScore
from app.schemas.validation import CheckStatus, ValidationRunResult

logger = structlog.get_logger(__name__)


class EvaluationReporter:
    def generate_report(
        self,
        matter_id: str,
        generation_run_id: str,
        validation_run_id: str,
        validation_result: ValidationRunResult,
        score: EvaluationScore,
    ) -> EvaluationReport:
        log = logger.bind(matter_id=matter_id, run_id=generation_run_id)
        log.info("report_generation_start")

        all_issues = [
            c.model_dump()
            for c in validation_result.checks
            if c.status in (CheckStatus.FAIL, "FAIL", CheckStatus.WARNING, "WARNING")
        ]

        markdown = self._build_markdown(
            matter_id=matter_id,
            generation_run_id=generation_run_id,
            score=score,
            validation_result=validation_result,
            all_issues=all_issues,
        )

        report = EvaluationReport(
            matter_id=matter_id,
            generation_run_id=generation_run_id,
            validation_run_id=validation_run_id,
            score=score,
            category_breakdown=score.categories,
            all_issues=all_issues,
            ai_review_warnings=validation_result.ai_review_warnings,
            report_markdown=markdown,
            created_at=datetime.utcnow(),
        )

        log.info("report_complete", score=score.overall_score)
        return report

    @staticmethod
    def _build_markdown(
        matter_id: str,
        generation_run_id: str,
        score: EvaluationScore,
        validation_result: ValidationRunResult,
        all_issues: list[dict],
    ) -> str:
        lines: list[str] = []

        # Header
        lines.append("# LegalDoc Intelligence Platform — Evaluation Report")
        lines.append(f"\n**Matter ID:** `{matter_id}`")
        lines.append(f"**Generation Run:** `{generation_run_id}`")
        lines.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

        # Score Summary
        lines.append("\n---\n\n## Overall Score\n")
        grade_emoji = {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴", "F": "❌"}.get(score.grade, "")
        lines.append(
            f"### {grade_emoji} **{score.overall_score:.1f} / 100** — Grade {score.grade}"
        )
        lines.append(f"\n{score.scoring_explanation}\n")

        # Stats table
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Checks | {validation_result.total_checks} |")
        lines.append(f"| Passed | ✅ {validation_result.passed} |")
        lines.append(f"| Failed | ❌ {validation_result.failed} |")
        lines.append(f"| Warnings | ⚠️ {validation_result.warnings} |")
        lines.append(f"| Critical Issues | 🔴 {score.critical_issues} |")

        # Category Scores
        lines.append("\n---\n\n## Category Scores\n")
        lines.append("| Category | Score | Max | Grade |")
        lines.append("|----------|-------|-----|-------|")
        for cat in score.categories:
            pct = (cat.earned_points / cat.max_points * 100) if cat.max_points else 0
            bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
            lines.append(
                f"| **{cat.category.replace('_', ' ').title()}** | "
                f"{cat.earned_points:.1f} | {cat.max_points} | `{bar}` |"
            )

        # Issues
        if all_issues:
            lines.append("\n---\n\n## Issues Detected\n")
            errors = [i for i in all_issues if i.get("status") == "FAIL"]
            warnings = [i for i in all_issues if i.get("status") == "WARNING"]

            if errors:
                lines.append("### ❌ Failures\n")
                for issue in errors:
                    lines.append(f"**{issue['check_id']}** ({issue['category']})")
                    lines.append(f"- Message: {issue['message']}")
                    if issue.get("expected"):
                        lines.append(f"- Expected: `{issue['expected']}`")
                    if issue.get("actual"):
                        lines.append(f"- Actual: `{issue['actual']}`")
                    if issue.get("suggested_correction"):
                        lines.append(f"- Fix: {issue['suggested_correction']}")
                    lines.append(f"- Rule: *{issue['source_rule']}*\n")

            if warnings:
                lines.append("### ⚠️ Warnings\n")
                for issue in warnings:
                    lines.append(f"**{issue['check_id']}** — {issue['message']}")
                    if issue.get("suggested_correction"):
                        lines.append(f"  - Fix: {issue['suggested_correction']}")
                    lines.append("")

        # AI Review
        if validation_result.ai_review_warnings:
            lines.append("\n---\n\n## AI Semantic Review ⚠️\n")
            lines.append(
                "> **Note:** The following are AI-generated advisory warnings. "
                "They supplement but do NOT override the deterministic checks above.\n"
            )
            for warning in validation_result.ai_review_warnings:
                lines.append(f"- {warning}")

        # Footer
        lines.append("\n---")
        lines.append(
            "\n*Generated by LegalDoc Intelligence Platform. "
            "This report is for review purposes only. "
            "Generated documents are NOT ready for filing without human review.*"
        )

        return "\n".join(lines)
