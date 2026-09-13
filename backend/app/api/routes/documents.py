"""Document upload and management routes."""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SourceDocument, ExtractionStatus
from app.db.session import get_db
from app.services.document_ingestion.ingestion_service import (
    DocumentIngestionService,
    EmptyDocumentError,
    FileTooLargeError,
    IngestionError,
    UnsupportedFileTypeError,
)

router = APIRouter()
_ingestion = DocumentIngestionService()


class DocumentSummary(BaseModel):
    id: str
    matter_id: str
    document_type: str
    original_filename: str
    mime_type: str
    file_size_bytes: int | None
    page_count: int | None
    extraction_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentDetail(DocumentSummary):
    extracted_text_preview: str | None


@router.post(
    "/matters/{matter_id}/documents",
    response_model=DocumentSummary,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    matter_id: str,
    document_type: str = Form(..., description="FORMAT_EXPLANATION | REFERENCE_AFFIDAVIT | CASE_INFORMATION"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> DocumentSummary:
    # Validate document_type
    valid_types = {"FORMAT_EXPLANATION", "REFERENCE_AFFIDAVIT", "CASE_INFORMATION"}
    if document_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"document_type must be one of {valid_types}",
        )

    content = await file.read()

    try:
        result = await _ingestion.ingest(
            file_content=content,
            original_filename=file.filename or "upload",
            matter_id=matter_id,
            document_type=document_type,
        )
    except UnsupportedFileTypeError as e:
        raise HTTPException(status_code=415, detail=str(e))
    except FileTooLargeError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except EmptyDocumentError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except IngestionError as e:
        raise HTTPException(status_code=500, detail=str(e))

    doc = SourceDocument(
        id=uuid.uuid4(),
        matter_id=uuid.UUID(matter_id),
        document_type=document_type,
        filename=result.safe_filename,
        original_filename=result.original_filename,
        mime_type=result.mime_type,
        storage_path=str(result.storage_path),
        extracted_text=result.extracted_text,
        extraction_status=ExtractionStatus.COMPLETED,
        extraction_metadata=result.metadata,
        file_size_bytes=result.file_size_bytes,
        page_count=result.page_count,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    return DocumentSummary(
        id=str(doc.id),
        matter_id=str(doc.matter_id),
        document_type=doc.document_type,
        original_filename=doc.original_filename,
        mime_type=doc.mime_type,
        file_size_bytes=doc.file_size_bytes,
        page_count=doc.page_count,
        extraction_status=doc.extraction_status,
        created_at=doc.created_at,
    )


@router.get("/matters/{matter_id}/documents", response_model=list[DocumentSummary])
async def list_documents(
    matter_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[DocumentSummary]:
    result = await db.execute(
        select(SourceDocument)
        .where(SourceDocument.matter_id == uuid.UUID(matter_id))
        .order_by(SourceDocument.created_at)
    )
    docs = result.scalars().all()
    return [
        DocumentSummary(
            id=str(d.id),
            matter_id=str(d.matter_id),
            document_type=d.document_type,
            original_filename=d.original_filename,
            mime_type=d.mime_type,
            file_size_bytes=d.file_size_bytes,
            page_count=d.page_count,
            extraction_status=d.extraction_status,
            created_at=d.created_at,
        )
        for d in docs
    ]


@router.get("/documents/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> DocumentDetail:
    result = await db.execute(
        select(SourceDocument).where(SourceDocument.id == uuid.UUID(document_id))
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    preview = (doc.extracted_text or "")[:500] + "..." if doc.extracted_text else None

    return DocumentDetail(
        id=str(doc.id),
        matter_id=str(doc.matter_id),
        document_type=doc.document_type,
        original_filename=doc.original_filename,
        mime_type=doc.mime_type,
        file_size_bytes=doc.file_size_bytes,
        page_count=doc.page_count,
        extraction_status=doc.extraction_status,
        created_at=doc.created_at,
        extracted_text_preview=preview,
    )
