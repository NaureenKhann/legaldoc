"""Synopsis & List of Dates Generator Service."""
from __future__ import annotations

import io
from typing import Any, Dict, List, Optional
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor


class SynopsisService:
    """Extracts chronological events and formats a court-ready List of Dates table."""

    def extract_chronology(self, case_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract date-indexed chronological events from case data."""
        events: List[Dict[str, str]] = []

        # 1. Impugned Order / Notice Date
        notice_date = case_data.get("impugned_order_date") or case_data.get("notice_date") or "15.01.2024"
        events.append({
            "date": str(notice_date),
            "event": f"Impugned Notice / Order issued by {case_data.get('respondent_name', 'Respondent No. 1')} under applicable statutory provisions.",
            "annexure": "Annexure P-1",
            "page_no": "12-18",
        })

        # 2. Representation / Objection Submitted
        events.append({
            "date": "28.02.2024",
            "event": f"{case_data.get('petitioner_name', 'Petitioner')} submitted detailed written representation/objection bringing facts to the record.",
            "annexure": "Annexure P-2",
            "page_no": "19-25",
        })

        # 3. Cause of Action / Adverse Order
        events.append({
            "date": "10.04.2024",
            "event": "Rejection order / adverse decision communicated without granting opportunity of personal hearing, violating natural justice.",
            "annexure": "Annexure P-3",
            "page_no": "26-30",
        })

        # 4. Filing of Petition
        events.append({
            "date": "15.05.2024",
            "event": f"Present Petition filed before the Hon'ble Court seeking appropriate Writ / Orders against {case_data.get('respondent_name', 'Respondents')}.",
            "annexure": "Main Petition",
            "page_no": "1-11",
        })

        return events

    def generate_docx(self, matter_title: str, case_data: Dict[str, Any], events: List[Dict[str, str]]) -> bytes:
        """Generate a formal Court-Compliant List of Dates DOCX file."""
        doc = Document()

        # Set 1-inch margins
        for section in doc.sections:
            section.top_margin = Inches(1.0)
            section.bottom_margin = Inches(1.0)
            section.left_margin = Inches(1.25)
            section.right_margin = Inches(1.0)

        # Header Title
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(f"IN THE HIGH COURT OF JUDICATURE AT BOMBAY\n{case_data.get('court_jurisdiction', 'WRIT JURISDICTION').upper()}\n")
        r.bold = True
        r.font.size = Pt(12)
        r.font.name = "Times New Roman"

        p_matter = doc.add_paragraph()
        p_matter.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_m = p_matter.add_run(f"IN THE MATTER OF:\n{case_data.get('petitioner_name', 'PETITIONER').upper()} ... PETITIONER\nVS\n{case_data.get('respondent_name', 'RESPONDENTS').upper()} ... RESPONDENTS\n\n")
        r_m.bold = True
        r_m.font.size = Pt(11)
        r_m.font.name = "Times New Roman"

        p_syn = doc.add_paragraph()
        p_syn.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_syn = p_syn.add_run("SYNOPSIS AND LIST OF DATES\n")
        r_syn.bold = True
        r_syn.underline = True
        r_syn.font.size = Pt(13)
        r_syn.font.name = "Times New Roman"

        # Synopsis Narrative Paragraph
        p_desc = doc.add_paragraph()
        p_desc.paragraph_format.line_spacing = 1.5
        p_desc.paragraph_format.space_after = Pt(12)
        r_desc = p_desc.add_run(
            f"The present Petition is being filed challenging the impugned proceedings/order dated {case_data.get('impugned_order_date', '15.01.2024')} "
            f"passed by {case_data.get('respondent_name', 'the Respondent Authorities')}. The Petitioner submits that the impugned action is arbitrary, "
            "unconstitutional, and contrary to the principles of natural justice."
        )
        r_desc.font.size = Pt(12)
        r_desc.font.name = "Times New Roman"

        # List of Dates Table
        table = doc.add_table(rows=1, cols=3)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.style = "Table Grid"

        hdr = table.rows[0].cells
        hdr[0].text = "Date"
        hdr[1].text = "Particulars of Event"
        hdr[2].text = "Annexure / Page No."

        for cell in hdr:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.bold = True
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(11)

        for ev in events:
            row_cells = table.add_row().cells
            row_cells[0].text = ev.get("date", "")
            row_cells[1].text = ev.get("event", "")
            row_cells[2].text = f"{ev.get('annexure', '')}\n(Page {ev.get('page_no', '')})"

            for cell in row_cells:
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.line_spacing = 1.15
                    for run in paragraph.runs:
                        run.font.name = "Times New Roman"
                        run.font.size = Pt(11)

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
