# SpecSentinel

**AI Bid Risk Intelligence + Execution + Communication Engine for MEP Contractors**

SpecSentinel analyzes construction spec PDFs and meeting notes to help HVAC, Plumbing, and Electrical contractors decide whether to bid, quantify financial risk, identify scope obligations, generate execution tasks, and auto-draft stakeholder emails.

**UNSTRUCTURED DOCUMENTS -> DECISIONS -> FINANCIALS -> TASKS -> COMMUNICATION**

## Features

- **Bid Decision Engine**: Go/No-Go recommendation with confidence and contingency %
- **Financial Risk Analysis**: Total exposure range, cost drivers, LD/bond/warranty breakdown
- **Risk Flags**: Severity, cost range, source quotes, page references, recommended actions
- **Requirements Extraction**: Insurance, bonding, warranty, LDs, testing, commissioning, submittals, schedule
- **Division Breakdown**: Div 22 (Plumbing), Div 23 (HVAC), Div 26 (Electrical)
- **ActionBoard**: Three-column task board — To Clarify (RFI) / Must Include in Bid / Internal Tasks
- **Meeting Notes Analysis**: Extract decisions, new risks, and tasks from meeting minutes
- **Email Generation**: Auto-draft RFI, internal alignment, and finance summary emails
- **AI-Powered**: Claude Sonnet for intelligent, structured extraction

## Quick Start

### Prerequisites

- Python 3.11+ with pip
- Node.js 18+
- Anthropic API key

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set your API key
echo "ANTHROPIC_API_KEY=sk-ant-your-key" > .env

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## Demo Flow

1. **Upload a spec PDF** — AI analyzes it in 30-60 seconds
2. **Review bid decision** — Go/No-Go with contingency %
3. **Explore financial exposure** — Total range, cost drivers, category breakdown
4. **Check risk flags** — Filter by severity, expand for details
5. **View requirements** — All extracted obligations in one place
6. **ActionBoard** — Tasks organized by category with owners
7. **Paste meeting notes** — Extract new decisions, risks, tasks
8. **Generate emails** — RFI, internal alignment, finance summary
9. **Send** — Simulate sending with one click

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload PDF and run full analysis |
| GET | `/api/analysis/{id}` | Get stored analysis result |
| GET | `/api/analyses` | List all analyses |
| POST | `/api/meeting-notes` | Analyze meeting notes |
| POST | `/api/generate-emails` | Generate 3 stakeholder emails |
| POST | `/api/send-email` | Simulate sending an email |

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11+ |
| AI | Anthropic Claude API (Sonnet) |
| PDF | pdfplumber |
| State | In-memory (demo mode) |

## Architecture

```
specsentinel/
├── backend/
│   └── app/
│       ├── main.py           # FastAPI app
│       ├── api/routes.py     # All API endpoints
│       ├── core/config.py    # Settings
│       ├── schemas/          # Pydantic models
│       └── services/
│           ├── analysis_pipeline.py  # Orchestration
│           ├── llm_extraction.py     # Claude API (spec + meeting + email)
│           ├── pdf_ingest.py         # PDF text extraction + chunking
│           └── spec_chunking.py      # Division segmentation
├── frontend/
│   ├── app/                  # Next.js App Router
│   │   ├── layout.tsx
│   │   ├── page.tsx          # Main single-page app
│   │   └── globals.css
│   ├── components/           # React components
│   │   ├── BidDecision.tsx
│   │   ├── FinancialSummary.tsx
│   │   ├── RiskFlags.tsx
│   │   ├── Requirements.tsx
│   │   ├── ActionBoard.tsx
│   │   ├── EmailPanel.tsx
│   │   ├── MeetingNotes.tsx
│   │   ├── FileUpload.tsx
│   │   └── TabNav.tsx
│   └── lib/
│       ├── api.ts            # API client
│       └── types.ts          # TypeScript types
└── infra/
    └── docker-compose.yml
```

## License

MIT
