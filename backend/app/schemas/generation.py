"""
Generation schemas — describe drafted paragraphs and generation run results.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DraftedParagraph(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    """
    A single drafted body paragraph with full provenance and hallucination checks.
    The drafting engine MUST populate unsupported_claims if detected.
    """
    paragraph_number: int = Field(ge=1)
    paragraph_type: str
    text: str = Field(description="Final drafted paragraph text")
    source_reply_point_id: Optional[int] = Field(
        default=None, description="ReplyPoint.order this paragraph addresses"
    )
    source_evidence: str = Field(description="What case data was used to draft this")
    unsupported_claims: list[str] = Field(
        default_factory=list,
        description="Claims in this paragraph not traceable to CaseData (hallucination flags)",
    )
    word_count: int = Field(default=0)


class GenerationResult(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    matter_id: str
    run_id: str
    file_path: str
    document_metadata: dict[str, object] = Field(default_factory=dict)
    generated_sections: list[str]
    body_paragraph_count: int
    verification_range: str
    drafted_paragraphs: list[DraftedParagraph]
    generation_warnings: list[str] = Field(default_factory=list)
    model_name: str
    prompt_version: str
    duration_seconds: Optional[float] = None


class GenerationRunStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class GenerationRunSummary(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: str
    matter_id: str
    status: GenerationRunStatus
    model_name: Optional[str]
    prompt_version: Optional[str]
    body_paragraph_count: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class GenerationRunDetail(GenerationRunSummary):
    result: Optional[GenerationResult] = None
    error_message: Optional[str] = None


class GenerateRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_name: Optional[str] = Field(
        default=None, description="Override default model for this run"
    )
    demo_mode: bool = Field(
        default=False, description="Use deterministic demo output without LLM"
    )
