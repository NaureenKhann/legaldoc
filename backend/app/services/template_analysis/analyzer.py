"""
Template Analyzer — uses LLM to derive TemplateSchema from
format explanation + reference affidavit. Produces a default
schema if documents are not yet uploaded.
"""
from __future__ import annotations

import structlog

from app.ai.provider import LLMProvider
from app.ai.prompts.all_prompts import TEMPLATE_ANALYSIS_SYSTEM, TEMPLATE_ANALYSIS_USER
from app.core.config import get_settings
from app.schemas.template import SectionRule, TemplateSchema

logger = structlog.get_logger(__name__)
settings = get_settings()


DEFAULT_SECTIONS: list[dict] = [
    {"section_id": "forum_heading", "label": "Forum / Court Heading", "order": 1, "required": True,
     "rules": ["Must be in uppercase", "Centre aligned", "Bold"],
     "evidence": "Default rule — court heading is first element"},
    {"section_id": "jurisdiction", "label": "Jurisdiction", "order": 2, "required": True,
     "rules": ["Centre aligned", "Uppercase"],
     "evidence": "Default rule"},
    {"section_id": "case_number", "label": "Case Number", "order": 3, "required": True,
     "rules": ["Include proceeding type and year"],
     "evidence": "Default rule"},
    {"section_id": "cause_title", "label": "Cause Title", "order": 4, "required": True,
     "rules": ["Petitioner above, Respondents below", "VERSUS separator"],
     "evidence": "Default rule"},
    {"section_id": "affidavit_title", "label": "Affidavit Title", "order": 5, "required": True,
     "rules": ["Must include 'AFFIDAVIT IN REPLY ON BEHALF OF RESPONDENT NO. X'"],
     "fixed_phrases": ["AFFIDAVIT IN REPLY ON BEHALF OF RESPONDENT NO."],
     "evidence": "Default rule"},
    {"section_id": "deponent_clause", "label": "Deponent Clause", "order": 6, "required": True,
     "rules": ["Include name, designation, organisation, address", "State acting on behalf of party"],
     "evidence": "Default rule"},
    {"section_id": "body_paragraphs", "label": "Body Paragraphs", "order": 7, "required": True,
     "rules": ["Numbered sequentially starting at 1", "No paragraph should be unnumbered"],
     "evidence": "Default rule"},
    {"section_id": "prayer", "label": "Prayer", "order": 8, "required": True,
     "rules": ["Labelled with PRAYER heading", "Items use letter notation (a), (b), not numbers"],
     "evidence": "Default rule"},
    {"section_id": "jurat", "label": "Jurat / Attestation", "order": 9, "required": True,
     "rules": ["Contains 'solemnly affirmed' or 'sworn'", "Use supplied place and date"],
     "evidence": "Default rule"},
    {"section_id": "verification", "label": "Verification", "order": 10, "required": True,
     "rules": ["Must reference exact paragraph range", "Use supplied place and date"],
     "evidence": "Default rule"},
    {"section_id": "advocate_block", "label": "Advocate / Drafting Block", "order": 11, "required": False,
     "rules": ["Include firm name", "Include party acted for"],
     "evidence": "Default rule"},
]


class TemplateAnalyzer:
    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def analyze(
        self,
        format_explanation_text: str,
        reference_affidavit_text: str,
    ) -> TemplateSchema:
        log = logger.bind(service="template_analyzer")

        if not format_explanation_text and not reference_affidavit_text:
            log.warning("no_documents_using_default_template")
            return self._default_schema()

        if settings.DEMO_MODE:
            log.info("demo_mode_template")
            return self._default_schema()

        try:
            user_prompt = TEMPLATE_ANALYSIS_USER.format(
                format_explanation_text=format_explanation_text[:6000],
                reference_affidavit_text=reference_affidavit_text[:6000],
            )
            schema = await self.llm.complete_structured(
                system_prompt=TEMPLATE_ANALYSIS_SYSTEM,
                user_prompt=user_prompt,
                response_schema=TemplateSchema,
            )
            log.info("template_analysis_complete", sections=len(schema.sections))
            return schema

        except Exception as e:
            log.error("template_analysis_failed_using_default", error=str(e))
            return self._default_schema()

    @staticmethod
    def _default_schema() -> TemplateSchema:
        sections = [
            SectionRule(
                section_id=s["section_id"],
                label=s["label"],
                order=s["order"],
                required=s["required"],
                rules=s["rules"],
                fixed_phrases=s.get("fixed_phrases", []),
                formatting={},
                evidence=s["evidence"],
            )
            for s in DEFAULT_SECTIONS
        ]
        return TemplateSchema(
            document_type="AFFIDAVIT_IN_REPLY",
            sections=sections,
            paragraph_rules=["Sequential numbering from 1", "No gaps in numbering"],
            prayer_rules=["Use letter notation (a), (b)", "Not body paragraph numbers"],
            verification_rules=[
                "Range must match actual body paragraph count",
                "Use supplied place and date",
            ],
            deponent_rules=[
                "If organisation is answering, deponent acts on behalf of organisation",
                "Deponent is NOT the organisation itself",
            ],
            formatting_rules=["Times New Roman 12pt", "1.25 inch left margin", "Bold headings"],
            fixed_phrases={
                "affidavit_title": "AFFIDAVIT IN REPLY ON BEHALF OF RESPONDENT NO.",
                "verification": "do hereby verify",
            },
            entity_requirements=["court_name", "case_number", "petitioner", "respondents", "deponent", "advocate"],
            unsupported_features=[],
            source_documents=["default"],
        )
