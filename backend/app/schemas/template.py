"""
Template schema — describes the structural rules derived from
the format explanation and reference affidavit documents.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SectionRule(BaseModel):
    section_id: str = Field(description="Machine-readable ID, e.g. 'forum_heading'")
    label: str = Field(description="Human-readable label")
    order: int = Field(ge=1, description="1-based position in document")
    required: bool
    rules: list[str] = Field(default_factory=list, description="Specific rules for this section")
    fixed_phrases: list[str] = Field(
        default_factory=list, description="Exact phrases that must appear"
    )
    formatting: dict[str, str] = Field(
        default_factory=dict,
        description="Formatting hints: alignment, bold, font_size etc."
    )
    evidence: str = Field(description="Excerpt from source document supporting this rule")


class TemplateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_type: str = Field(default="AFFIDAVIT_IN_REPLY")
    sections: list[SectionRule] = Field(description="Ordered list of required sections")
    paragraph_rules: list[str] = Field(description="Rules for body paragraph numbering/format")
    prayer_rules: list[str] = Field(description="Rules specific to the prayer section")
    verification_rules: list[str] = Field(description="Rules for verification paragraph + range")
    deponent_rules: list[str] = Field(description="Rules about deponent description")
    formatting_rules: list[str] = Field(description="General formatting conventions")
    fixed_phrases: dict[str, str] = Field(
        default_factory=dict,
        description="Map of section_id → fixed phrase that must appear verbatim",
    )
    entity_requirements: list[str] = Field(
        description="Entities that must be present in the document"
    )
    unsupported_features: list[str] = Field(
        default_factory=list,
        description="Features mentioned in format_explanation but not supported by reference",
    )
    source_documents: list[str] = Field(
        description="Document types that were used to derive this schema"
    )


class TemplateSchemaResponse(BaseModel):
    matter_id: str
    template: TemplateSchema
    section_count: int
    required_section_count: int
