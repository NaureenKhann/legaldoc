"""
Document Ingestion Service — handles PDF, DOCX, and TXT files.
Validates, extracts text, normalises whitespace, records metadata.
"""
from __future__ import annotations

import mimetypes
import uuid
from pathlib import Path
from typing import Any

import aiofiles
import structlog

from app.core.config import get_settings
from app.core.security import sanitize_filename, verify_storage_path

logger = structlog.get_logger(__name__)
settings = get_settings()


class IngestionError(Exception):
    pass


class UnsupportedFileTypeError(IngestionError):
    pass


class FileTooLargeError(IngestionError):
    pass


class EmptyDocumentError(IngestionError):
    pass


class IngestionResult:
    def __init__(
        self,
        *,
        original_filename: str,
        safe_filename: str,
        storage_path: Path,
        mime_type: str,
        extracted_text: str,
        file_size_bytes: int,
        page_count: int | None,
        metadata: dict[str, Any],
    ) -> None:
        self.original_filename = original_filename
        self.safe_filename = safe_filename
        self.storage_path = storage_path
        self.mime_type = mime_type
        self.extracted_text = extracted_text
        self.file_size_bytes = file_size_bytes
        self.page_count = page_count
        self.metadata = metadata


class DocumentIngestionService:
    """
    Orchestrates file validation, storage, and text extraction.
    Does NOT perform OCR. Isolates format-specific readers.
    """

    ALLOWED_MIME_TYPES: set[str] = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
    }

    def __init__(self, storage_root: Path | None = None) -> None:
        self.storage_root = storage_root or settings.STORAGE_PATH
        self.storage_root.mkdir(parents=True, exist_ok=True)

    async def ingest(
        self,
        file_content: bytes,
        original_filename: str,
        matter_id: str,
        document_type: str,
    ) -> IngestionResult:
        log = logger.bind(
            matter_id=matter_id, filename=original_filename, document_type=document_type
        )

        # 1. Validate extension
        suffix = Path(original_filename).suffix.lstrip(".").lower()
        if suffix not in settings.allowed_extensions_set:
            raise UnsupportedFileTypeError(
                f"File extension '.{suffix}' is not allowed. "
                f"Allowed: {settings.ALLOWED_EXTENSIONS}"
            )

        # 2. Validate size
        if len(file_content) > settings.max_upload_bytes:
            raise FileTooLargeError(
                f"File size {len(file_content)} bytes exceeds "
                f"limit of {settings.max_upload_bytes} bytes"
            )

        # 3. Detect MIME type
        mime_type, _ = mimetypes.guess_type(original_filename)
        mime_type = mime_type or "application/octet-stream"

        if mime_type not in self.ALLOWED_MIME_TYPES:
            raise UnsupportedFileTypeError(f"MIME type '{mime_type}' is not supported")

        # 4. Save with safe filename
        safe_name = sanitize_filename(original_filename)
        dest_dir = self.storage_root / "uploads" / matter_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / safe_name

        verify_storage_path(self.storage_root, dest_path)

        async with aiofiles.open(dest_path, "wb") as f:
            await f.write(file_content)

        log.info("file_saved", path=str(dest_path), size=len(file_content))

        # 5. Extract text
        extracted_text, page_count, metadata = await self._extract_text(
            dest_path, mime_type, file_content
        )

        # 6. Detect empty
        if not extracted_text.strip():
            raise EmptyDocumentError(
                f"Document '{original_filename}' produced no extractable text"
            )

        # 7. Normalise whitespace
        extracted_text = self._normalise_text(extracted_text)

        log.info(
            "ingestion_complete",
            chars=len(extracted_text),
            pages=page_count,
        )

        return IngestionResult(
            original_filename=original_filename,
            safe_filename=safe_name,
            storage_path=dest_path,
            mime_type=mime_type,
            extracted_text=extracted_text,
            file_size_bytes=len(file_content),
            page_count=page_count,
            metadata=metadata,
        )

    async def _extract_text(
        self,
        file_path: Path,
        mime_type: str,
        content: bytes,
    ) -> tuple[str, int | None, dict[str, Any]]:
        if mime_type == "application/pdf":
            return self._extract_pdf(content)
        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return self._extract_docx(file_path)
        elif mime_type == "text/plain":
            text = content.decode("utf-8", errors="replace")
            return text, None, {"format": "txt"}
        else:
            raise UnsupportedFileTypeError(f"No extractor for {mime_type}")

    def _extract_pdf(self, content: bytes) -> tuple[str, int, dict[str, Any]]:
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(stream=content, filetype="pdf")
            page_count = doc.page_count
            pages: list[str] = []
            for page_num, page in enumerate(doc):
                text = page.get_text("text")
                if text.strip():
                    pages.append(f"=== Page {page_num + 1} ===\n{text}")
            doc.close()

            full_text = "\n\n".join(pages)
            metadata = {"format": "pdf", "page_count": page_count}
            return full_text, page_count, metadata

        except Exception as e:
            raise IngestionError(f"PDF extraction failed: {e}") from e

    def _extract_docx(self, file_path: Path) -> tuple[str, None, dict[str, Any]]:
        try:
            from docx import Document

            doc = Document(str(file_path))
            paragraphs: list[str] = []

            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text)

            # Also extract from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            paragraphs.append(cell.text)

            full_text = "\n\n".join(paragraphs)
            metadata = {
                "format": "docx",
                "paragraph_count": len(doc.paragraphs),
                "table_count": len(doc.tables),
            }
            return full_text, None, metadata

        except Exception as e:
            raise IngestionError(f"DOCX extraction failed: {e}") from e

    @staticmethod
    def _normalise_text(text: str) -> str:
        """Normalise whitespace while preserving paragraph structure."""
        import re

        # Collapse multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Strip trailing whitespace per line
        lines = [line.rstrip() for line in text.split("\n")]
        # Collapse runs of spaces (not indents)
        lines = [re.sub(r" {3,}", "  ", line) for line in lines]
        return "\n".join(lines).strip()
