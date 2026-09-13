"""
E2E test verifying full pipeline execution on input PDFs.
"""
from __future__ import annotations

from pathlib import Path
import pytest

from app.cli import run_pipeline


@pytest.mark.asyncio
async def test_full_pipeline_e2e(tmp_path: Path) -> None:
    repo_dir = Path(__file__).resolve().parent.parent.parent.parent
    outputs_dir = tmp_path / "outputs"

    docx_path, md_path, json_path = await run_pipeline(repo_dir, outputs_dir)

    assert docx_path.exists()
    assert md_path.exists()
    assert json_path.exists()

    assert docx_path.stat().st_size > 1000
    assert "LegalDoc Intelligence Platform" in md_path.read_text(encoding="utf-8")
