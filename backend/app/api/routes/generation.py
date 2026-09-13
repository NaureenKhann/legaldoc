"""Generation routes — full pipeline: map → draft → generate DOCX."""
from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.provider import get_llm_provider
from app.db.models import (
    CaseData as CaseDataModel,
    ContentMapping as ContentMappingModel,
    GenerationRun,
    GenerationStatus,
    SourceDocument,
    TemplateAnalysis,
)
from app.db.session import get_db
from app.schemas.case import CaseData
from app.schemas.generation import GenerateRequest, GenerationRunDetail, GenerationResult
from app.schemas.mapping import MappingPlan
from app.schemas.template import TemplateSchema
from app.services.content_mapping.mapper import ContentMapper
from app.services.docx_generation.generator import DocxGenerator
from app.services.drafting.engine import DraftingEngine
from app.services.template_analysis.analyzer import TemplateAnalyzer

router = APIRouter()


@router.post("/matters/{matter_id}/generate", response_model=GenerationRunDetail)
async def generate_document(
    matter_id: str,
    request: GenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> GenerationRunDetail:
    # Load case data
    cd_result = await db.execute(
        select(CaseDataModel).where(CaseDataModel.matter_id == uuid.UUID(matter_id))
    )
    cd_record = cd_result.scalar_one_or_none()
    if not cd_record:
        raise HTTPException(status_code=404, detail="Case data not found. Run extraction first.")

    case_data = CaseData.model_validate(cd_record.structured_json)

    # Load template (or create default)
    template = await _get_or_create_template(matter_id, db)

    # Map content
    mapper = ContentMapper()
    mapping = mapper.map(template, case_data)
    mapping.matter_id = matter_id

    # Persist mapping
    await _save_mapping(matter_id, mapping, db)

    # Load reference text for drafting style
    reference_text = await _get_reference_text(matter_id, db)

    # Create generation run record
    run_id = str(uuid.uuid4())
    run = GenerationRun(
        id=uuid.UUID(run_id),
        matter_id=uuid.UUID(matter_id),
        status=GenerationStatus.RUNNING,
        model_name=request.model_name or "demo" if request.demo_mode else "gpt-4o",
        prompt_version="v1.0",
    )
    db.add(run)
    await db.commit()

    try:
        # Draft paragraphs
        llm = get_llm_provider()
        drafter = DraftingEngine(llm)
        drafted = await drafter.draft(case_data, mapping, reference_text)

        # Generate DOCX
        generator = DocxGenerator()
        meta = generator.generate(case_data, mapping, drafted, matter_id, run_id)

        # Build result
        result = GenerationResult(
            matter_id=matter_id,
            run_id=run_id,
            file_path=meta.file_path,
            document_metadata={
                "filename": meta.filename,
                "warnings": meta.warnings,
            },
            generated_sections=meta.generated_sections,
            body_paragraph_count=meta.body_paragraph_count,
            verification_range=meta.verification_range,
            drafted_paragraphs=drafted,
            generation_warnings=meta.warnings,
            model_name=run.model_name or "unknown",
            prompt_version="v1.0",
        )

        # Update run
        run.status = GenerationStatus.COMPLETED
        run.output_document_path = meta.file_path
        run.generation_metadata = result.model_dump(mode="json", exclude={"drafted_paragraphs"})
        run.completed_at = datetime.utcnow()
        await db.commit()

        return GenerationRunDetail(
            id=run_id,
            matter_id=matter_id,
            status=GenerationStatus.COMPLETED,
            model_name=run.model_name,
            prompt_version="v1.0",
            body_paragraph_count=meta.body_paragraph_count,
            created_at=run.created_at,
            completed_at=run.completed_at,
            result=result,
        )

    except Exception as e:
        run.status = GenerationStatus.FAILED
        run.error_message = str(e)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")


@router.get("/matters/{matter_id}/generation-runs", response_model=list[GenerationRunDetail])
async def list_generation_runs(
    matter_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[GenerationRunDetail]:
    result = await db.execute(
        select(GenerationRun)
        .where(GenerationRun.matter_id == uuid.UUID(matter_id))
        .order_by(GenerationRun.created_at.desc())
    )
    runs = result.scalars().all()
    return [
        GenerationRunDetail(
            id=str(r.id),
            matter_id=str(r.matter_id),
            status=r.status,
            model_name=r.model_name,
            prompt_version=r.prompt_version,
            created_at=r.created_at,
            completed_at=r.completed_at,
        )
        for r in runs
    ]


@router.get("/generation-runs/{run_id}/download")
async def download_document(
    run_id: str,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    result = await db.execute(
        select(GenerationRun).where(GenerationRun.id == uuid.UUID(run_id))
    )
    run = result.scalar_one_or_none()
    if not run or not run.output_document_path:
        raise HTTPException(status_code=404, detail="Generated document not found")

    from app.core.config import get_settings
    settings = get_settings()

    path = Path(run.output_document_path) if run.output_document_path and run.output_document_path != "None" else settings.STORAGE_PATH / "generated" / str(run.matter_id) / f"affidavit_in_reply_{run_id}.docx"
    
    if not path.exists():
        fallback_path = settings.STORAGE_PATH / "generated" / str(run.matter_id) / f"affidavit_in_reply_{run_id}.docx"
        if fallback_path.exists():
            path = fallback_path
        else:
            raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=str(path),
        filename=path.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _get_or_create_template(matter_id: str, db: AsyncSession) -> TemplateSchema:
    result = await db.execute(
        select(TemplateAnalysis).where(TemplateAnalysis.matter_id == uuid.UUID(matter_id))
    )
    record = result.scalar_one_or_none()
    if record:
        return TemplateSchema.model_validate(record.schema_json)

    # Try to analyze from uploaded documents
    docs_result = await db.execute(
        select(SourceDocument).where(SourceDocument.matter_id == uuid.UUID(matter_id))
    )
    docs = {d.document_type: d for d in docs_result.scalars().all()}

    llm = get_llm_provider()
    analyzer = TemplateAnalyzer(llm)
    schema = await analyzer.analyze(
        format_explanation_text=docs.get("FORMAT_EXPLANATION", None) and docs["FORMAT_EXPLANATION"].extracted_text or "",
        reference_affidavit_text=docs.get("REFERENCE_AFFIDAVIT", None) and docs["REFERENCE_AFFIDAVIT"].extracted_text or "",
    )

    ta = TemplateAnalysis(
        id=uuid.uuid4(),
        matter_id=uuid.UUID(matter_id),
        schema_json=schema.model_dump(mode="json"),
        source_document_ids=list(str(d.id) for d in docs.values()),
    )
    db.add(ta)
    await db.commit()
    return schema


async def _get_reference_text(matter_id: str, db: AsyncSession) -> str:
    result = await db.execute(
        select(SourceDocument).where(
            SourceDocument.matter_id == uuid.UUID(matter_id),
            SourceDocument.document_type == "REFERENCE_AFFIDAVIT",
        )
    )
    doc = result.scalar_one_or_none()
    return (doc.extracted_text or "")[:3000] if doc else ""


async def _save_mapping(matter_id: str, mapping: MappingPlan, db: AsyncSession) -> None:
    existing = await db.execute(
        select(ContentMappingModel).where(
            ContentMappingModel.matter_id == uuid.UUID(matter_id)
        )
    )
    record = existing.scalar_one_or_none()
    if record:
        record.mapping_json = mapping.model_dump(mode="json")
    else:
        cm = ContentMappingModel(
            id=uuid.uuid4(),
            matter_id=uuid.UUID(matter_id),
            mapping_json=mapping.model_dump(mode="json"),
        )
        db.add(cm)
    await db.commit()
