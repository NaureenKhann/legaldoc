"""Entity extraction routes."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.provider import get_llm_provider
from app.db.models import CaseData as CaseDataModel, SourceDocument
from app.db.session import get_db
from app.schemas.case import CaseData, CaseDataResponse
from app.services.entity_extraction.extractor import EntityExtractor

router = APIRouter()


@router.post("/matters/{matter_id}/extract", response_model=CaseDataResponse)
async def extract_entities(
    matter_id: str,
    db: AsyncSession = Depends(get_db),
) -> CaseDataResponse:
    # Find the case information document
    result = await db.execute(
        select(SourceDocument).where(
            SourceDocument.matter_id == uuid.UUID(matter_id),
            SourceDocument.document_type == "CASE_INFORMATION",
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=404,
            detail="No CASE_INFORMATION document found for this matter. Upload it first.",
        )

    if not doc.extracted_text:
        raise HTTPException(status_code=422, detail="Document has no extracted text")

    # Extract
    extractor = EntityExtractor(llm=get_llm_provider())
    case_data = await extractor.extract(doc.extracted_text)

    # Persist
    existing = await db.execute(
        select(CaseDataModel).where(CaseDataModel.matter_id == uuid.UUID(matter_id))
    )
    existing_record = existing.scalar_one_or_none()

    if existing_record:
        existing_record.structured_json = case_data.model_dump(mode="json")
        existing_record.extraction_confidence = case_data.extraction_confidence
        existing_record.unresolved_fields = case_data.unresolved_fields
    else:
        cd_record = CaseDataModel(
            id=uuid.uuid4(),
            matter_id=uuid.UUID(matter_id),
            structured_json=case_data.model_dump(mode="json"),
            extraction_confidence=case_data.extraction_confidence,
            unresolved_fields=case_data.unresolved_fields,
        )
        db.add(cd_record)

    await db.commit()

    return CaseDataResponse(
        matter_id=matter_id,
        case_data=case_data,
        extraction_confidence=case_data.extraction_confidence,
        unresolved_fields=case_data.unresolved_fields,
        warnings=case_data.warnings,
    )


@router.get("/matters/{matter_id}/case-data", response_model=CaseDataResponse)
async def get_case_data(
    matter_id: str,
    db: AsyncSession = Depends(get_db),
) -> CaseDataResponse:
    result = await db.execute(
        select(CaseDataModel).where(CaseDataModel.matter_id == uuid.UUID(matter_id))
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Case data not yet extracted")

    case_data = CaseData.model_validate(record.structured_json)
    return CaseDataResponse(
        matter_id=matter_id,
        case_data=case_data,
        extraction_confidence=record.extraction_confidence or 0.0,
        unresolved_fields=record.unresolved_fields or [],
        warnings=case_data.warnings,
    )
