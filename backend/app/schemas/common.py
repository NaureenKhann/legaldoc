"""
Common/shared Pydantic schemas used across the platform.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


# ─── Provenance ────────────────────────────────────────────────────────────────

class SourceDocumentType(str, Enum):
    FORMAT_EXPLANATION = "format_explanation"
    REFERENCE_AFFIDAVIT = "reference_affidavit"
    CASE_INFORMATION = "case_information"
    GENERATED = "generated"


class ProvenanceField(BaseSchema):
    """Every important extracted field carries this provenance record."""
    field: str
    value: Any
    source_document: SourceDocumentType
    evidence: str = Field(description="Verbatim excerpt from the source document")
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence 0-1")


# ─── Job / Status ──────────────────────────────────────────────────────────────

class MatterStatus(str, Enum):
    CREATED = "CREATED"
    UPLOADING = "UPLOADING"
    EXTRACTING = "EXTRACTING"
    ANALYZING_TEMPLATE = "ANALYZING_TEMPLATE"
    EXTRACTING_ENTITIES = "EXTRACTING_ENTITIES"
    MAPPING = "MAPPING"
    GENERATING = "GENERATING"
    VALIDATING = "VALIDATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class DocumentType(str, Enum):
    FORMAT_EXPLANATION = "FORMAT_EXPLANATION"
    REFERENCE_AFFIDAVIT = "REFERENCE_AFFIDAVIT"
    CASE_INFORMATION = "CASE_INFORMATION"
    GENERATED_OUTPUT = "GENERATED_OUTPUT"


class ExtractionStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EMPTY = "EMPTY"


# ─── Standard API Responses ────────────────────────────────────────────────────

class ErrorDetail(BaseSchema):
    error_code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseSchema):
    status: Literal["ok", "degraded", "error"]
    version: str
    database: bool
    storage: bool
    demo_mode: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)
