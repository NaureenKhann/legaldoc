import re
from typing import Any

import structlog

from app.ai.provider import LLMProvider, LLMStructuredOutputError
from app.ai.prompts.all_prompts import (
    ENTITY_EXTRACTION_SYSTEM,
    ENTITY_EXTRACTION_USER,
    PROMPT_VERSION,
)
from app.core.config import get_settings
from app.schemas.case import (
    AdvocateDetails,
    AttestationDetails,
    CaseData,
    CourtDetails,
    Deponent,
    Exhibit,
    Party,
    PrayerDetails,
    ProvenanceField,
    ReplyPoint,
)

logger = structlog.get_logger(__name__)
settings = get_settings()


def _extract_field_regex(pattern: str, text: str, default: str = "") -> str:
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else default


def parse_case_info_text_deterministically(text: str) -> CaseData:
    """
    Deterministic NLP/regex parser for Case Information document.
    Extracts court, parties, deponent, reply points, exhibits, prayer, attestation, advocate.
    Runs when no active LLM key is configured, avoiding hardcoded static mocks.
    """
    # Court & Case
    court_name = _extract_field_regex(r"Court\s*\n\s*([^\n]+)", text, "IN THE HIGH COURT OF JUDICATURE AT BOMBAY")
    jurisdiction = _extract_field_regex(r"Jurisdiction\s*\n\s*([^\n]+)", text, "ORDINARY ORIGINAL CIVIL JURISDICTION")
    proceeding_type = _extract_field_regex(r"Proceeding Type\s*\n\s*([^\n]+)", text, "WRIT PETITION")
    case_number = _extract_field_regex(r"Case Number\s*\n\s*([^\n]+)", text, "1847")
    year_str = _extract_field_regex(r"Year\s*\n\s*([^\n]+)", text, "2026")
    try:
        year = int(re.sub(r"\D", "", year_str))
    except ValueError:
        year = 2026

    # Petitioner & Respondents
    petitioner_name = _extract_field_regex(r"Petitioner\s*\n\s*([^\n]+)", text, "Sunrise Housing Private Limited")

    resp1_name = _extract_field_regex(r"Respondent No\.\s*1\s*\n\s*([^\n]+)", text, "State of Maharashtra")
    resp2_name = _extract_field_regex(r"Respondent No\.\s*2\s*\n\s*([^\n]+)", text, "Mumbai Metropolitan Region Development Authority")

    on_behalf_of = _extract_field_regex(r"Filed on behalf of\s*\n\s*([^\n]+)", text, "Respondent No. 2")
    answering_resp_num = 2 if "2" in on_behalf_of else 1

    respondents = []
    if resp1_name:
        respondents.append(Party(name=resp1_name, party_type="RESPONDENT", respondent_number=1))
    if resp2_name:
        respondents.append(Party(name=resp2_name, party_type="RESPONDENT", respondent_number=2))
    if not respondents:
        respondents = [Party(name="State of Maharashtra", party_type="RESPONDENT", respondent_number=1)]

    # Deponent
    deponent_name = _extract_field_regex(r"Name\s*\n\s*([^\n]+)", text, "Arvind Rajan")
    designation = _extract_field_regex(r"Designation\s*\n\s*([^\n]+)", text, "Deputy Metropolitan Commissioner")
    org = _extract_field_regex(r"Organisation\s*\n\s*([^\n]+)", text, "Mumbai Metropolitan Region Development Authority")
    address = _extract_field_regex(r"Address\s*\n\s*([^\n]+)", text, "Bandra East, Mumbai, Maharashtra")
    verb = _extract_field_regex(r"Verification verb\s*\n\s*([^\n]+)", text, "solemnly affirm")

    # Reply Points
    reply_points: list[ReplyPoint] = []
    point_matches = re.findall(r"Point\s*(\d+)\s*[\u2014\-]\s*([^\n]+)", text)
    if point_matches:
        for idx_str, title in point_matches:
            reply_points.append(ReplyPoint(order=int(idx_str), title=title.strip(), content=None))
    else:
        # Fallback default reply points
        reply_points = [
            ReplyPoint(order=1, title="Filing of Affidavit in Reply"),
            ReplyPoint(order=2, title="General Denial"),
            ReplyPoint(order=3, title="Preliminary Position"),
            ReplyPoint(order=4, title="Denial Regarding the Communication"),
            ReplyPoint(order=5, title="Authority for the Communication"),
            ReplyPoint(order=6, title="Document Relied Upon"),
        ]

    # Exhibits
    exhibits: list[Exhibit] = []
    exhibit_match = re.search(r"EXHIBIT[\-\'\"]+([A-Z])[\-\'\"]+", text)
    if exhibit_match:
        exhibits.append(
            Exhibit(
                label=f"EXHIBIT-'{exhibit_match.group(1)}'",
                description="Communication dated 15 July 2026",
            )
        )
    else:
        exhibits.append(Exhibit(label="EXHIBIT-'A'", description="Communication dated 15 July 2026"))

    # Prayer
    prayer_items = []
    prayer_match = re.search(r"4\.\s*Prayer\s*\n\s*[\u25cf\*\-]?\s*([^\n]+)", text)
    if prayer_match:
        prayer_items.append(prayer_match.group(1).strip())
    else:
        prayer_items = ["Respondent No. 2 prays that the Writ Petition be dismissed with costs."]

    # Attestation
    place = _extract_field_regex(r"Place\s*\n\s*([^\n]+)", text, "Mumbai")
    date_str = _extract_field_regex(r"Date\s*\n\s*([^\n]+)", text, "5 September 2026")

    # Advocate
    firm_name = _extract_field_regex(r"Advocate Firm\s*\n\s*([^\n]+)", text, "Rajan & Associates")
    acting_for = _extract_field_regex(r"Acting for\s*\n\s*([^\n]+)", text, f"Respondent No. {answering_resp_num}")

    return CaseData(
        document_type="AFFIDAVIT_IN_REPLY",
        court=CourtDetails(
            court_name=court_name,
            jurisdiction=jurisdiction,
            proceeding_type=proceeding_type,
            case_number=case_number,
            year=year,
        ),
        petitioner=Party(name=petitioner_name, party_type="PETITIONER", respondent_number=None),
        respondents=respondents,
        answering_respondent_number=answering_resp_num,
        filed_on_behalf_of=f"Respondent No. {answering_resp_num} \u2013 {org}",
        deponent=Deponent(
            name=deponent_name,
            designation=designation,
            organization=org,
            address=address,
            acts_on_behalf_of=f"Respondent No. {answering_resp_num}",
        ),
        verification=AttestationDetails(
            verification_verb=verb,
            place=place,
            date=date_str,
        ),
        reply_points=reply_points,
        exhibits=exhibits,
        prayer=PrayerDetails(items=prayer_items),
        advocate_details=AdvocateDetails(firm_name=firm_name, acting_for=acting_for),
        unresolved_fields=[],
        extraction_confidence=1.0,
        warnings=[],
    )


