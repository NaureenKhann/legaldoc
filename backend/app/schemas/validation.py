"""
Validation schemas — 25 deterministic checks, statuses, severities.
"""
from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class CheckSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class CheckCategory(str, Enum):
    ENTITY_ACCURACY = "ENTITY_ACCURACY"
    COMPLETENESS = "COMPLETENESS"
    STRUCTURE = "STRUCTURE"
    CONSISTENCY = "CONSISTENCY"
    TEMPLATE_FIDELITY = "TEMPLATE_FIDELITY"
    UNSUPPORTED_CONTENT = "UNSUPPORTED_CONTENT"


# ─── The 25 required check IDs ────────────────────────────────────────────────────

REQUIRED_CHECK_IDS: list[str] = [
    "REQUIRED_SECTIONS_PRESENT",
    "SECTION_ORDER_CORRECT",
    "COURT_HEADING_CONSISTENT",
    "JURISDICTION_CONSISTENT",
    "CASE_NUMBER_CONSISTENT",
    "YEAR_CONSISTENT",
    "PETITIONER_CONSISTENT",
    "RESPONDENT_NAMES_CONSISTENT",
    "ANSWERING_RESPONDENT_NUMBER_CONSISTENT",
    "DEPONENT_NAME_CONSISTENT",
    "DEPONENT_DESIGNATION_CONSISTENT",
    "ORG_DEPONENT_RELATIONSHIP_VALID",
    "PARAGRAPH_NUMBERING_SEQUENTIAL",
    "PRAYER_USES_LETTERS",
    "PRAYER_PRESENT",
    "EXHIBIT_REFERENCE_PRESENT",
    "JURAT_PRESENT",
    "VERIFICATION_PRESENT",
    "VERIFICATION_RANGE_MATCHES_COUNT",
    "JURAT_DATE_CONSISTENT",
    "VERIFICATION_DATE_CONSISTENT",
    "ADVOCATE_DETAILS_CONSISTENT",
    "UNSUPPORTED_NAMES_FLAGGED",
    "UNSUPPORTED_DATES_FLAGGED",
    "MISSING_REQUIRED_INFORMATION_FLAGGED",
]


class ValidationCheck(BaseModel):
    """Single deterministic validation check result."""
    check_id: str = Field(description="One of REQUIRED_CHECK_IDS")
    category: CheckCategory
    status: CheckStatus
    severity: CheckSeverity
    message: str
    expected: Optional[str] = None
    actual: Optional[str] = None
    source_rule: str = Field(description="Template rule or spec section that this check enforces")
    evidence: Optional[str] = Field(default=None, description="Excerpt from generated document")
    suggested_correction: Optional[str] = None


class ValidationRunResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    generation_run_id: str
    checks: list[ValidationCheck]
    total_checks: int
    passed: int
    failed: int
    warnings: int
    not_applicable: int
    critical_failures: list[str] = Field(description="check_ids with ERROR severity that FAILed")
    ai_review_warnings: list[str] = Field(
        default_factory=list,
        description="Semantic issues flagged by AI review (labeled separately from deterministic checks)",
    )


class ValidationRunSummary(BaseModel):
    id: str
    generation_run_id: str
    issue_count: int
    passed: int
    failed: int
    created_at: str
