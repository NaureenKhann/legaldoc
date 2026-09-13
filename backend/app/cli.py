"""
LegalDoc Intelligence Platform — Pipeline CLI Runner.
Executes end-to-end processing on input PDF files and writes deliverables to /outputs/.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
import fitz  # PyMuPDF

from app.ai.provider import get_llm_provider
from app.schemas.case import CaseData
from app.services.content_mapping.mapper import ContentMapper
from app.services.docx_generation.generator import DocxGenerator
from app.services.drafting.engine import DraftingEngine
from app.services.entity_extraction.extractor import EntityExtractor
from app.services.reporting.reporter import EvaluationReporter
from app.services.scoring.engine import ScoringEngine
from app.services.template_analysis.analyzer import TemplateAnalyzer
from app.services.validation.engine import ValidationEngine


def _read_pdf_text(path: Path) -> str:
    if not path.exists():
        return ""
    doc = fitz.open(path)
    return "\n".join(page.get_text() for page in doc)


async def run_pipeline(
    base_dir: Path,
    outputs_dir: Path,
) -> tuple[Path, Path, Path]:
    print("============================================================")
    print(" LegalDoc Intelligence Platform — E2E Pipeline Execution")
    print("============================================================")

    outputs_dir.mkdir(parents=True, exist_ok=True)

    # Search for PDF files in base_dir or base_dir.parent
    def find_file(filename: str) -> Path:
        p1 = base_dir / filename
        if p1.exists():
            return p1
        p2 = base_dir.parent / filename
        if p2.exists():
            return p2
        return p1

    fmt_path = find_file("01 Affidavit Format Explained.pdf")
    ref_path = find_file("02 Affidavit in Reply Sample.docx.pdf")
    case_path = find_file("03_Case_Information.pdf")

    print(f"[1/6] Ingesting source PDFs...")
    fmt_text = _read_pdf_text(fmt_path)
    ref_text = _read_pdf_text(ref_path)
    case_text = _read_pdf_text(case_path)

    print(f"      - Format Explanation text: {len(fmt_text)} chars")
    print(f"      - Reference Affidavit text: {len(ref_text)} chars")
    print(f"      - Case Information text: {len(case_text)} chars")

    llm = get_llm_provider()

    print("[2/6] Extracting structured case data...")
    extractor = EntityExtractor(llm)
    case_data: CaseData = await extractor.extract(case_text)
    print(f"      - Petitioner: {case_data.petitioner.name}")
    print(f"      - Answering Respondent: Respondent No. {case_data.answering_respondent_number}")
    print(f"      - Reply Points: {len(case_data.reply_points)} points")

    print("[3/6] Analyzing template & mapping content...")
    analyzer = TemplateAnalyzer(llm)
    template = await analyzer.analyze(fmt_text, ref_text)

    mapper = ContentMapper()
    mapping = mapper.map(template, case_data)
    mapping.matter_id = "cli-run"

    print("[4/6] Drafting body paragraphs...")
    drafter = DraftingEngine(llm)
    drafted = await drafter.draft(case_data, mapping, ref_text)
    print(f"      - Drafted {len(drafted)} paragraphs")

    print("[5/6] Generating DOCX affidavit output...")
    output_docx = outputs_dir / "Generated_Affidavit_in_Reply.docx"

    generator = DocxGenerator()
    gen_meta = generator.generate(
        case_data=case_data,
        mapping=mapping,
        drafted_paragraphs=drafted,
        matter_id="cli-run",
        run_id="run-001",
        output_path=str(output_docx),
    )
    print(f"      - DOCX saved to: {output_docx.resolve()}")

    print("[6/6] Validating document & generating evaluation report...")
    from docx import Document as DocxDocument
    doc_docx = DocxDocument(output_docx)
    generated_text = "\n".join(p.text for p in doc_docx.paragraphs if p.text.strip())

    from app.schemas.generation import GenerationResult
    gen_result = GenerationResult(
        matter_id="cli-run",
        run_id="run-001",
        file_path=str(output_docx),
        generated_sections=gen_meta.generated_sections,
        body_paragraph_count=gen_meta.body_paragraph_count,
        verification_range=gen_meta.verification_range,
        drafted_paragraphs=drafted,
        model_name="deterministic-engine",
        prompt_version="v1.0",
    )

    validator = ValidationEngine()
    val_result = validator.validate(case_data, gen_result, generated_text)

    scorer = ScoringEngine()
    score = scorer.score(val_result)

    reporter = EvaluationReporter()
    report = reporter.generate_report(
        matter_id="cli-run",
        generation_run_id="run-001",
        validation_run_id="val-001",
        validation_result=val_result,
        score=score,
    )

    output_md = outputs_dir / "Evaluation_Report.md"
    output_json = outputs_dir / "Evaluation_Report.json"

    output_md.write_text(report.report_markdown, encoding="utf-8")
    output_json.write_text(json.dumps(report.model_dump(mode="json"), indent=2), encoding="utf-8")

    print("============================================================")
    print(f" PIPELINE COMPLETE")
    print(f" Overall Score: {score.overall_score:.1f} / {score.max_score:.1f} ({score.percentage:.1f}%)")
    print(f" Checks Passed: {val_result.passed} | Failed: {val_result.failed} | Warnings: {val_result.warnings}")
    print(f" Generated Files:")
    print(f"   1. {output_docx}")
    print(f"   2. {output_md}")
    print(f"   3. {output_json}")
    print("============================================================")

    return output_docx, output_md, output_json


def main() -> None:
    backend_dir = Path(__file__).resolve().parent.parent
    repo_dir = backend_dir.parent
    outputs_dir = repo_dir / "outputs"
    asyncio.run(run_pipeline(repo_dir, outputs_dir))


if __name__ == "__main__":
    main()
