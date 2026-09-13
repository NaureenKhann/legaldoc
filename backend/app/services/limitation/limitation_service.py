"""Limitation & Condonation of Delay Calculator & Petition Drafting Service."""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any, Dict, Optional
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt


class LimitationService:
    """Calculates delay under Limitation Act and auto-drafts Section 5 Condonation Petition."""

    def calculate_delay(
        self,
        order_date_str: str,
        filing_date_str: Optional[str] = None,
        statutory_limit_days: int = 30,
    ) -> Dict[str, Any]:
        """Calculate statutory delay days and return limitation metrics."""
        try:
            order_date = datetime.strptime(order_date_str, "%Y-%m-%d")
        except ValueError:
            # Fallback format DD.MM.YYYY
            try:
                order_date = datetime.strptime(order_date_str, "%d.%m.%Y")
            except ValueError:
                order_date = datetime.now()

        if filing_date_str:
            try:
                filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d")
            except ValueError:
                filing_date = datetime.now()
        else:
            filing_date = datetime.now()

        elapsed_days = (filing_date - order_date).days
        delay_days = max(0, elapsed_days - statutory_limit_days)
        is_delayed = delay_days > 0

        return {
            "order_date": order_date.strftime("%d.%m.%Y"),
            "filing_date": filing_date.strftime("%d.%m.%Y"),
            "statutory_limit_days": statutory_limit_days,
            "elapsed_days": elapsed_days,
            "delay_days": delay_days,
            "is_delayed": is_delayed,
            "statutory_section": "Section 5 of the Limitation Act, 1963",
        }

    def generate_condonation_docx(
        self,
        case_data: Dict[str, Any],
        limitation_info: Dict[str, Any],
    ) -> bytes:
        """Generate a court-ready Section 5 Condonation of Delay Application in DOCX format."""
        doc = Document()

        for section in doc.sections:
            section.top_margin = Inches(1.0)
            section.bottom_margin = Inches(1.0)
            section.left_margin = Inches(1.25)
            section.right_margin = Inches(1.0)

        # Court Header
        p_head = doc.add_paragraph()
        p_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_h = p_head.add_run(
            f"IN THE HIGH COURT OF JUDICATURE AT BOMBAY\n"
            f"{case_data.get('court_jurisdiction', 'WRIT JURISDICTION').upper()}\n"
            f"INTERLOCUTORY APPLICATION NO. _____ OF {datetime.now().year}\n"
            f"IN\n"
            f"WRIT PETITION NO. _____ OF {datetime.now().year}\n"
        )
        r_h.bold = True
        r_h.font.size = Pt(12)
        r_h.font.name = "Times New Roman"

        # Parties Block
        p_party = doc.add_paragraph()
        p_party.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_p = p_party.add_run(
            f"IN THE MATTER OF:\n"
            f"{case_data.get('petitioner_name', 'APPLICANT / PETITIONER').upper()} ... APPLICANT\n"
            f"VERSUS\n"
            f"{case_data.get('respondent_name', 'RESPONDENT').upper()} ... RESPONDENTS\n\n"
        )
        r_p.bold = True
        r_p.font.size = Pt(11)
        r_p.font.name = "Times New Roman"

        # Application Title
        p_title = doc.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_t = p_title.add_run(
            f"APPLICATION UNDER SECTION 5 OF THE LIMITATION ACT, 1963 FOR CONDONATION OF DELAY OF {limitation_info.get('delay_days', 0)} DAYS IN FILING THE PETITION\n"
        )
        r_t.bold = True
        r_t.underline = True
        r_t.font.size = Pt(13)
        r_t.font.name = "Times New Roman"

        # Body Paragraphs
        paragraphs = [
            (
                "1. That the Applicant / Petitioner has filed the accompanying Writ Petition challenging the impugned order / notice "
                f"dated {limitation_info.get('order_date', '')} passed by the Respondent Authorities."
            ),
            (
                f"2. That as per applicable statutory rules, the prescribed limitation period for filing the petition is {limitation_info.get('statutory_limit_days', 30)} days. "
                f"However, there has occurred a unintentional delay of {limitation_info.get('delay_days', 0)} days in preferring the present petition."
            ),
            (
                "3. That the delay of "
                f"{limitation_info.get('delay_days', 0)} days was caused due to bona fide, genuine, and unavoidable circumstances, including administrative process time in collecting certified copies and seeking legal opinion."
            ),
            (
                "4. That the Applicant has a strong prima facie case on merits and the balance of convenience lies entirely in favor of the Applicant. "
                "No prejudice or hardship will be caused to the Respondents if the delay is condoned."
            ),
            (
                "5. That the present application is made bona fide and in the interest of justice."
            ),
        ]

        for p_text in paragraphs:
            p = doc.add_paragraph()
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.space_after = Pt(8)
            run = p.add_run(p_text)
            run.font.name = "Times New Roman"
            run.font.size = Pt(12)

        # Prayer Block
        p_prayer = doc.add_paragraph()
        p_prayer.paragraph_format.space_before = Pt(12)
        r_pr_h = p_prayer.add_run("PRAYER\n")
        r_pr_h.bold = True
        r_pr_h.font.size = Pt(12)
        r_pr_h.font.name = "Times New Roman"

        p_pr_text = doc.add_paragraph()
        p_pr_text.paragraph_format.line_spacing = 1.5
        r_pr = p_pr_text.add_run(
            f"It is therefore most respectfully prayed that this Hon'ble Court may be pleased to:\n"
            f"a) Condone the delay of {limitation_info.get('delay_days', 0)} days in filing the accompanying Writ Petition;\n"
            f"b) Pass such other or further order(s) as this Hon'ble Court may deem fit and proper in the circumstances of the case."
        )
        r_pr.font.size = Pt(12)
        r_pr.font.name = "Times New Roman"

        # Advocate Block
        p_adv = doc.add_paragraph()
        p_adv.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_adv.paragraph_format.space_before = Pt(24)
        r_adv = p_adv.add_run(
            "FILED BY:\n\n_______________________\nADVOCATE FOR THE APPLICANT\nBOMBAY HIGH COURT"
        )
        r_adv.bold = True
        r_adv.font.size = Pt(11)
        r_adv.font.name = "Times New Roman"

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
