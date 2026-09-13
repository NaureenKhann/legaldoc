# LegalDoc Intelligence Platform

> **AI-powered Affidavit in Reply generation, validation, and evaluation.**
> Built for professional legal document processing — not for direct legal filing without human review.

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)](https://postgresql.org)

---

## Problem Statement

Generating a legally structured Affidavit in Reply requires:
- Accurate extraction of case facts from multiple documents
- Template-aware document structure (not generic layout)
- Every generated fact traceable to a source
- Independent validation of the output (not trusting the drafting LLM)
- Transparent scoring of document quality

This platform solves each of these requirements with a **traceable processing pipeline**.

---

## Core Principle

> **AI interprets and drafts. Python validates and controls structure.**
> Never blindly trust generated legal content.

The system uses:
- **Structured intermediate representation** — every extracted fact is stored in a typed Pydantic schema
- **Template-aware generation** — structure comes from Python, not LLM layout
- **Provenance** — every field records its source document and verbatim evidence
- **Independent validation** — 25 deterministic checks run separately from the drafting LLM
- **Explainable scoring** — every deduction is documented

---

## Architecture

```mermaid
flowchart TB
    User(["👤 User / Reviewer"])

    subgraph FE["NEXT.JS FRONTEND (Vercel)"]
        Dashboard["Dashboard"]
        Upload["Upload + Create Matter"]
        Workspace["Matter Workspace"]
        Evaluation["Evaluation Report"]
    end

    subgraph BE["PYTHON BACKEND (FastAPI / Railway)"]
        API["REST API Layer\n/api/v1"]

        subgraph Pipeline["AI Processing Pipeline"]
            Ingest["Document\nIngestion"]
            Template["Template\nAnalyzer"]
            Extract["Entity\nExtractor"]
            Map["Content\nMapper"]
            Draft["Drafting\nEngine"]
            DocxGen["DOCX\nGenerator"]
            Val["Validation\nEngine\n(25 checks)"]
            Score["Scoring\nEngine"]
            Report["Evaluation\nReporter"]
        end

        subgraph AI["AI Layer"]
            LLM["Provider Adapter\n(OpenAI/Anthropic/Gemini)"]
            Prompts["Versioned\nPrompts"]
        end
    end

    subgraph Store["Storage"]
        DB[("PostgreSQL")]
        Files["File Storage\n(uploads + generated)"]
    end

    subgraph Out["Generated Artifacts"]
        DOCX[".docx\nAffidavit"]
        MD["Evaluation\nMarkdown Report"]
        JSON["Evaluation\nJSON Report"]
    end

    User --> FE
    FE --> API
    API --> Pipeline
    Pipeline --> AI
    Pipeline --> DB
    Ingest --> Files
    DocxGen --> DOCX
    Report --> MD & JSON
```

---

## Features

### Document Generation Pipeline
- Upload 3 input documents (Format Explanation, Reference Affidavit, Case Information)
- Automatic text extraction from PDF and DOCX
- LLM-powered entity extraction with structured output
- Template analysis from reference documents
- Python-controlled DOCX generation (LLM never controls layout)
- Exhibit reference management
- Precise verification range calculation

### Independent Validation (25 Checks)
All checks are deterministic and run independently of the drafting LLM:

| Category | Checks |
|----------|--------|
| Entity Accuracy | Court, jurisdiction, case number, petitioner, respondents, deponent, designation |
| Completeness | Required sections, prayer, jurat, verification, exhibit references |
| Structure | Section order, paragraph numbering, prayer uses letters not numbers |
| Consistency | Answering respondent number, dates, places, advocate details |
| Template Fidelity | Organisation/deponent relationship, fixed phrases |
| Unsupported Content | Unknown organisation names, unknown dates |

### Evaluation & Scoring
| Category | Points |
|----------|--------|
| Entity Accuracy | 25 |
| Completeness | 20 |
| Structure | 20 |
| Consistency | 15 |
| Template Fidelity | 10 |
| Unsupported Content | 10 |
| **Total** | **100** |

### Error Injection Demo
Deliberately corrupt a document to test that the system catches:
- Wrong respondent number (should be 2, got 1)
- Wrong case number (1847 vs 9999)
- Missing verification section
- Incorrect paragraph range (1–10 vs actual 1–7)
- Unknown organisation names
- Date mismatches

---

## Technology Stack

### Backend
| Technology | Purpose |
|-----------|---------|
| Python 3.11+ | Runtime |
| FastAPI | REST API framework |
| Pydantic v2 | Typed schemas and validation |
| SQLAlchemy 2 (async) | ORM |
| Alembic | Database migrations |
| PostgreSQL 16 | Primary database |
| PyMuPDF (fitz) | PDF text extraction |
| python-docx | DOCX reading and generation |
| structlog | Structured logging with context |
| tenacity | LLM retry with exponential backoff |
| OpenAI / Anthropic / Gemini | LLM providers (pluggable) |

### Frontend
| Technology | Purpose |
|-----------|---------|
| Next.js 14 | App Router framework |
| TypeScript | Type safety |
| Tailwind CSS | Styling |
| TanStack Query | Server state management |
| React Hook Form | Form handling |
| React Dropzone | File upload UX |
| Recharts | Score visualisation |
| React Markdown | Report rendering |
| Lucide React | Icons |

---

## Repository Structure

```
legaldoc-intelligence/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app factory
│   │   ├── api/routes/                # All REST endpoints
│   │   ├── core/                      # Config, logging, security
│   │   ├── db/                        # SQLAlchemy models and session
│   │   ├── schemas/                   # Pydantic v2 schemas
│   │   ├── services/                  # All service modules
│   │   │   ├── document_ingestion/    # PDF + DOCX extraction
│   │   │   ├── template_analysis/     # TemplateAnalyzer
│   │   │   ├── entity_extraction/     # EntityExtractor (LLM)
│   │   │   ├── content_mapping/       # ContentMapper
│   │   │   ├── drafting/              # DraftingEngine (LLM)
│   │   │   ├── docx_generation/       # DocxGenerator (Python)
│   │   │   ├── validation/            # ValidationEngine (25 checks)
│   │   │   ├── scoring/               # ScoringEngine
│   │   │   └── reporting/             # EvaluationReporter
│   │   └── ai/                        # LLM provider adapter + prompts
│   └── tests/                         # Unit, integration, e2e tests
├── frontend/
│   └── src/
│       ├── app/                       # Next.js App Router pages
│       ├── components/                # UI components
│       └── lib/                       # API client + utilities
├── docker-compose.yml
└── README.md
```

---

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker Desktop (for PostgreSQL)
- At least one LLM API key (OpenAI, Anthropic, or Gemini)

### 1. Start Database

```bash
docker compose up postgres -d
```

### 2. Backend Setup

```bash
cd backend

# Copy environment variables
cp .env.example .env
# Edit .env and add your LLM API key

# Install dependencies
pip install poetry
poetry install

# Run migrations
poetry run alembic upgrade head

# Start backend
poetry run uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Copy environment
cp .env.local.example .env.local

# Install dependencies
npm install

# Start frontend
npm run dev
```

### 4. Access

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **OpenAPI Docs:** http://localhost:8000/docs

---

## Environment Variables

### Backend (`backend/.env`)

```env
DATABASE_URL=postgresql+asyncpg://legaldoc:legaldoc_secret@localhost:5432/legaldoc
LLM_PROVIDER=openai          # openai | anthropic | gemini
OPENAI_API_KEY=sk-...
DEMO_MODE=false              # true = run without LLM key
STORAGE_PATH=./storage
MAX_UPLOAD_SIZE_MB=20
```

### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_DEMO_MODE=false
```

---

## Database Migrations

```bash
# Create a new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback one step
poetry run alembic downgrade -1
```

---

## Testing

```bash
cd backend

# Run all unit tests
poetry run pytest tests/unit/ -v

# Run with coverage
poetry run pytest tests/ --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/unit/test_validation_engine.py -v

# Run error injection tests
poetry run pytest tests/unit/test_validation_engine.py -k "inject" -v
```

---

## Docker (Full Stack)

```bash
# Start everything
docker compose up --build

# Backend only
docker compose up postgres backend

# View logs
docker compose logs backend -f
```

---

## API Documentation

Full OpenAPI documentation is available at `http://localhost:8000/docs` when the backend is running.

### Key Endpoints

```
POST   /api/v1/matters                          # Create matter
POST   /api/v1/matters/{id}/documents           # Upload document
POST   /api/v1/matters/{id}/extract             # Extract entities (LLM)
POST   /api/v1/matters/{id}/generate            # Generate affidavit
GET    /api/v1/generation-runs/{run_id}/download # Download DOCX
POST   /api/v1/generation-runs/{run_id}/validate # Run 25 checks
GET    /api/v1/generation-runs/{run_id}/evaluation # Get report
GET    /api/v1/health                           # Health check
```

---

## Demo Mode

Set `DEMO_MODE=true` and `NEXT_PUBLIC_DEMO_MODE=true` to run the full pipeline without an LLM API key.

Demo mode uses:
- Cached structured extraction of the assignment case (Arvind Rajan / MMRDA)
- Deterministic paragraph drafting
- Fully functional 25-check validation engine
- Complete evaluation report generation

The UI displays a prominent amber banner when running in demo mode.

---

## Deployment

### Backend (Railway / Render)
1. Push backend to a GitHub repository
2. Connect to Railway or Render
3. Set environment variables (DATABASE_URL, LLM provider key)
4. Add DATABASE_URL from a managed PostgreSQL add-on

### Frontend (Vercel)
1. Push frontend to GitHub
2. Import to Vercel
3. Set `NEXT_PUBLIC_API_BASE_URL` to your deployed backend URL

---

## Evaluation Methodology

The scoring system uses 6 categories totalling 100 points.

**Deduction rules:**
- Each FAIL at ERROR severity deducts `max_category_points / total_checks_in_category`
- Each FAIL at WARNING severity deducts half the above
- Each WARNING in UNSUPPORTED_CONTENT deducts 2 points
- No category goes below 0

Every deduction is documented in the report with the check ID, expected/actual values, and suggested correction.

---

## Security Considerations

- File type validation (extension + MIME type)
- File size limits (configurable, default 20MB)
- Sanitized safe filenames preventing path traversal
- API keys stored in environment variables only — never in code or database
- No document content logged at INFO level
- Session-level database transactions with proper rollback
- Non-root Docker user

---

## Known Limitations (v0.1.0)

1. Synchronous processing (no background jobs) — suitable for demo
2. Local file storage (S3 adapter needed for production)
3. No authentication layer (add Clerk or Auth.js for production)
4. AI review layer is optional and marked as advisory
5. Extraction confidence is self-reported by the LLM — verify manually for critical fields

---

## AI Coding Assistant Disclosure

This project was developed with the assistance of an AI coding assistant (Antigravity/Claude). All architectural decisions, business logic, validation rules, and legal document structure rules were authored by the project team. The AI assistant was used to accelerate code writing, not to make legal or architectural decisions.

---

## License

MIT — For research and educational use only. Not for production legal filing.
