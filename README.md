# SpecSentinel

**AI-powered spec-checker for commercial HVAC/Plumbing/Electrical contractors.**

SpecSentinel ingests project manuals (PDF) and generates structured requirements extraction and comprehensive bid risk reports, helping contractors quickly identify key requirements and potential risks in bid documents.

## Features

- **Multi-tenant Architecture**: Organizations with users, projects, and documents
- **PDF Analysis**: Extract text from project specification PDFs using pdfplumber
- **AI-Powered Extraction**: Claude API integration for intelligent spec analysis
- **Comprehensive Risk Reports**:
  - Project summary (name, location, type, scope, schedule)
  - Risk flags with severity, spec location, impact, and recommended actions
  - Bid cost impact estimates ($, $$, $$$)
  - Estimator checklist (confirm before pricing, include in bid cost, clarify via RFI)
- **Structured Extraction**: Identify insurance, bonding, warranty, liquidated damages, testing, commissioning, and submittal requirements
- **Division-Specific Analysis**: Extract Division 22 (Plumbing), 23 (HVAC), and 26 (Electrical) requirements
- **Subscription Management**: Free/Pro/Enterprise tiers with usage limits

## Architecture

```
specsentinel/
├── backend/          # FastAPI + SQLAlchemy + Alembic
│   ├── app/
│   │   ├── api/      # REST API endpoints
│   │   ├── core/     # Config, security
│   │   ├── db/       # Database setup
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic schemas
│   │   └── services/ # Business logic (PDF, extraction, risk, LLM)
│   ├── alembic/      # Database migrations
│   └── tests/        # Pytest tests
├── frontend/         # Next.js + React + TypeScript + Tailwind
│   ├── components/   # React components
│   ├── lib/          # API client, auth, types
│   ├── pages/        # Next.js pages
│   └── styles/       # Global CSS
└── infra/            # Docker configuration
```

## Quick Start with Docker

The easiest way to run SpecSentinel locally:

```bash
# Clone and navigate to project
cd specsentinel

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local

# Edit backend/.env and add your Anthropic API key
# ANTHROPIC_API_KEY=sk-ant-xxx

# Start all services
cd infra
docker-compose up --build
```

Services will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs

## Manual Setup (Development)

### Prerequisites

- Python 3.11+ (tested with 3.13)
- Node.js 18+
- PostgreSQL 15+

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL, SECRET_KEY, and ANTHROPIC_API_KEY

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.local.example .env.local

# Start development server
npm run dev
```

## Environment Variables

### Backend (`backend/.env`)

```env
# Database (psycopg3 driver)
DATABASE_URL=postgresql+psycopg://specsentinel:specsentinel@localhost:5432/specsentinel

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# File Storage
FILE_STORAGE_PATH=./uploads

# Anthropic API (for AI-powered extraction)
ANTHROPIC_API_KEY=sk-ant-xxx
USE_LLM_EXTRACTION=true

# Environment
ENV=dev
```

### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Usage

### 1. Register and Login

1. Navigate to http://localhost:3000
2. Click "Get Started" to register
3. Enter your company name, name, email, and password
4. You'll be redirected to the dashboard

### 2. Create a Project

1. Click "New Project" on the dashboard
2. Enter project name, client name, and bid due date
3. Click "Create Project"

### 3. Upload a PDF

1. Click on your project to open it
2. Drag and drop a PDF or click to upload
3. Watch the progress indicator as AI analyzes your document:
   - Uploading document...
   - Extracting text from PDF...
   - Analyzing spec requirements...
   - Identifying risk flags...
   - Generating bid report...

### 4. Review Analysis

The analysis will show:
- **Project Summary**: Name, location, type, scope, schedule constraints
- **Risk Assessment**: Overall risk level and detailed risk flags with:
  - Severity (Low/Medium/High/Critical)
  - Bid cost impact ($, $$, $$$)
  - Spec location and quotes
  - Impact analysis
  - Recommended actions
- **Estimator Checklist**:
  - Must confirm before pricing
  - Include in bid cost
  - Clarify via RFI
- **Key Requirements**: Insurance, bonding, warranty, LDs, testing, commissioning, submittals
- **Division Requirements**: Division 22/23/26 specific extractions

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register organization + user
- `POST /api/v1/auth/login` - Login (OAuth2 form)
- `POST /api/v1/auth/login/json` - Login (JSON body)
- `GET /api/v1/auth/me` - Get current user

### Projects
- `GET /api/v1/projects/` - List projects
- `POST /api/v1/projects/` - Create project
- `GET /api/v1/projects/{id}` - Get project
- `PATCH /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project

### Documents
- `POST /api/v1/documents/upload` - Upload PDF (multipart/form-data)
- `GET /api/v1/documents/{id}` - Get document
- `DELETE /api/v1/documents/{id}` - Delete document

### Analysis
- `GET /api/v1/analysis/{document_id}` - Get analysis for document
- `GET /api/v1/analysis/project/{project_id}` - Get all analyses for project

### Billing
- `GET /api/v1/billing/plans` - List subscription plans
- `GET /api/v1/billing/subscription` - Get current subscription
- `GET /api/v1/billing/usage` - Get usage statistics
- `POST /api/v1/billing/checkout` - Create checkout session (TODO: Stripe)

## Running Tests

```bash
cd backend
pytest
```

## TODOs for Production

### Stripe Integration
- [ ] Add Stripe customer creation
- [ ] Implement checkout session creation
- [ ] Add webhook handling for subscription events
- [ ] Handle payment failures and subscription cancellation

### Security & Infrastructure
- [ ] Add rate limiting
- [ ] Implement proper RBAC (role-based access control)
- [ ] Add email verification
- [ ] Set up S3/GCS for file storage
- [ ] Add Redis for caching and background jobs
- [ ] Set up Celery for async document processing

### Features
- [ ] Team member invitations
- [ ] Document comparison
- [ ] Export reports to PDF/Word
- [ ] Email notifications for bid deadlines
- [ ] Audit logging
- [ ] RAG pipeline with embeddings for semantic search

## Tech Stack

### Backend
- FastAPI - Web framework
- SQLAlchemy 2.x - ORM
- Alembic - Database migrations
- PostgreSQL + psycopg3 - Database
- pdfplumber - PDF text extraction
- Anthropic Claude API - AI-powered extraction
- Pydantic - Data validation
- python-jose - JWT handling
- bcrypt - Password hashing

### Frontend
- Next.js 14 - React framework
- TypeScript - Type safety
- Tailwind CSS - Styling
- Axios - HTTP client

## License

MIT License - see LICENSE file for details.
