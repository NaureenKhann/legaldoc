"""
Validation Engine — 25 deterministic checks for generated affidavits.
These checks are INDEPENDENT of the drafting LLM.
Results feed directly into the scoring engine.
"""
from __future__ import annotations

import re
from typing import Any

import structlog

from app.schemas.case import CaseData
from app.schemas.generation import GenerationResult
from app.schemas.validation import (
    CheckCategory,
    CheckSeverity,
    CheckStatus,
    REQUIRED_CHECK_IDS,
    ValidationCheck,
    ValidationRunResult,
)

logger = structlog.get_logger(__name__)


class ValidationEngine:
    """
    Runs all 25 deterministic validation checks on a generated document.
    Input: case_data (authoritative) + generated document text/metadata.
    """

    def validate(
        self,
        case_data: CaseData,
        generation_result: GenerationResult,
        document_text: str,
        ai_review_warnings: list[str] | None = None,
    ) -> ValidationRunResult:
        log = logger.bind(run_id=generation_result.run_id)
        log.info("validation_start", check_count=25)

        checks: list[ValidationCheck] = []
        text = document_text
        meta = generation_result

        # Run all 25 checks
        checks.append(self._check_required_sections(meta))
        checks.append(self._check_section_order(meta))
        checks.append(self._check_court_heading(case_data, text))
        checks.append(self._check_jurisdiction(case_data, text))
        checks.append(self._check_case_number(case_data, text))
        checks.append(self._check_year(case_data, text))
        checks.append(self._check_petitioner(case_data, text))
        checks.append(self._check_respondent_names(case_data, text))
        checks.append(self._check_answering_respondent_number(case_data, text))
        checks.append(self._check_deponent_name(case_data, text))
        checks.append(self._check_deponent_designation(case_data, text))
        checks.append(self._check_org_deponent_relationship(case_data, text))
        checks.append(self._check_paragraph_numbering(meta))
        checks.append(self._check_prayer_uses_letters(text))
        checks.append(self._check_prayer_present(text))
        checks.append(self._check_exhibit_reference(case_data, text))
        checks.append(self._check_jurat_present(text))
        checks.append(self._check_verification_present(text))
        checks.append(self._check_verification_range(meta, text))
        checks.append(self._check_jurat_date(case_data, text))
        checks.append(self._check_verification_date(case_data, text))
        checks.append(self._check_advocate_details(case_data, text))
        checks.append(self._check_unsupported_names(case_data, text))
        checks.append(self._check_unsupported_dates(case_data, text))
        checks.append(self._check_missing_required_info(case_data))

        passed = sum(1 for c in checks if c.status == CheckStatus.PASS)
        failed = sum(1 for c in checks if c.status == CheckStatus.FAIL)
        warnings = sum(1 for c in checks if c.status == CheckStatus.WARNING)
        na = sum(1 for c in checks if c.status == CheckStatus.NOT_APPLICABLE)
        critical = [c.check_id for c in checks if c.status == CheckStatus.FAIL and c.severity == CheckSeverity.ERROR]

        log.info("validation_complete", passed=passed, failed=failed, critical=critical)

        return ValidationRunResult(
            generation_run_id=meta.run_id,
            checks=checks,
            total_checks=len(checks),
            passed=passed,
            failed=failed,
            warnings=warnings,
            not_applicable=na,
            critical_failures=critical,
            ai_review_warnings=ai_review_warnings or [],
        )

    # ── Individual checks ──────────────────────────────────────────────────────

    def _check_required_sections(self, meta: GenerationResult) -> ValidationCheck:
        expected = {
            "forum_heading", "jurisdiction", "case_number", "cause_title",
            "affidavit_title", "deponent_clause", "body_paragraphs",
            "prayer", "jurat", "verification", "advocate_block",
        }
        actual = set(meta.generated_sections)
        missing = expected - actual

        if missing:
            return ValidationCheck(
                check_id="REQUIRED_SECTIONS_PRESENT",
                category=CheckCategory.COMPLETENESS,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.ERROR,
                message=f"Missing required sections: {', '.join(sorted(missing))}",
                expected=str(sorted(expected)),
                actual=str(sorted(actual)),
                source_rule="Section 4: Ten required parts of affidavit structure",
                suggested_correction="Ensure all required sections are generated",
            )

        return ValidationCheck(
            check_id="REQUIRED_SECTIONS_PRESENT",
            category=CheckCategory.COMPLETENESS,
            status=CheckStatus.PASS,
            severity=CheckSeverity.ERROR,
            message=f"All {len(expected)} required sections are present",
            source_rule="Section 4: Ten required parts of affidavit structure",
        )

    def _check_section_order(self, meta: GenerationResult) -> ValidationCheck:
        expected_order = [
            "forum_heading", "jurisdiction", "case_number", "cause_title",
            "affidavit_title", "deponent_clause", "body_paragraphs",
            "prayer", "jurat", "verification", "advocate_block",
        ]
        actual = [s for s in meta.generated_sections if s in expected_order]
        expected_filtered = [s for s in expected_order if s in actual]

        if actual != expected_filtered:
            return ValidationCheck(
                check_id="SECTION_ORDER_CORRECT",
                category=CheckCategory.STRUCTURE,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.ERROR,
                message="Sections are not in the required order",
                expected=str(expected_filtered),
                actual=str(actual),
                source_rule="Section 4: Heading order must be preserved",
            )

        return ValidationCheck(
            check_id="SECTION_ORDER_CORRECT",
            category=CheckCategory.STRUCTURE,
            status=CheckStatus.PASS,
            severity=CheckSeverity.ERROR,
            message="Sections appear in correct order",
            source_rule="Section 4: Heading order must be preserved",
        )

    def _check_court_heading(self, case_data: CaseData, text: str) -> ValidationCheck:
        expected = case_data.court.court_name.upper()
        found = expected in text.upper()
        return ValidationCheck(
            check_id="COURT_HEADING_CONSISTENT",
            category=CheckCategory.CONSISTENCY,
            status=CheckStatus.PASS if found else CheckStatus.FAIL,
            severity=CheckSeverity.ERROR,
            message="Court heading matches case data" if found
                else f"Court heading not found: '{expected}'",
            expected=expected,
            actual="Present in document" if found else "Not found",
            source_rule="Section 5B: Court heading must be consistent across document",
        )

    def _check_jurisdiction(self, case_data: CaseData, text: str) -> ValidationCheck:
        expected = case_data.court.jurisdiction.upper()
        found = expected in text.upper()
        return ValidationCheck(
            check_id="JURISDICTION_CONSISTENT",
            category=CheckCategory.CONSISTENCY,
            status=CheckStatus.PASS if found else CheckStatus.FAIL,
            severity=CheckSeverity.ERROR,
            message="Jurisdiction is consistent" if found else "Jurisdiction not found",
            expected=expected,
            actual="Present" if found else "Not found",
            source_rule="Section 5: Jurisdiction must be consistent",
        )

    def _check_case_number(self, case_data: CaseData, text: str) -> ValidationCheck:
        expected = str(case_data.court.case_number)
        found = expected in text
        return ValidationCheck(
            check_id="CASE_NUMBER_CONSISTENT",
            category=CheckCategory.CONSISTENCY,
            status=CheckStatus.PASS if found else CheckStatus.FAIL,
            severity=CheckSeverity.ERROR,
            message="Case number is consistent" if found else f"Case number '{expected}' not found",
            expected=expected,
            actual="Present" if found else "Not found",
            source_rule="Section 5B: Case number must be consistent across document",
        )

    def _check_year(self, case_data: CaseData, text: str) -> ValidationCheck:
        expected = str(case_data.court.year)
        found = expected in text
        return ValidationCheck(
            check_id="YEAR_CONSISTENT",
            category=CheckCategory.CONSISTENCY,
            status=CheckStatus.PASS if found else CheckStatus.WARNING,
            severity=CheckSeverity.WARNING,
            message="Year is consistent" if found else f"Year '{expected}' not explicitly found",
            expected=expected,
            actual="Present" if found else "Not found",
            source_rule="Section 5E: Year must be consistent",
        )

    def _check_petitioner(self, case_data: CaseData, text: str) -> ValidationCheck:
        expected = case_data.petitioner.name.upper()
        found = expected in text.upper()
        return ValidationCheck(
            check_id="PETITIONER_CONSISTENT",
            category=CheckCategory.ENTITY_ACCURACY,
            status=CheckStatus.PASS if found else CheckStatus.FAIL,
            severity=CheckSeverity.ERROR,
            message="Petitioner name is consistent" if found else f"Petitioner '{expected}' not found",
            expected=expected,
            source_rule="Section 5B: Petitioner must be consistent",
        )

    def _check_respondent_names(self, case_data: CaseData, text: str) -> ValidationCheck:
        missing = []
        for r in case_data.respondents:
            if r.name.upper() not in text.upper():
                missing.append(r.name)

        if missing:
            return ValidationCheck(
                check_id="RESPONDENT_NAMES_CONSISTENT",
                category=CheckCategory.ENTITY_ACCURACY,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.ERROR,
                message=f"Respondent name(s) not found: {', '.join(missing)}",
                expected=str([r.name for r in case_data.respondents]),
                source_rule="Section 5B: All respondent names must appear",
            )

        return ValidationCheck(
            check_id="RESPONDENT_NAMES_CONSISTENT",
            category=CheckCategory.ENTITY_ACCURACY,
            status=CheckStatus.PASS,
            severity=CheckSeverity.ERROR,
            message="All respondent names are consistent",
            source_rule="Section 5B: All respondent names must appear",
        )

    def _check_answering_respondent_number(self, case_data: CaseData, text: str) -> ValidationCheck:
        num = case_data.answering_respondent_number
        patterns = [
            f"RESPONDENT NO. {num}",
            f"Respondent No. {num}",
            f"RESPONDENT NO {num}",
        ]
        found = any(p in text for p in patterns)
        return ValidationCheck(
            check_id="ANSWERING_RESPONDENT_NUMBER_CONSISTENT",
            category=CheckCategory.CONSISTENCY,
            status=CheckStatus.PASS if found else CheckStatus.FAIL,
            severity=CheckSeverity.ERROR,
            message=f"Answering respondent No. {num} is consistent" if found
                else f"'Respondent No. {num}' not found in document",
            expected=f"Respondent No. {num}",
            source_rule="Section 5B: Answering respondent number must be consistent",
        )

    def _check_deponent_name(self, case_data: CaseData, text: str) -> ValidationCheck:
        name = case_data.deponent.name
        found = name in text
        return ValidationCheck(
            check_id="DEPONENT_NAME_CONSISTENT",
            category=CheckCategory.ENTITY_ACCURACY,
            status=CheckStatus.PASS if found else CheckStatus.FAIL,
            severity=CheckSeverity.ERROR,
            message="Deponent name is consistent" if found else f"Deponent '{name}' not found",
            expected=name,
            source_rule="Section 5A: Deponent must be described correctly",
        )

    def _check_deponent_designation(self, case_data: CaseData, text: str) -> ValidationCheck:
        desig = case_data.deponent.designation
        found = desig in text
        return ValidationCheck(
            check_id="DEPONENT_DESIGNATION_CONSISTENT",
            category=CheckCategory.ENTITY_ACCURACY,
            status=CheckStatus.PASS if found else CheckStatus.FAIL,
            severity=CheckSeverity.ERROR,
            message="Deponent designation is consistent" if found else f"Designation '{desig}' not found",
            expected=desig,
            source_rule="Section 5A: Deponent designation must be present",
        )

    def _check_org_deponent_relationship(self, case_data: CaseData, text: str) -> ValidationCheck:
        org = case_data.deponent.organization
        # Rule: if answering respondent is an org, deponent should say "acting on behalf of"
        acting_phrases = ["acting for and on behalf of", "on behalf of"]
        has_org = org.upper() in text.upper()
        has_acting = any(p in text.lower() for p in acting_phrases)

        if has_org and has_acting:
            return ValidationCheck(
                check_id="ORG_DEPONENT_RELATIONSHIP_VALID",
                category=CheckCategory.TEMPLATE_FIDELITY,
                status=CheckStatus.PASS,
                severity=CheckSeverity.ERROR,
                message="Organisation-deponent relationship correctly stated",
                source_rule="Section 5A: Deponent deposing on behalf of organisation",
            )
        elif not has_org:
            return ValidationCheck(
                check_id="ORG_DEPONENT_RELATIONSHIP_VALID",
                category=CheckCategory.TEMPLATE_FIDELITY,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.ERROR,
                message=f"Organisation '{org}' not mentioned in document",
                expected=org,
                source_rule="Section 5A: Deponent deposing on behalf of organisation",
            )
        else:
            return ValidationCheck(
                check_id="ORG_DEPONENT_RELATIONSHIP_VALID",
                category=CheckCategory.TEMPLATE_FIDELITY,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.WARNING,
                message="Organisation present but 'acting on behalf of' phrase not found",
                source_rule="Section 5A: Deponent deposing on behalf of organisation",
            )

    def _check_paragraph_numbering(self, meta: GenerationResult) -> ValidationCheck:
        paragraphs = meta.drafted_paragraphs
        expected = list(range(1, len(paragraphs) + 1))
        actual = [p.paragraph_number for p in sorted(paragraphs, key=lambda x: x.paragraph_number)]

        if actual == expected:
            return ValidationCheck(
                check_id="PARAGRAPH_NUMBERING_SEQUENTIAL",
                category=CheckCategory.STRUCTURE,
                status=CheckStatus.PASS,
                severity=CheckSeverity.ERROR,
                message=f"Body paragraphs numbered sequentially 1 to {len(paragraphs)}",
                source_rule="Section 5C: Body paragraphs must be numbered sequentially",
            )

        return ValidationCheck(
            check_id="PARAGRAPH_NUMBERING_SEQUENTIAL",
            category=CheckCategory.STRUCTURE,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.ERROR,
            message="Paragraph numbering is not sequential",
            expected=str(expected),
            actual=str(actual),
            source_rule="Section 5C: Body paragraphs must be numbered sequentially",
        )

    def _check_prayer_uses_letters(self, text: str) -> ValidationCheck:
        # Prayer items should use (a), (b), (c) NOT 1., 2., 3.
        prayer_section = ""
        if "PRAYER" in text.upper():
            idx = text.upper().index("PRAYER")
            prayer_section = text[idx:idx + 1000]

        has_letters = bool(re.search(r'\([a-z]\)', prayer_section))
        has_numbers_as_prayer = bool(re.search(r'^\s*\d+\.\s+', prayer_section, re.MULTILINE))

        if has_letters and not has_numbers_as_prayer:
            status = CheckStatus.PASS
            msg = "Prayer items correctly use letter notation (a), (b), ..."
        elif has_numbers_as_prayer:
            status = CheckStatus.FAIL
            msg = "Prayer items incorrectly use numeric notation (1., 2., ...)"
        else:
            status = CheckStatus.WARNING
            msg = "Prayer section format unclear — letter notation not detected"

        return ValidationCheck(
            check_id="PRAYER_USES_LETTERS",
            category=CheckCategory.STRUCTURE,
            status=status,
            severity=CheckSeverity.ERROR,
            message=msg,
            expected="(a) item, (b) item ...",
            source_rule="Section 5C: Prayer items must use letters not body numbering",
        )

    def _check_prayer_present(self, text: str) -> ValidationCheck:
        found = "PRAYER" in text.upper()
        return ValidationCheck(
            check_id="PRAYER_PRESENT",
            category=CheckCategory.COMPLETENESS,
            status=CheckStatus.PASS if found else CheckStatus.FAIL,
            severity=CheckSeverity.ERROR,
            message="Prayer section is present" if found else "Prayer section is MISSING",
            source_rule="Section 4: Prayer is a required section",
        )

    def _check_exhibit_reference(self, case_data: CaseData, text: str) -> ValidationCheck:
        if not case_data.exhibits:
            return ValidationCheck(
                check_id="EXHIBIT_REFERENCE_PRESENT",
                category=CheckCategory.COMPLETENESS,
                status=CheckStatus.NOT_APPLICABLE,
                severity=CheckSeverity.INFO,
                message="No exhibits required for this matter",
                source_rule="Section 4: Exhibit references where applicable",
            )

        missing = []
        for exhibit in case_data.exhibits:
            if exhibit.label not in text:
                missing.append(exhibit.label)

        if missing:
            return ValidationCheck(
                check_id="EXHIBIT_REFERENCE_PRESENT",
                category=CheckCategory.COMPLETENESS,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.ERROR,
                message=f"Exhibit reference(s) not found: {', '.join(missing)}",
                expected=str([e.label for e in case_data.exhibits]),
                source_rule="Section 4: Exhibit references must be present",
            )

        return ValidationCheck(
            check_id="EXHIBIT_REFERENCE_PRESENT",
            category=CheckCategory.COMPLETENESS,
            status=CheckStatus.PASS,
            severity=CheckSeverity.ERROR,
            message="All exhibit references are present",
            source_rule="Section 4: Exhibit references must be present",
        )

    def _check_jurat_present(self, text: str) -> ValidationCheck:
        keywords = ["solemnly affirmed", "sworn", "jurat"]
        found = any(k.lower() in text.lower() for k in keywords)
        return ValidationCheck(
            check_id="JURAT_PRESENT",
            category=CheckCategory.COMPLETENESS,
            status=CheckStatus.PASS if found else CheckStatus.FAIL,
            severity=CheckSeverity.ERROR,
            message="Jurat is present" if found else "Jurat is MISSING",
            source_rule="Section 4: Jurat is a required section",
        )

    def _check_verification_present(self, text: str) -> ValidationCheck:
        found = "VERIFICATION" in text.upper() or "do hereby verify" in text.lower()
        return ValidationCheck(
            check_id="VERIFICATION_PRESENT",
            category=CheckCategory.COMPLETENESS,
            status=CheckStatus.PASS if found else CheckStatus.FAIL,
            severity=CheckSeverity.ERROR,
            message="Verification section is present" if found else "Verification is MISSING",
            source_rule="Section 4: Verification is a required section",
        )

    def _check_verification_range(self, meta: GenerationResult, text: str) -> ValidationCheck:
        expected_count = meta.body_paragraph_count
        expected_range_str = f"1 to {expected_count}" if expected_count > 1 else "1"

        # Look for range patterns in verification section
        pattern = re.compile(r"paragraphs?\s+(\d+)\s+to\s+(\d+)", re.IGNORECASE)
        matches = pattern.findall(text)

        if not matches:
            return ValidationCheck(
                check_id="VERIFICATION_RANGE_MATCHES_COUNT",
                category=CheckCategory.CONSISTENCY,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.WARNING,
                message="Could not detect paragraph range in verification section",
                expected=f"paragraphs {expected_range_str}",
                source_rule="Section 5D: Verification range must match actual body paragraph count",
            )

        found_start, found_end = int(matches[-1][0]), int(matches[-1][1])
        if found_start == 1 and found_end == expected_count:
            return ValidationCheck(
                check_id="VERIFICATION_RANGE_MATCHES_COUNT",
                category=CheckCategory.CONSISTENCY,
                status=CheckStatus.PASS,
                severity=CheckSeverity.ERROR,
                message=f"Verification range (1 to {found_end}) matches body paragraph count ({expected_count})",
                source_rule="Section 5D: Verification range must match actual body paragraph count",
            )

        return ValidationCheck(
            check_id="VERIFICATION_RANGE_MATCHES_COUNT",
            category=CheckCategory.CONSISTENCY,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.ERROR,
            message=(
                f"Verification range ({found_start} to {found_end}) does NOT match "
                f"body paragraph count ({expected_count})"
            ),
            expected=f"paragraphs 1 to {expected_count}",
            actual=f"paragraphs {found_start} to {found_end}",
            source_rule="Section 5D: Verification range must match actual body paragraph count",
            suggested_correction=f"Change verification range to: paragraphs 1 to {expected_count}",
        )

    def _check_jurat_date(self, case_data: CaseData, text: str) -> ValidationCheck:
        date = case_data.verification.date
        place = case_data.verification.place
        found_date = date in text
        found_place = place.lower() in text.lower()

        if found_date and found_place:
            return ValidationCheck(
                check_id="JURAT_DATE_CONSISTENT",
                category=CheckCategory.CONSISTENCY,
                status=CheckStatus.PASS,
                severity=CheckSeverity.ERROR,
                message="Jurat date and place are consistent with case data",
                source_rule="Section 5E: Jurat must use supplied date and place",
            )

        return ValidationCheck(
            check_id="JURAT_DATE_CONSISTENT",
            category=CheckCategory.CONSISTENCY,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.ERROR,
            message=f"Jurat date ('{date}') or place ('{place}') not found",
            expected=f"{date} at {place}",
            source_rule="Section 5E: Jurat must use supplied date and place",
        )

    def _check_verification_date(self, case_data: CaseData, text: str) -> ValidationCheck:
        date = case_data.verification.date
        place = case_data.verification.place

        # Look for date in the verification section specifically
        verif_idx = text.upper().find("VERIFICATION")
        verif_text = text[verif_idx:] if verif_idx >= 0 else text
        found = date in verif_text and place.lower() in verif_text.lower()

        return ValidationCheck(
            check_id="VERIFICATION_DATE_CONSISTENT",
            category=CheckCategory.CONSISTENCY,
            status=CheckStatus.PASS if found else CheckStatus.FAIL,
            severity=CheckSeverity.ERROR,
            message="Verification date is consistent" if found else f"Verification date '{date}' not in verification section",
            expected=f"Verified at {place} on {date}",
            source_rule="Section 5E: Verification must use supplied date and place",
        )

    def _check_advocate_details(self, case_data: CaseData, text: str) -> ValidationCheck:
        firm = case_data.advocate_details.firm_name
        found = firm in text
        return ValidationCheck(
            check_id="ADVOCATE_DETAILS_CONSISTENT",
            category=CheckCategory.ENTITY_ACCURACY,
            status=CheckStatus.PASS if found else CheckStatus.FAIL,
            severity=CheckSeverity.WARNING,
            message="Advocate details are consistent" if found else f"Advocate firm '{firm}' not found",
            expected=firm,
            source_rule="Section 4: Advocate block must reflect supplied details",
        )

    def _check_unsupported_names(self, case_data: CaseData, text: str) -> ValidationCheck:
        # Collect all known party names and deponent
        known_names = {
            case_data.petitioner.name.lower(),
            case_data.deponent.name.lower(),
            case_data.deponent.organization.lower(),
            case_data.advocate_details.firm_name.lower(),
        }
        for r in case_data.respondents:
            known_names.add(r.name.lower())

        # Look for suspicious patterns (e.g., "Private Limited", "Ltd", "Authority" that are unknown)
        # Simple heuristic: flag if we find proper-noun-like strings not in known_names
        potential_orgs = re.findall(
            r"\b([A-Z][a-z]+ (?:Private )?(?:Limited|Authority|Corporation|Commission|Board|Society))\b",
            text,
        )
        unknown = [
            org for org in potential_orgs
            if org.lower() not in known_names and len(org) > 10
        ]

        if unknown:
            return ValidationCheck(
                check_id="UNSUPPORTED_NAMES_FLAGGED",
                category=CheckCategory.UNSUPPORTED_CONTENT,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.WARNING,
                message=f"Potentially unsupported organization names detected: {', '.join(set(unknown))}",
                evidence=str(set(unknown)),
                source_rule="Section 5F: Unsupported entity names must be flagged",
                suggested_correction="Review and verify these organisation names are from supplied case data",
            )

        return ValidationCheck(
            check_id="UNSUPPORTED_NAMES_FLAGGED",
            category=CheckCategory.UNSUPPORTED_CONTENT,
            status=CheckStatus.PASS,
            severity=CheckSeverity.WARNING,
            message="No unsupported organisation names detected",
            source_rule="Section 5F: Unsupported entity names must be flagged",
        )

    def _check_unsupported_dates(self, case_data: CaseData, text: str) -> ValidationCheck:
        # Known dates from case data
        known_dates = {case_data.verification.date}
        for exhibit in case_data.exhibits:
            # Extract dates from exhibit descriptions
            date_matches = re.findall(r"\d{1,2} \w+ \d{4}", exhibit.description)
            known_dates.update(date_matches)

        # Find all date-like patterns in text
        found_dates = set(re.findall(r"\d{1,2} \w+ \d{4}", text))
        unknown_dates = found_dates - known_dates

        if unknown_dates:
            return ValidationCheck(
                check_id="UNSUPPORTED_DATES_FLAGGED",
                category=CheckCategory.UNSUPPORTED_CONTENT,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.WARNING,
                message=f"Dates not traceable to case data: {', '.join(unknown_dates)}",
                evidence=str(unknown_dates),
                source_rule="Section 5F: Unsupported dates must be flagged",
                suggested_correction="Verify these dates exist in supplied case information",
            )

        return ValidationCheck(
            check_id="UNSUPPORTED_DATES_FLAGGED",
            category=CheckCategory.UNSUPPORTED_CONTENT,
            status=CheckStatus.PASS,
            severity=CheckSeverity.WARNING,
            message="All dates are traceable to supplied case data",
            source_rule="Section 5F: Unsupported dates must be flagged",
        )

    def _check_missing_required_info(self, case_data: CaseData) -> ValidationCheck:
        missing = case_data.unresolved_fields

        if missing:
            return ValidationCheck(
                check_id="MISSING_REQUIRED_INFORMATION_FLAGGED",
                category=CheckCategory.COMPLETENESS,
                status=CheckStatus.WARNING,
                severity=CheckSeverity.WARNING,
                message=f"These required fields were not resolved during extraction: {', '.join(missing)}",
                expected="All fields resolved",
                actual=f"{len(missing)} unresolved fields",
                source_rule="Section 5F: Missing required information must be flagged",
            )

        return ValidationCheck(
            check_id="MISSING_REQUIRED_INFORMATION_FLAGGED",
            category=CheckCategory.COMPLETENESS,
            status=CheckStatus.PASS,
            severity=CheckSeverity.WARNING,
            message="All required information was resolved",
            source_rule="Section 5F: Missing required information must be flagged",
        )
