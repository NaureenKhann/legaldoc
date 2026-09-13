"""
Evaluation and scoring schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CategoryScore(BaseModel):
    category: str
    max_points: int
    earned_points: float = Field(ge=0.0)
    passed_checks: int
    failed_checks: int
    warnings: int
    deductions: list[str] = Field(
        default_factory=list, description="Reasons for point deductions"
    )
    explanation: str


SCORING_CATEGORIES: dict[str, int] = {
    "ENTITY_ACCURACY": 25,
    "COMPLETENESS": 20,
    "STRUCTURE": 20,
    "CONSISTENCY": 15,
    "TEMPLATE_FIDELITY": 10,
    "UNSUPPORTED_CONTENT": 10,
}


class EvaluationScore(BaseModel):
    overall_score: float = Field(ge=0.0, le=100.0)
    max_score: float = 100.0
    percentage: float = Field(ge=0.0, le=100.0)
    grade: str = Field(description="A/B/C/D/F label")
    categories: list[CategoryScore]
    critical_issues: int
    total_deductions: float
    scoring_explanation: str = Field(
        description="Plain-language explanation of the final score"
    )

    @classmethod
    def grade_from_score(cls, score: float) -> str:
        if score >= 90:
            return "A"
        if score >= 75:
            return "B"
        if score >= 60:
            return "C"
        if score >= 45:
            return "D"
        return "F"


class EvaluationReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    matter_id: str
    generation_run_id: str
    validation_run_id: str
    score: EvaluationScore
    category_breakdown: list[CategoryScore]
    all_issues: list[dict] = Field(
        description="All ValidationCheck items that FAILED or WARNING"
    )
    ai_review_warnings: list[str] = Field(
        default_factory=list,
        description="AI semantic review warnings — clearly labeled as AI-generated",
    )
    report_markdown: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EvaluationReportResponse(BaseModel):
    matter_id: str
    generation_run_id: str
    report: EvaluationReport
    download_url: Optional[str] = None
