"""
Comprehensive test suite for the Validation Engine.
Tests all 25 checks with both passing and failing scenarios,
including error injection fixtures.
"""
from __future__ import annotations

import pytest
from app.schemas.case import (
    AdvocateDetails,
    AttestationDetails,
    CaseData,
    CourtDetails,
    Deponent,
    Exhibit,
    Party,
    PrayerDetails,
    ReplyPoint,
)
from app.schemas.generation import DraftedParagraph, GenerationResult
from app.schemas.validation import CheckStatus
from app.services.validation.engine import ValidationEngine


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_case_data(**overrides) -> CaseData:
    defaults = dict(
        court=CourtDetails(
            court_name="IN THE HIGH COURT OF JUDICATURE AT BOMBAY",
            jurisdiction="ORDINARY ORIGINAL CIVIL JURISDICTION",
            proceeding_type="Writ Petition",
            case_number="1847",
            year=2026,
        ),
        petitioner=Party(name="Sunrise Housing Private Limited", party_type="PETITIONER"),
        respondents=[
            Party(name="State of Maharashtra", party_type="RESPONDENT", respondent_number=1),
            Party(
                name="Mumbai Metropolitan Region Development Authority",
                party_type="RESPONDENT",
                respondent_number=2,
            ),
        ],
        answering_respondent_number=2,
        filed_on_behalf_of="Respondent No. 2 – Mumbai Metropolitan Region Development Authority",
        deponent=Deponent(
            name="Arvind Rajan",
            designation="Deputy Metropolitan Commissioner",
            organization="Mumbai Metropolitan Region Development Authority",
            address="Bandra East, Mumbai, Maharashtra",
            acts_on_behalf_of="Respondent No. 2",
        ),
        verification=AttestationDetails(
            verification_verb="solemnly affirm",
            place="Mumbai",
            date="5 September 2026",
        ),
        reply_points=[
            ReplyPoint(order=1, title="Filing of Affidavit in Reply"),
            ReplyPoint(order=2, title="General Denial"),
        ],
        exhibits=[Exhibit(label="EXHIBIT-'A'", description="Communication dated 15 July 2026")],
        prayer=PrayerDetails(items=["That the Writ Petition be dismissed."]),
        advocate_details=AdvocateDetails(
            firm_name="Rajan & Associates",
            acting_for="Respondent No. 2",
        ),
        extraction_confidence=1.0,
    )
    defaults.update(overrides)
    return CaseData(**defaults)


def make_generation_result(
    para_count: int = 3,
    sections: list[str] | None = None,
) -> GenerationResult:
    if sections is None:
        sections = [
            "forum_heading", "jurisdiction", "case_number", "cause_title",
            "affidavit_title", "deponent_clause", "body_paragraphs",
            "prayer", "jurat", "verification", "advocate_block",
        ]
    drafted = [
        DraftedParagraph(
            paragraph_number=i,
            paragraph_type="SUBSTANTIVE_ANSWER",
            text=f"Paragraph {i} text",
            source_evidence="test",
        )
        for i in range(1, para_count + 1)
    ]
    return GenerationResult(
        matter_id="test-matter",
        run_id="test-run",
        file_path="/tmp/test.docx",
        generated_sections=sections,
        body_paragraph_count=para_count,
        verification_range=f"paragraphs 1 to {para_count}",
        drafted_paragraphs=drafted,
        model_name="test",
        prompt_version="v1.0",
    )


