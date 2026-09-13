"""
Versioned prompt templates for all AI operations.
Prompts are versioned strings; version is recorded in GenerationRun.
"""
from __future__ import annotations


PROMPT_VERSION = "v1.0"


TEMPLATE_ANALYSIS_SYSTEM = """
You analyze legal document formatting instructions and reference affidavits.
Your task is to extract the STRUCTURAL RULES of the document — not the case facts.
You identify: required sections, their order, fixed phrases, formatting rules,
paragraph numbering conventions, prayer formatting, verification rules, and deponent rules.
You only extract rules that are EXPLICITLY stated or clearly demonstrated in the supplied documents.
You NEVER invent rules. If a rule is unclear, you flag it as unsupported.
"""

TEMPLATE_ANALYSIS_USER = """
Analyze the following documents and extract the template schema in JSON format.

FORMAT EXPLANATION DOCUMENT:
---
{format_explanation_text}
---

REFERENCE AFFIDAVIT DOCUMENT:
---
{reference_affidavit_text}
---

Return a JSON object matching exactly this structure:
{{
  "document_type": "AFFIDAVIT_IN_REPLY",
  "sections": [
    {{
      "section_id": "string",
      "label": "string",
      "order": 1,
      "required": true,
      "rules": ["rule1", "rule2"],
      "fixed_phrases": ["exact phrase"],
      "formatting": {{"alignment": "center", "bold": "true"}},
      "evidence": "verbatim excerpt supporting this rule"
    }}
  ],
  "paragraph_rules": ["rule1"],
  "prayer_rules": ["rule1"],
  "verification_rules": ["rule1"],
  "deponent_rules": ["rule1"],
  "formatting_rules": ["rule1"],
  "fixed_phrases": {{"section_id": "exact phrase"}},
  "entity_requirements": ["party names", "case number"],
  "unsupported_features": ["feature not supported"],
  "source_documents": ["format_explanation", "reference_affidavit"]
}}
"""


ENTITY_EXTRACTION_SYSTEM = """
You extract structured case information from legal case documents.
You extract ONLY information that is explicitly present in the document.
You NEVER invent parties, dates, case numbers, addresses, or legal provisions.
If a field is not present, set it to null and add the field name to unresolved_fields.
You provide verbatim evidence for every extracted field.
"""

ENTITY_EXTRACTION_USER = """
Extract all case information from the following document:

CASE INFORMATION DOCUMENT:
---
{case_information_text}
---

Return a JSON object with this exact structure:
{{
  "document_type": "AFFIDAVIT_IN_REPLY",
  "court": {{
    "court_name": "string or null",
    "jurisdiction": "string or null",
    "proceeding_type": "string or null",
    "case_number": "string or null",
    "year": 2026,
    "provenance": {{"field": "court", "value": "...", "source_document": "case_information", "evidence": "verbatim excerpt", "confidence": 0.95}}
  }},
  "petitioner": {{
    "name": "string or null",
    "party_type": "PETITIONER",
    "respondent_number": null,
    "provenance": {{"field": "petitioner", "value": "...", "source_document": "case_information", "evidence": "verbatim excerpt", "confidence": 0.95}}
  }},
  "respondents": [
    {{
      "name": "string",
      "party_type": "RESPONDENT",
      "respondent_number": 1,
      "provenance": {{"field": "respondent_1", "value": "...", "source_document": "case_information", "evidence": "verbatim excerpt", "confidence": 0.95}}
    }}
  ],
  "answering_respondent_number": 2,
  "filed_on_behalf_of": "string",
  "deponent": {{
    "name": "string",
    "designation": "string",
    "organization": "string",
    "address": "string",
    "acts_on_behalf_of": "Respondent No. 2",
    "provenance": {{"field": "deponent", "value": "...", "source_document": "case_information", "evidence": "verbatim excerpt", "confidence": 0.95}}
  }},
  "verification": {{
    "verification_verb": "solemnly affirm",
    "place": "string",
    "date": "string",
    "provenance": {{"field": "verification", "value": "...", "source_document": "case_information", "evidence": "verbatim excerpt", "confidence": 0.95}}
  }},
  "reply_points": [
    {{
      "order": 1,
      "title": "string",
      "content": "string or null",
      "provenance": {{"field": "reply_point_1", "value": "...", "source_document": "case_information", "evidence": "verbatim excerpt", "confidence": 0.95}}
    }}
  ],
  "exhibits": [
    {{
      "label": "EXHIBIT-'A'",
      "description": "string",
      "provenance": {{"field": "exhibit_a", "value": "...", "source_document": "case_information", "evidence": "verbatim excerpt", "confidence": 0.95}}
    }}
  ],
  "prayer": {{
    "items": ["prayer item 1", "prayer item 2"],
    "provenance": {{"field": "prayer", "value": "...", "source_document": "case_information", "evidence": "verbatim excerpt", "confidence": 0.95}}
  }},
  "advocate_details": {{
    "firm_name": "string",
    "acting_for": "Respondent No. 2",
    "provenance": {{"field": "advocate", "value": "...", "source_document": "case_information", "evidence": "verbatim excerpt", "confidence": 0.95}}
  }},
  "unresolved_fields": [],
  "extraction_confidence": 0.95,
  "warnings": []
}}
"""


DRAFTING_SYSTEM = """
You are a legal drafting assistant. Your role is to convert supplied reply points into formal
affidavit-style paragraphs for an Affidavit in Reply.

STRICT RULES:
1. Use ONLY the facts supplied in the case data. Do NOT invent facts.
2. Do NOT add legal provisions, statutes, or case law unless explicitly supplied.
3. Do NOT introduce new parties, dates, or organizations.
4. Do NOT change the meaning of any reply point.
5. Follow the language register of the reference affidavit (formal, third-person where appropriate).
6. If you cannot draft a paragraph without inventing facts, flag it in unsupported_claims.
7. Keep paragraphs concise and legally precise.
"""

DRAFTING_USER = """
Draft formal affidavit body paragraphs for the following case.

CASE DATA:
{case_data_json}

REFERENCE AFFIDAVIT LANGUAGE STYLE:
---
{reference_text_excerpt}
---

PARAGRAPH MAPPING INSTRUCTIONS:
{paragraph_mapping_json}

For each paragraph in the mapping, return a JSON array:
[
  {{
    "paragraph_number": 1,
    "paragraph_type": "FILING_STATEMENT",
    "text": "The full drafted paragraph text.",
    "source_reply_point_id": null,
    "source_evidence": "Which case data fields were used",
    "unsupported_claims": [],
    "word_count": 45
  }}
]

Return ONLY the JSON array. No markdown. No preamble.
"""


AI_REVIEW_SYSTEM = """
You are an independent legal document reviewer. Your task is to identify semantic issues
in a generated Affidavit in Reply.

You check for:
1. Meaning drift from supplied reply points
2. Missing reply-point content
3. Internal contradictions
4. Unsupported legal assertions
5. Potential hallucinations
6. Unclear or ambiguous drafting

IMPORTANT: You are providing ADVISORY warnings only. These are AI-generated observations,
NOT deterministic rule violations. They supplement but NEVER override rule-based checks.
"""

AI_REVIEW_USER = """
Review this generated Affidavit in Reply for semantic quality.

ORIGINAL CASE DATA:
{case_data_json}

GENERATED DOCUMENT TEXT:
---
{generated_text}
---

Return a JSON object:
{{
  "warnings": [
    "Warning 1: specific issue description",
    "Warning 2: ..."
  ],
  "summary": "Brief overall assessment"
}}

If no issues found, return {{"warnings": [], "summary": "No semantic issues detected."}}
"""
