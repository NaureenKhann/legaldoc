"""
Tests for entity schema validation, missing fields, and CaseData integrity.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

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


def make_valid_case_data() -> dict:
    return {
        "document_type": "AFFIDAVIT_IN_REPLY",
        "court": {
            "court_name": "IN THE HIGH COURT OF JUDICATURE AT BOMBAY",
            "jurisdiction": "ORDINARY ORIGINAL CIVIL JURISDICTION",
            "proceeding_type": "Writ Petition",
            "case_number": "1847",
            "year": 2026,
        },
        "petitioner": {"name": "Sunrise Housing Private Limited", "party_type": "PETITIONER"},
        "respondents": [
            {"name": "State of Maharashtra", "party_type": "RESPONDENT", "respondent_number": 1},
            {"name": "MMRDA", "party_type": "RESPONDENT", "respondent_number": 2},
        ],
        "answering_respondent_number": 2,
        "filed_on_behalf_of": "Respondent No. 2",
        "deponent": {
            "name": "Arvind Rajan",
            "designation": "Deputy Commissioner",
            "organization": "MMRDA",
            "address": "Bandra East",
            "acts_on_behalf_of": "Respondent No. 2",
        },
        "verification": {
            "verification_verb": "solemnly affirm",
            "place": "Mumbai",
            "date": "5 September 2026",
        },
        "reply_points": [{"order": 1, "title": "Filing"}],
        "exhibits": [],
        "prayer": {"items": ["Dismiss the petition"]},
        "advocate_details": {"firm_name": "Rajan & Associates", "acting_for": "Respondent No. 2"},
        "extraction_confidence": 1.0,
    }


class TestCaseDataValidation:
    def test_valid_case_data_passes(self):
        data = make_valid_case_data()
        cd = CaseData.model_validate(data)
        assert cd.court.case_number == "1847"
        assert len(cd.respondents) == 2

    def test_respondent_without_number_fails(self):
        data = make_valid_case_data()
        data["respondents"] = [
            {"name": "State of Maharashtra", "party_type": "RESPONDENT"}  # no number
        ]
        with pytest.raises(ValidationError):
            CaseData.model_validate(data)

    def test_empty_respondents_fails(self):
        data = make_valid_case_data()
        data["respondents"] = []
        with pytest.raises(ValidationError):
            CaseData.model_validate(data)

    def test_empty_reply_points_fails(self):
        data = make_valid_case_data()
        data["reply_points"] = []
        with pytest.raises(ValidationError):
            CaseData.model_validate(data)

    def test_invalid_confidence_fails(self):
        data = make_valid_case_data()
        data["extraction_confidence"] = 1.5  # > 1.0
        with pytest.raises(ValidationError):
            CaseData.model_validate(data)

    def test_get_answering_respondent(self):
        data = make_valid_case_data()
        cd = CaseData.model_validate(data)
        r = cd.get_answering_respondent()
        assert r is not None
        assert r.respondent_number == 2
        assert r.name == "MMRDA"

    def test_unresolved_fields_stored(self):
        data = make_valid_case_data()
        data["unresolved_fields"] = ["court.address", "exhibit_b"]
        cd = CaseData.model_validate(data)
        assert "court.address" in cd.unresolved_fields

    def test_confidences_between_zero_and_one(self):
        data = make_valid_case_data()
        for c in [0.0, 0.5, 1.0]:
            data["extraction_confidence"] = c
            cd = CaseData.model_validate(data)
            assert 0.0 <= cd.extraction_confidence <= 1.0