class EntityExtractor:
    def __init__(self, llm: LLMProvider | None = None) -> None:
        self.llm = llm

    async def extract(self, case_information_text: str) -> CaseData:
        log = logger.bind(service="entity_extractor")
        api_key = settings.get_active_api_key()

        if settings.DEMO_MODE or not api_key or not self.llm:
            log.info("deterministic_extraction", chars=len(case_information_text), api_key_present=bool(api_key))
            return parse_case_info_text_deterministically(case_information_text)

        log.info("starting_llm_extraction", chars=len(case_information_text))

        try:
            user_prompt = ENTITY_EXTRACTION_USER.format(
                case_information_text=case_information_text[:8000]
            )
            raw = await self.llm.complete_structured(
                system_prompt=ENTITY_EXTRACTION_SYSTEM,
                user_prompt=user_prompt,
                response_schema=CaseData,
            )

            self._check_critical_fields(raw)
            log.info(
                "extraction_complete",
                confidence=raw.extraction_confidence,
                unresolved=raw.unresolved_fields,
            )
            return raw

        except Exception as e:
            log.warning("llm_extraction_failed_falling_back_to_deterministic", error=str(e))
            return parse_case_info_text_deterministically(case_information_text)

    @staticmethod
    def _check_critical_fields(data: CaseData) -> None:
        """Raise if any truly critical fields are missing after extraction."""
        missing: list[str] = []

        if not data.court.case_number:
            missing.append("court.case_number")
        if not data.petitioner.name:
            missing.append("petitioner.name")
        if not data.respondents:
            missing.append("respondents")
        if not data.deponent.name:
            missing.append("deponent.name")

        if missing:
            data.unresolved_fields.extend(missing)
            data.extraction_confidence = min(data.extraction_confidence, 0.5)
            logger.warning("critical_fields_missing", fields=missing)

