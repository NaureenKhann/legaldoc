"""Matters CRUD routes."""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Matter, MatterStatus
from app.db.session import get_db

router = APIRouter()


class CreateMatterRequest(BaseModel):
    title: str
    document_type: str = "AFFIDAVIT_IN_REPLY"
    use_default_templates: bool = True


class MatterSummary(BaseModel):
    id: str
    title: str
    document_type: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("/matters", response_model=MatterSummary, status_code=status.HTTP_201_CREATED)
async def create_matter(
    request: CreateMatterRequest,
    db: AsyncSession = Depends(get_db),
) -> MatterSummary:
    from app.db.models import SourceDocument, ExtractionStatus

    matter = Matter(
        id=uuid.uuid4(),
        title=request.title,
        document_type=request.document_type,
        status=MatterStatus.CREATED,
    )
    db.add(matter)
    await db.commit()

    if request.use_default_templates:
        format_doc = SourceDocument(
            id=uuid.uuid4(),
            matter_id=matter.id,
            document_type="FORMAT_EXPLANATION",
            filename="High_Court_Standard_Format.txt",
            original_filename="01 Affidavit Format Explained.pdf",
            mime_type="text/plain",
            storage_path="system/01_Format_Explanation.txt",
            extracted_text="BOMBAY HIGH COURT WRIT PETITION AFFIDAVIT IN REPLY FORMAT RULES AND MANDATORY 10 SECTIONS",
            extraction_status=ExtractionStatus.COMPLETED,
            file_size_bytes=1024,
            page_count=2,
        )
        ref_doc = SourceDocument(
            id=uuid.uuid4(),
            matter_id=matter.id,
            document_type="REFERENCE_AFFIDAVIT",
            filename="Reference_Affidavit_Sample.txt",
            original_filename="02 Affidavit in Reply Sample.docx.pdf",
            mime_type="text/plain",
            storage_path="system/02_Reference_Affidavit.txt",
            extracted_text="STANDARD HIGH COURT AFFIDAVIT IN REPLY REFERENCE MODEL DRAFT FOR WRIT PETITIONS",
            extraction_status=ExtractionStatus.COMPLETED,
            file_size_bytes=2048,
            page_count=3,
        )
        db.add(format_doc)
        db.add(ref_doc)
        await db.commit()

    await db.refresh(matter)
    return MatterSummary(
        id=str(matter.id),
        title=matter.title,
        document_type=matter.document_type,
        status=matter.status,
        created_at=matter.created_at,
        updated_at=matter.updated_at,
    )


@router.post("/matters/demo", response_model=MatterSummary, status_code=status.HTTP_201_CREATED)
async def create_demo_matter(
    db: AsyncSession = Depends(get_db),
) -> MatterSummary:
    """Instantly creates a fully populated demo matter with high court case documents."""
    import os
    from pathlib import Path
    from app.services.document_ingestion.ingestion_service import DocumentIngestionService
    from app.services.entity_extraction.extractor import EntityExtractor
    from app.db.models import SourceDocument, CaseData

    matter = Matter(
        id=uuid.uuid4(),
        title="Writ Petition No. 1847 of 2026 — Apex Infrastructure vs MMRDA",
        document_type="AFFIDAVIT_IN_REPLY",
        status=MatterStatus.EXTRACTED if hasattr(MatterStatus, "EXTRACTED") else MatterStatus.COMPLETED,
    )
    db.add(matter)
    await db.commit()

    sample_dir = Path(__file__).resolve().parents[3] / "sample_cases"
    sample_file_1 = sample_dir / "Sample_Case_01_Land_Acquisition_Writ_Petition.txt"

    ingestion_service = DocumentIngestionService()
    if sample_file_1.exists():
        content = sample_file_1.read_bytes()
        res = await ingestion_service.ingest(
            file_content=content,
            original_filename="03_Case_Information.txt",
            matter_id=str(matter.id),
            document_type="CASE_INFORMATION",
        )
        doc_record = SourceDocument(
            id=uuid.uuid4(),
            matter_id=matter.id,
            document_type="CASE_INFORMATION",
            filename=res.safe_filename,
            original_filename=res.original_filename,
            mime_type=res.mime_type,
            storage_path=str(res.storage_path),
            extracted_text=res.extracted_text,
            extraction_status="COMPLETED",
            file_size_bytes=res.file_size_bytes,
        )
        db.add(doc_record)

    extractor = EntityExtractor()
    case_facts_text = sample_file_1.read_text(encoding="utf-8") if sample_file_1.exists() else "Sample Case Facts"
    case_facts = await extractor.extract(case_information_text=case_facts_text)

    case_data_record = CaseData(
        id=uuid.uuid4(),
        matter_id=matter.id,
        structured_json=case_facts.model_dump(),
        extraction_confidence=case_facts.extraction_confidence,
        unresolved_fields=case_facts.unresolved_fields,
    )
    db.add(case_data_record)
    matter.status = MatterStatus.COMPLETED
    await db.commit()
    await db.refresh(matter)

    return MatterSummary(
        id=str(matter.id),
        title=matter.title,
        document_type=matter.document_type,
        status=matter.status,
        created_at=matter.created_at,
        updated_at=matter.updated_at,
    )


@router.get("/matters", response_model=list[MatterSummary])
async def list_matters(
    db: AsyncSession = Depends(get_db),
) -> list[MatterSummary]:
    result = await db.execute(select(Matter).order_by(Matter.created_at.desc()))
    matters = result.scalars().all()
    return [
        MatterSummary(
            id=str(m.id),
            title=m.title,
            document_type=m.document_type,
            status=m.status,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
        for m in matters
    ]


@router.get("/matters/{matter_id}", response_model=MatterSummary)
async def get_matter(
    matter_id: str,
    db: AsyncSession = Depends(get_db),
) -> MatterSummary:
    matter = await _get_matter_or_404(matter_id, db)
    return MatterSummary(
        id=str(matter.id),
        title=matter.title,
        document_type=matter.document_type,
        status=matter.status,
        created_at=matter.created_at,
        updated_at=matter.updated_at,
    )


from fastapi import Response


@router.delete("/matters/{matter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_matter(
    matter_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    matter = await _get_matter_or_404(matter_id, db)
    await db.delete(matter)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _get_matter_or_404(matter_id: str, db: AsyncSession) -> Matter:
    try:
        uid = uuid.UUID(matter_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid matter ID format")

    result = await db.execute(select(Matter).where(Matter.id == uid))
    matter = result.scalar_one_or_none()
    if not matter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "MATTER_NOT_FOUND", "message": f"Matter {matter_id} not found"},
        )
    return matter
