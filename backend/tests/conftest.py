"""Pytest configuration and shared fixtures."""
from __future__ import annotations

import os
import pytest
from typing import AsyncGenerator

# Use SQLite for tests
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_legaldoc.db"
os.environ["DEMO_MODE"] = "true"

from app.db.session import init_db, engine, AsyncSessionLocal
from app.db.models import Base


@pytest.fixture(autouse=True, scope="session")
async def setup_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="session")
def sample_case_information_text() -> str:
    return """
COURT:
IN THE HIGH COURT OF JUDICATURE AT BOMBAY

JURISDICTION:
ORDINARY ORIGINAL CIVIL JURISDICTION

PROCEEDING:
WRIT PETITION

CASE NUMBER:
1847

YEAR:
2026

PETITIONER:
Sunrise Housing Private Limited

RESPONDENT NO. 1:
State of Maharashtra

RESPONDENT NO. 2:
Mumbai Metropolitan Region Development Authority

ANSWERING RESPONDENT:
Respondent No. 2

DEPONENT:
Arvind Rajan

DESIGNATION:
Deputy Metropolitan Commissioner

ORGANIZATION:
Mumbai Metropolitan Region Development Authority

ADDRESS:
Bandra East, Mumbai, Maharashtra

VERIFICATION VERB:
solemnly affirm

PLACE:
Mumbai

DATE:
5 September 2026

ADVOCATE FIRM:
Rajan & Associates

ACTING FOR:
Respondent No. 2

REPLY POINTS:
1. Filing of Affidavit in Reply
2. General Denial
3. Preliminary Position
4. Denial Regarding the Communication
5. Authority for the Communication
6. Document Relied Upon

COMMUNICATION DATE:
15 July 2026

EXHIBIT:
EXHIBIT-'A'
"""


@pytest.fixture(scope="session")
def sample_format_explanation_text() -> str:
    return """
AFFIDAVIT IN REPLY — FORMAT EXPLANATION

An Affidavit in Reply must contain the following ten required parts in order:

1. FORUM HEADING
   The full name of the court in uppercase, centre-aligned, bold.

2. JURISDICTION
   The jurisdictional designation in uppercase, centre-aligned.

3. CASE NUMBER
   The proceeding type and number in the format: WRIT PETITION NO. [number] OF [year].

4. CAUSE TITLE
   Petitioner above and all respondents below, separated by VERSUS.

5. AFFIDAVIT TITLE
   Must state: AFFIDAVIT IN REPLY ON BEHALF OF RESPONDENT NO. [number]

6. DEPONENT CLAUSE
   The deponent must state their name, designation, organisation, and that they act
   on behalf of the named respondent. The deponent must not be confused with the organisation.

7. BODY PARAGRAPHS
   Must be numbered sequentially starting at 1. Each reply point corresponds to one paragraph.
   The last paragraph must be a closing paragraph.

8. PRAYER
   Must use letter notation (a), (b), (c)... NOT numeric notation 1, 2, 3.
   Introduced by the phrase "It is, therefore, respectfully prayed that this Hon'ble Court
   may be pleased to."

9. JURAT / ATTESTATION
   Must state: "Solemnly affirmed at [place] on [date]."

10. VERIFICATION
    Must state: "I, [deponent name], do hereby verify that the contents of paragraphs
    [range] are true and correct to the best of my knowledge, information and belief."
    THE RANGE MUST MATCH THE ACTUAL NUMBER OF BODY PARAGRAPHS.
    Verified at [place] on [date].

ADDITIONAL RULES:
- The advocate/drafting block appears at the end.
- Exhibit references must appear in the body paragraph that mentions them.
- All dates must be supplied; do not invent dates.
- The answering respondent number must be consistent throughout.
"""