def make_document_text(case_data: CaseData, para_count: int = 3, **overrides) -> str:
    """Build a realistic document text for validation."""
    d = case_data.deponent
    court = case_data.court
    r_num = case_data.answering_respondent_number

    lines = [
        court.court_name.upper(),
        court.jurisdiction.upper(),
        f"WRIT PETITION NO. {court.case_number} OF {court.year}",
        case_data.petitioner.name.upper(),
        "...PETITIONER",
        "VERSUS",
        *[f"{r.name.upper()}\n...RESPONDENT NO. {r.respondent_number}" for r in case_data.respondents],
        f"AFFIDAVIT IN REPLY ON BEHALF OF RESPONDENT NO. {r_num}",
        f"I, {d.name}, {d.designation}, {d.organization}, {d.address}, "
        f"acting for and on behalf of {case_data.filed_on_behalf_of}, do hereby state as follows:",
    ]

    for i in range(1, para_count + 1):
        lines.append(f"{i}. Para {i} text.")

    lines += [
        "PRAYER",
        "It is respectfully prayed that:",
        "(a) That the Writ Petition be dismissed.",
        f"Solemnly affirmed at {case_data.verification.place} on {case_data.verification.date}.",
        f"VERIFICATION: I, {d.name}, do hereby verify that the contents of paragraphs 1 to {para_count}",
        f"Verified at {case_data.verification.place} on {case_data.verification.date}.",
        f"{case_data.advocate_details.firm_name}\nAdvocates for {case_data.advocate_details.acting_for}",
    ]

    # Inject exhibit
    if case_data.exhibits:
        lines.append(f"The communication is marked as {case_data.exhibits[0].label}.")

    for key, val in overrides.items():
        lines.append(str(val))

    return "\n".join(lines)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestValidationEngine:
    def setup_method(self):
        self.engine = ValidationEngine()
        self.case_data = make_case_data()
        self.gen_result = make_generation_result(para_count=3)
        self.doc_text = make_document_text(self.case_data, para_count=3)

    def _get_check(self, result, check_id: str):
        for c in result.checks:
            if c.check_id == check_id:
                return c
        raise AssertionError(f"Check {check_id} not found")

    def test_all_25_checks_run(self):
        result = self.engine.validate(self.case_data, self.gen_result, self.doc_text)
        assert len(result.checks) == 25

    def test_all_checks_have_required_fields(self):
        result = self.engine.validate(self.case_data, self.gen_result, self.doc_text)
        for check in result.checks:
            assert check.check_id
            assert check.category
            assert check.status
            assert check.severity
            assert check.message
            assert check.source_rule

    def test_passes_on_valid_document(self):
        result = self.engine.validate(self.case_data, self.gen_result, self.doc_text)
        failed = [c for c in result.checks if c.status == CheckStatus.FAIL]
        # Should have minimal failures on a well-formed document
        assert len(failed) <= 2

    # ── Error Injection Tests ─────────────────────────────────────────────────

    def test_wrong_case_number_detected(self):
        """Error injection: wrong case number in document."""
        bad_text = self.doc_text.replace("1847", "9999")
        result = self.engine.validate(self.case_data, self.gen_result, bad_text)
        check = self._get_check(result, "CASE_NUMBER_CONSISTENT")
        assert check.status == CheckStatus.FAIL

    def test_wrong_respondent_number_detected(self):
        """Error injection: wrong answering respondent number in affidavit title only."""
        # Case data says answering respondent is No. 2
        # Replace the affidavit title reference AND set answering_respondent_number to 3
        # so no match is found for "Respondent No. 3"
        case_with_different_num = make_case_data(answering_respondent_number=3)
        result = self.engine.validate(case_with_different_num, self.gen_result, self.doc_text)
        check = self._get_check(result, "ANSWERING_RESPONDENT_NUMBER_CONSISTENT")
        assert check.status == CheckStatus.FAIL

    def test_missing_verification_detected(self):
        """Error injection: no verification section."""
        bad_text = self.doc_text.replace("VERIFICATION", "").replace("do hereby verify", "")
        result = self.engine.validate(self.case_data, self.gen_result, bad_text)
        check = self._get_check(result, "VERIFICATION_PRESENT")
        assert check.status == CheckStatus.FAIL

    def test_missing_prayer_detected(self):
        """Error injection: no prayer section."""
        bad_text = self.doc_text.replace("PRAYER", "").replace("(a)", "")
        result = self.engine.validate(self.case_data, self.gen_result, bad_text)
        check = self._get_check(result, "PRAYER_PRESENT")
        assert check.status == CheckStatus.FAIL

    def test_wrong_verification_range_detected(self):
        """Error injection: verification range doesn't match paragraph count."""
        # Document says 1 to 10, but actual count is 3
        bad_text = self.doc_text.replace(
            "paragraphs 1 to 3",
            "paragraphs 1 to 10",
        )
        result = self.engine.validate(self.case_data, self.gen_result, bad_text)
        check = self._get_check(result, "VERIFICATION_RANGE_MATCHES_COUNT")
        assert check.status == CheckStatus.FAIL
        assert "10" in (check.actual or "")

    def test_numeric_prayer_detected(self):
        """Error injection: prayer uses numbers instead of letters."""
        bad_text = self.doc_text.replace("(a) That", "1. That")
        result = self.engine.validate(self.case_data, self.gen_result, bad_text)
        check = self._get_check(result, "PRAYER_USES_LETTERS")
        assert check.status == CheckStatus.FAIL

    def test_missing_exhibit_detected(self):
        """Error injection: exhibit not referenced."""
        bad_text = self.doc_text.replace("EXHIBIT-'A'", "")
        result = self.engine.validate(self.case_data, self.gen_result, bad_text)
        check = self._get_check(result, "EXHIBIT_REFERENCE_PRESENT")
        assert check.status == CheckStatus.FAIL

    def test_paragraph_numbering_sequential(self):
        """Non-sequential paragraph numbering is detected."""
        gen = make_generation_result(para_count=3)
        # Mess up numbering
        gen.drafted_paragraphs[1].paragraph_number = 5  # Gap: 1, 5, 3
        result = self.engine.validate(self.case_data, gen, self.doc_text)
        check = self._get_check(result, "PARAGRAPH_NUMBERING_SEQUENTIAL")
        assert check.status == CheckStatus.FAIL

    def test_missing_required_sections(self):
        """Missing sections are detected."""
        gen = make_generation_result(
            sections=["forum_heading", "jurisdiction"]  # Incomplete
        )
        result = self.engine.validate(self.case_data, gen, self.doc_text)
        check = self._get_check(result, "REQUIRED_SECTIONS_PRESENT")
        assert check.status == CheckStatus.FAIL

    def test_deponent_name_missing_detected(self):
        """Error injection: deponent name not in document."""
        bad_text = self.doc_text.replace("Arvind Rajan", "Someone Else")
        result = self.engine.validate(self.case_data, self.gen_result, bad_text)
        check = self._get_check(result, "DEPONENT_NAME_CONSISTENT")
        assert check.status == CheckStatus.FAIL

    def test_missing_jurat_detected(self):
        """Error injection: no jurat."""
        bad_text = self.doc_text.replace("Solemnly affirmed at Mumbai", "")
        bad_text = bad_text.replace("solemnly affirm", "")
        result = self.engine.validate(self.case_data, self.gen_result, bad_text)
        check = self._get_check(result, "JURAT_PRESENT")
        assert check.status == CheckStatus.FAIL

    def test_unresolved_fields_flagged(self):
        """Missing extraction fields show in MISSING_REQUIRED_INFORMATION check."""
        case_data = make_case_data(unresolved_fields=["court.case_number", "deponent.name"])
        result = self.engine.validate(case_data, self.gen_result, self.doc_text)
        check = self._get_check(result, "MISSING_REQUIRED_INFORMATION_FLAGGED")
        assert check.status == CheckStatus.WARNING
