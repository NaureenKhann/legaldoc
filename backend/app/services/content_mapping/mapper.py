"""
Content Mapper — maps CaseData fields to document sections defined in TemplateSchema.
Calculates verification range. Detects unresolved fields before generation begins.
"""
from __future__ import annotations

import structlog

from app.schemas.case import CaseData
from app.schemas.mapping import MappingEntry, MappingPlan, ParagraphMapping, ParagraphType
from app.schemas.template import TemplateSchema

logger = structlog.get_logger(__name__)

# Map reply point titles to paragraph types
_PARAGRAPH_TYPE_RULES: dict[str, ParagraphType] = {
    "filing": ParagraphType.FILING_STATEMENT,
    "general denial": ParagraphType.GENERAL_DENIAL,
    "preliminary": ParagraphType.PRELIMINARY_POSITION,
    "denial": ParagraphType.SUBSTANTIVE_ANSWER,
    "authority": ParagraphType.SUBSTANTIVE_ANSWER,
    "document": ParagraphType.SUBSTANTIVE_ANSWER,
    "further": ParagraphType.SUBSTANTIVE_ANSWER,
}


def _infer_paragraph_type(title: str) -> ParagraphType:
    lower = title.lower()
    for keyword, ptype in _PARAGRAPH_TYPE_RULES.items():
        if keyword in lower:
            return ptype
    return ParagraphType.SUBSTANTIVE_ANSWER


class ContentMapper:
    def map(self, template: TemplateSchema, case_data: CaseData) -> MappingPlan:
        log = logger.bind(service="content_mapper")
        log.info("mapping_start", sections=len(template.sections))

        answering_r = case_data.get_answering_respondent()
        answering_r_name = answering_r.name if answering_r else "UNKNOWN"
        answering_r_num = case_data.answering_respondent_number

        sections: list[MappingEntry] = []
        unresolved: list[str] = []

        # Map each template section to CaseData fields
        section_map = {
            "forum_heading": (
                case_data.court.court_name,
                ["court.court_name"],
            ),
            "jurisdiction": (
                case_data.court.jurisdiction,
                ["court.jurisdiction"],
            ),
            "case_number": (
                f"WRIT PETITION NO. {case_data.court.case_number} OF {case_data.court.year}",
                ["court.case_number", "court.year"],
            ),
            "cause_title": (
                f"{case_data.petitioner.name}\n...PETITIONER\n\n"
                + "\n".join(
                    f"{r.name}\n...RESPONDENT NO. {r.respondent_number}"
                    for r in case_data.respondents
                ),
                ["petitioner.name", "respondents"],
            ),
            "affidavit_title": (
                f"AFFIDAVIT IN REPLY ON BEHALF OF RESPONDENT NO. {answering_r_num}",
                ["answering_respondent_number"],
            ),
            "deponent_clause": (
                f"I, {case_data.deponent.name}, {case_data.deponent.designation}, "
                f"{case_data.deponent.organization}, {case_data.deponent.address}, "
                f"the deponent herein, acting for and on behalf of {case_data.filed_on_behalf_of}, "
                f"do hereby state as follows:",
                ["deponent", "filed_on_behalf_of"],
            ),
            "body_paragraphs": (
                f"{len(case_data.reply_points)} paragraphs + 1 closing",
                ["reply_points"],
            ),
            "prayer": (
                "\n".join(
                    f"({chr(96 + i + 1)}) {item}"
                    for i, item in enumerate(case_data.prayer.items)
                ),
                ["prayer.items"],
            ),
            "jurat": (
                f"Solemnly affirmed at {case_data.verification.place} "
                f"on {case_data.verification.date}",
                ["verification"],
            ),
            "verification": (
                f"I, {case_data.deponent.name}, the deponent above-named, do hereby verify "
                f"that the contents of paragraphs 1 to {{PARA_COUNT}} are true and correct "
                f"to the best of my knowledge, information and belief.\n\n"
                f"Verified at {case_data.verification.place} on {case_data.verification.date}.",
                ["deponent.name", "verification"],
            ),
            "advocate_block": (
                f"{case_data.advocate_details.firm_name}\n"
                f"Advocates for {case_data.advocate_details.acting_for}",
                ["advocate_details"],
            ),
        }

        for sec in sorted(template.sections, key=lambda s: s.order):
            sec_id = sec.section_id
            if sec_id in section_map:
                value, source_fields = section_map[sec_id]
                is_resolved = bool(value and "UNKNOWN" not in value)
                entry = MappingEntry(
                    section=sec_id,
                    section_label=sec.label,
                    source_fields=source_fields,
                    value=value,
                    is_resolved=is_resolved,
                    unresolved_reason=None if is_resolved else "Required data is missing",
                )
            else:
                entry = MappingEntry(
                    section=sec_id,
                    section_label=sec.label,
                    source_fields=[],
                    value="",
                    is_resolved=False,
                    unresolved_reason=f"No mapping rule for section '{sec_id}'",
                )

            if not entry.is_resolved:
                unresolved.append(sec_id)
            sections.append(entry)

        # Map body paragraphs
        body_paragraphs: list[ParagraphMapping] = []
        para_num = 1

        for rp in sorted(case_data.reply_points, key=lambda r: r.order):
            ptype = _infer_paragraph_type(rp.title)
            body_paragraphs.append(
                ParagraphMapping(
                    paragraph_number=para_num,
                    paragraph_type=ptype,
                    reply_point_order=rp.order,
                    reply_point_title=rp.title,
                    source_fields=[f"reply_points[{rp.order}]"],
                    draft_instruction=(
                        f"Draft a formal affidavit paragraph addressing reply point: "
                        f"'{rp.title}'. If content is provided: {rp.content or 'not provided'}."
                    ),
                )
            )
            para_num += 1

        # Add closing paragraph
        body_paragraphs.append(
            ParagraphMapping(
                paragraph_number=para_num,
                paragraph_type=ParagraphType.CLOSING_PARAGRAPH,
                reply_point_order=None,
                reply_point_title="Closing / Prayer reference",
                source_fields=["prayer"],
                draft_instruction=(
                    "Draft the standard closing paragraph requesting that the petition be dismissed "
                    "and the relief sought in the affidavit be granted."
                ),
            )
        )

        expected_body_count = para_num
        verification_range = (
            f"paragraphs 1 to {expected_body_count}"
            if expected_body_count > 1
            else "paragraph 1"
        )

        # Update verification section with actual count
        for entry in sections:
            if entry.section == "verification":
                entry.value = entry.value.replace("{PARA_COUNT}", str(expected_body_count))

        exhibits = [e.model_dump() for e in case_data.exhibits]

        log.info(
            "mapping_complete",
            body_paragraphs=expected_body_count,
            unresolved=unresolved,
        )

        return MappingPlan(
            matter_id="",  # Filled in by caller
            sections=sections,
            body_paragraphs=body_paragraphs,
            expected_body_count=expected_body_count,
            verification_range=verification_range,
            unresolved_sections=unresolved,
            exhibits=exhibits,
            warnings=[
                f"Unresolved section: {s}" for s in unresolved
            ],
        )
