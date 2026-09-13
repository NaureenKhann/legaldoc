"""Limitation & Condonation of Delay API routes."""
from __future__ import annotations

import uuid
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CaseData as CaseDataModel, Matter as MatterModel
from app.db.session import get_db
from app.services.limitation.limitation_service import LimitationService

router = APIRouter()


@router.post("/matters/{matter_id}/limitation/calculate")
async def calculate_limitation(
    matter_id: str,
    order_date: Optional[str] = Query(None),
    filing_date: Optional[str] = Query(None),
    statutory_days: int = Query(30),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    matter = await _get_matter_or_404(matter_id, db)
    case_data = await _get_case_data(matter_id, db)

    effective_order_date = order_date or case_data.get("impugned_order_date") or "2024-01-15"
    service = LimitationService()
    info = service.calculate_delay(effective_order_date, filing_date, statutory_days)

    return {
        "matter_id": matter_id,
        "title": matter.title,
        "limitation": info,
    }


@router.get("/matters/{matter_id}/limitation/download")
async def download_condonation_docx(
    matter_id: str,
    order_date: Optional[str] = Query(None),
    filing_date: Optional[str] = Query(None),
    statutory_days: int = Query(30),
    db: AsyncSession = Depends(get_db),
) -> Response:
    matter = await _get_matter_or_404(matter_id, db)
    case_data = await _get_case_data(matter_id, db)

    effective_order_date = order_date or case_data.get("impugned_order_date") or "2024-01-15"
    service = LimitationService()
    info = service.calculate_delay(effective_order_date, filing_date, statutory_days)
    docx_bytes = service.generate_condonation_docx(case_data, info)

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=Section_5_Condonation_Petition_{matter_id[:8]}.docx"},
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
            "petitioner_name": "Applicant Petitioner",
            "respondent_name": "State Authorities",
            "court_jurisdiction": "Writ Jurisdiction",
            "impugned_order_date": "2024-01-15",
        }
    return record.structured_json or {}
