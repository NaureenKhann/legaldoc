"""
Case data Pydantic schemas — the authoritative structured representation
of all facts extracted from the case information document.
"""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import ProvenanceField


class Party(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(description="Full legal name of the party")
    party_type: Literal["PETITIONER", "RESPONDENT"]
    respondent_number: Optional[int] = Field(
        default=None, description="e.g. 1 for Respondent No. 1"
    )
    provenance: Optional[ProvenanceField] = None


class Deponent(BaseModel):
    name: str = Field(description="Full name of the deponent")
    designation: str = Field(description="Official designation/title")
    organization: str = Field(description="Organisation the deponent belongs to")
    address: str = Field(description="Official address")
    acts_on_behalf_of: str = Field(
        description="Party name/number this deponent represents"
    )
    provenance: Optional[ProvenanceField] = None


class CourtDetails(BaseModel):
    court_name: str = Field(description="Full name of the court")
    jurisdiction: str = Field(description="e.g. Ordinary Original Civil Jurisdiction")
    proceeding_type: str = Field(description="e.g. Writ Petition")
    case_number: str = Field(description="Case number as string (may include slashes)")
    year: int = Field(description="Year of the proceeding")
    provenance: Optional[ProvenanceField] = None


class Exhibit(BaseModel):
    label: str = Field(description="Exhibit label, e.g. EXHIBIT-'A'")
    description: str = Field(description="What the exhibit contains")
    provenance: Optional[ProvenanceField] = None


class ReplyPoint(BaseModel):
    order: int = Field(ge=1, description="1-based order in the affidavit body")
    title: str = Field(description="Short title of the reply point")
    content: Optional[str] = Field(
        default=None, description="Detailed content if available"
    )
    provenance: Optional[ProvenanceField] = None


class PrayerDetails(BaseModel):
    items: list[str] = Field(description="Ordered prayer items (lettered by generator)")
    provenance: Optional[ProvenanceField] = None


class AttestationDetails(BaseModel):
    verification_verb: str = Field(
        description="'solemnly affirm' or 'swear'"
    )
    place: str = Field(description="Place of verification")
    date: str = Field(description="Date of verification (formatted)")
    provenance: Optional[ProvenanceField] = None


class AdvocateDetails(BaseModel):
    firm_name: str = Field(description="Name of the advocate/firm")
    acting_for: str = Field(description="Party description, e.g. 'Respondent No. 2'")
    provenance: Optional[ProvenanceField] = None


class CaseData(BaseModel):
    """
    The single authoritative structured representation of all case facts.
    Every field should trace back to the case_information source document.
    """
    model_config = ConfigDict(from_attributes=True)

    document_type: str = Field(default="AFFIDAVIT_IN_REPLY")
    court: CourtDetails
    petitioner: Party
    respondents: list[Party] = Field(min_length=1)
    answering_respondent_number: int = Field(
        ge=1, description="Which respondent is filing this affidavit"
    )
    filed_on_behalf_of: str = Field(
        description="Full name/designation of the entity on whose behalf this is filed"
    )
    deponent: Deponent
    verification: AttestationDetails
    reply_points: list[ReplyPoint] = Field(min_length=1)
    exhibits: list[Exhibit] = Field(default_factory=list)
    prayer: PrayerDetails
    advocate_details: AdvocateDetails

    # Quality fields
    unresolved_fields: list[str] = Field(
        default_factory=list,
        description="Fields that could not be extracted with confidence",
    )
    extraction_confidence: float = Field(
        ge=0.0, le=1.0, default=1.0, description="Overall extraction confidence"
    )
    warnings: list[str] = Field(
        default_factory=list, description="Non-fatal extraction warnings"
    )

    def get_answering_respondent(self) -> Party | None:
        for r in self.respondents:
            if r.respondent_number == self.answering_respondent_number:
                return r
        return None

    @field_validator("respondents")
    @classmethod
    def respondents_have_numbers(cls, v: list[Party]) -> list[Party]:
        for r in v:
            if r.party_type == "RESPONDENT" and r.respondent_number is None:
                raise ValueError(f"Respondent '{r.name}' is missing a respondent_number")
        return v


# ─── Request/Response wrappers ─────────────────────────────────────────────────

class CaseDataResponse(BaseModel):
    matter_id: str
    case_data: CaseData
    extraction_confidence: float
    unresolved_fields: list[str]
    warnings: list[str]


class CaseDataUpdateRequest(BaseModel):
    """Allow human reviewers to patch specific fields."""
    field_path: str = Field(description="Dot-notation path, e.g. 'court.case_number'")
    new_value: Any
    review_note: Optional[str] = None
