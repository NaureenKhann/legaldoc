"""
Mapping schemas — describe how CaseData fields map to document sections.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ParagraphType(str, Enum):
    FILING_STATEMENT = "FILING_STATEMENT"
    GENERAL_DENIAL = "GENERAL_DENIAL"
    PRELIMINARY_POSITION = "PRELIMINARY_POSITION"
    SUBSTANTIVE_ANSWER = "SUBSTANTIVE_ANSWER"
    CLOSING_PARAGRAPH = "CLOSING_PARAGRAPH"


class MappingEntry(BaseModel):
    """Maps a document section to its source CaseData fields."""
    section: str = Field(description="section_id from TemplateSchema")
    section_label: str
    source_fields: list[str] = Field(description="CaseData field paths used to populate this section")
    value: str = Field(description="Resolved value for this section")
    is_resolved: bool = Field(default=True)
    unresolved_reason: Optional[str] = Field(default=None)


class ParagraphMapping(BaseModel):
    """Maps a body paragraph to its reply point."""
    paragraph_number: int = Field(ge=1)
    paragraph_type: ParagraphType
    reply_point_order: Optional[int] = Field(
        default=None, description="Original ReplyPoint.order"
    )
    reply_point_title: Optional[str] = None
    source_fields: list[str] = Field(default_factory=list)
    draft_instruction: str = Field(
        default="", description="Instruction for the drafting engine"
    )


class MappingPlan(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    matter_id: str
    sections: list[MappingEntry]
    body_paragraphs: list[ParagraphMapping]
    expected_body_count: int
    verification_range: str = Field(
        description="e.g. 'paragraphs 1 to 6' — calculated, not copied from reference"
    )
    unresolved_sections: list[str] = Field(default_factory=list)
    exhibits: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class MappingPlanResponse(BaseModel):
    matter_id: str
    mapping: MappingPlan
    is_complete: bool
    unresolved_count: int
