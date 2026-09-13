"""Synopsis & List of Dates API routes."""
from __future__ import annotations

import uuid
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CaseData as CaseDataModel, Matter as MatterModel
from app.db.session import get_db
from app.services.synopsis.synopsis_service import SynopsisService

router = APIRouter()


@router.post("/matters/{matter_id}/synopsis/generate")
async def generate_synopsis(
    matter_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    matter = await _get_matter_or_404(matter_id, db)
    case_data = await _get_case_data(matter_id, db)

    service = SynopsisService()
    events = service.extract_chronology(case_data)

    return {
        "matter_id": matter_id,
        "title": matter.title,
        "events_count": len(events),
        "events": events,
    }


@router.get("/matters/{matter_id}/synopsis/download")
async def download_synopsis_docx(
    matter_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    matter = await _get_matter_or_404(matter_id, db)
    case_data = await _get_case_data(matter_id, db)

    service = SynopsisService()
    events = service.extract_chronology(case_data)
    docx_bytes = service.generate_docx(matter.title, case_data, events)

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=Synopsis_List_of_Dates_{matter_id[:8]}.docx"},
    )


async def _get_matter_or_404(matter_id: str, db: AsyncSession) -> MatterModel:
    res = await db.execute(select(MatterModel).where(MatterModel.id == uuid.UUID(matter_id)))
    m = res.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Matter not found")
    return m


async def _get_case_data(matter_id: str, db: AsyncSession) -> Dict[str, Any]:
    res = await db.execute(select(CaseDataModel).where(CaseDataModel.matter_id == uuid.UUID(matter_id)))
    record = res.scalar_one_or_none()
    if not record:
        return {
            "petitioner_name": "Standard Petitioner",
            "respondent_name": "State Authorities",
            "court_jurisdiction": "Writ Jurisdiction",
            "impugned_order_date": "15.01.2024",
        }
    return record.structured_json or {}
