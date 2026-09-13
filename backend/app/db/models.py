"""
SQLAlchemy 2 ORM models for LegalDoc Intelligence Platform.
All IDs are UUIDs. All timestamps are timezone-aware.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UUID,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedColumn, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ─── Enums ────────────────────────────────────────────────────────────────────

class MatterStatus(str, PyEnum):
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


class DocumentType(str, PyEnum):
    FORMAT_EXPLANATION = "FORMAT_EXPLANATION"
    REFERENCE_AFFIDAVIT = "REFERENCE_AFFIDAVIT"
    CASE_INFORMATION = "CASE_INFORMATION"
    GENERATED_OUTPUT = "GENERATED_OUTPUT"


class ExtractionStatus(str, PyEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EMPTY = "EMPTY"


class GenerationStatus(str, PyEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ─── Models ───────────────────────────────────────────────────────────────────

class Matter(Base):
    __tablename__ = "matters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(500))
    document_type: Mapped[str] = mapped_column(String(100), default="AFFIDAVIT_IN_REPLY")
    status: Mapped[str] = mapped_column(String(50), default=MatterStatus.CREATED)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    source_documents: Mapped[list[SourceDocument]] = relationship(
        "SourceDocument", back_populates="matter", cascade="all, delete-orphan"
    )
    template_analysis: Mapped[TemplateAnalysis | None] = relationship(
        "TemplateAnalysis", back_populates="matter", uselist=False, cascade="all, delete-orphan"
    )
    case_data: Mapped[CaseData | None] = relationship(
        "CaseData", back_populates="matter", uselist=False, cascade="all, delete-orphan"
    )
    content_mapping: Mapped[ContentMapping | None] = relationship(
        "ContentMapping", back_populates="matter", uselist=False, cascade="all, delete-orphan"
    )
    generation_runs: Mapped[list[GenerationRun]] = relationship(
        "GenerationRun", back_populates="matter", cascade="all, delete-orphan"
    )


class SourceDocument(Base):
    __tablename__ = "source_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    matter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matters.id", ondelete="CASCADE")
    )
    document_type: Mapped[str] = mapped_column(String(50))
    filename: Mapped[str] = mapped_column(String(500))
    original_filename: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str] = mapped_column(String(100))
    storage_path: Mapped[str] = mapped_column(String(1000))
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_status: Mapped[str] = mapped_column(String(50), default=ExtractionStatus.PENDING)
    extraction_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    matter: Mapped[Matter] = relationship("Matter", back_populates="source_documents")


class TemplateAnalysis(Base):
    __tablename__ = "template_analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    matter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matters.id", ondelete="CASCADE"), unique=True
    )
    schema_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    source_document_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    matter: Mapped[Matter] = relationship("Matter", back_populates="template_analysis")


class CaseData(Base):
    __tablename__ = "case_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    matter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matters.id", ondelete="CASCADE"), unique=True
    )
    structured_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    extraction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    unresolved_fields: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    matter: Mapped[Matter] = relationship("Matter", back_populates="case_data")


class ContentMapping(Base):
    __tablename__ = "content_mappings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    matter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matters.id", ondelete="CASCADE"), unique=True
    )
    mapping_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    matter: Mapped[Matter] = relationship("Matter", back_populates="content_mapping")


class GenerationRun(Base):
    __tablename__ = "generation_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    matter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matters.id", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(String(50), default=GenerationStatus.PENDING)
    model_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    output_document_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    generation_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    matter: Mapped[Matter] = relationship("Matter", back_populates="generation_runs")
    validation_run: Mapped[ValidationRun | None] = relationship(
        "ValidationRun", back_populates="generation_run", uselist=False, cascade="all, delete-orphan"
    )


class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    generation_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generation_runs.id", ondelete="CASCADE"), unique=True
    )
    checks_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    score_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    issue_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    generation_run: Mapped[GenerationRun] = relationship(
        "GenerationRun", back_populates="validation_run"
    )
    evaluation_report: Mapped[EvaluationReport | None] = relationship(
        "EvaluationReport", back_populates="validation_run", uselist=False, cascade="all, delete-orphan"
    )


class EvaluationReport(Base):
    __tablename__ = "evaluation_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    validation_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("validation_runs.id", ondelete="CASCADE"), unique=True
    )
    report_markdown: Mapped[str] = mapped_column(Text)
    report_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    validation_run: Mapped[ValidationRun] = relationship(
        "ValidationRun", back_populates="evaluation_report"
    )
