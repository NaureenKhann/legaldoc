"""
Drafting Engine — uses LLM to convert reply points into formal affidavit paragraphs.
Python calls the LLM with a controlled prompt; output is validated as DraftedParagraph[].
"""
from __future__ import annotations

import json

import structlog

from app.ai.provider import LLMProvider
from app.ai.prompts.all_prompts import DRAFTING_SYSTEM, DRAFTING_USER, PROMPT_VERSION
from app.core.config import get_settings
from app.schemas.case import CaseData
from app.schemas.generation import DraftedParagraph
from app.schemas.mapping import MappingPlan, ParagraphType

logger = structlog.get_logger(__name__)
settings = get_settings()


# ─── Demo Drafts ──────────────────────────────────────────────────────────────

def _build_demo_paragraphs(case_data: CaseData, mapping: MappingPlan) -> list[DraftedParagraph]:
    """Deterministic demo paragraphs for use when DEMO_MODE=true."""
    d = case_data.deponent
    court = case_data.court
    resp_no = case_data.answering_respondent_number

    para_texts = {
        ParagraphType.FILING_STATEMENT: (
            f"The Respondent No. {resp_no} hereby files this Affidavit in Reply "
            f"to the Writ Petition No. {court.case_number} of {court.year} filed by the Petitioner."
        ),
        ParagraphType.GENERAL_DENIAL: (
            f"The Respondent No. {resp_no} denies each and every averment, allegation, "
            f"statement and contention made in the Writ Petition except those that are "
            f"specifically admitted herein. The Petitioner is put to strict proof thereof."
        ),
        ParagraphType.PRELIMINARY_POSITION: (
            f"As a preliminary position, the Respondent No. {resp_no} submits that "
            f"the Writ Petition is not maintainable in law and is liable to be dismissed "
            f"on the ground that the Petitioner has no locus standi to file the present petition."
        ),
        ParagraphType.SUBSTANTIVE_ANSWER: (
            f"The Respondent No. {resp_no} denies the allegations made in the Writ Petition "
            f"and states that all actions taken were in accordance with applicable law and regulations."
        ),
        ParagraphType.CLOSING_PARAGRAPH: (
            f"In view of the above, the Respondent No. {resp_no} respectfully submits that "
            f"the Writ Petition deserves to be dismissed with costs."
        ),
    }

    drafted: list[DraftedParagraph] = []

    for pm in sorted(mapping.body_paragraphs, key=lambda p: p.paragraph_number):
        base_text = para_texts.get(pm.paragraph_type, para_texts[ParagraphType.SUBSTANTIVE_ANSWER])

        # Inject exhibit reference if applicable
        if (
            "document" in (pm.reply_point_title or "").lower()
            and case_data.exhibits
        ):
            exhibit = case_data.exhibits[0]
            base_text += (
                f" The Respondent No. {resp_no} relies upon the communication dated "
                f"15 July 2026, which is marked and exhibited herewith as {exhibit.label}."
            )

        text = base_text

        drafted.append(
            DraftedParagraph(
                paragraph_number=pm.paragraph_number,
                paragraph_type=pm.paragraph_type.value
                if hasattr(pm.paragraph_type, "value") else pm.paragraph_type,
                text=text,
                source_reply_point_id=pm.reply_point_order,
                source_evidence=f"Reply point: {pm.reply_point_title or 'closing'}",
                unsupported_claims=[],
                word_count=len(text.split()),
            )
        )

    return drafted


class DraftingEngine:
    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def draft(
        self,
        case_data: CaseData,
        mapping: MappingPlan,
        reference_text_excerpt: str = "",
    ) -> list[DraftedParagraph]:
        log = logger.bind(service="drafting_engine")

        if settings.DEMO_MODE:
            log.info("demo_mode_drafting")
            return _build_demo_paragraphs(case_data, mapping)

        log.info("llm_drafting_start", paragraphs=len(mapping.body_paragraphs))

        user_prompt = DRAFTING_USER.format(
            case_data_json=case_data.model_dump_json(indent=2),
            reference_text_excerpt=reference_text_excerpt[:2000],
            paragraph_mapping_json=json.dumps(
                [pm.model_dump() for pm in mapping.body_paragraphs], indent=2
            ),
        )

        try:
            raw_text = await self.llm._call_provider(
                f"System: {DRAFTING_SYSTEM}", user_prompt, 0.1
            )

            # Parse array of DraftedParagraph
            raw_json = json.loads(raw_text)
            if not isinstance(raw_json, list):
                raw_json = raw_json.get("paragraphs", [])

            drafted = []
            for item in raw_json:
                try:
                    dp = DraftedParagraph.model_validate(item)
                    dp.word_count = len(dp.text.split())
                    drafted.append(dp)
                except Exception as e:
                    log.warning("paragraph_parse_error", item=item, error=str(e))

            if not drafted:
                log.warning("llm_returned_empty_drafts_using_demo")
                return _build_demo_paragraphs(case_data, mapping)

            log.info("drafting_complete", count=len(drafted))
            return drafted

        except Exception as e:
            log.error("drafting_failed_using_demo", error=str(e))
            return _build_demo_paragraphs(case_data, mapping)
