# ApplyPilot

ApplyPilot is a full-stack New-Grad Job-Fit Engine that helps candidates evaluate job postings against their profile using deterministic rules instead of relying on an LLM for core matching.

It turns a pasted job description and a structured candidate profile into explainable scores, missing-skill feedback, work authorization risk, resume tailoring suggestions, application tracking, and dashboard analytics.

- Compare jobs against resume text, skills, projects, target roles, locations, graduation date, and work authorization notes.
- Score postings across new-grad fit, skill match, experience fit, location fit, resume match, and authorization risk.
- Surface actionable outputs: recommendation, missing skills, evidence, next actions, resume tailoring, and portfolio-level analytics.
- Re-run all saved analyses after profile changes so stored scores and dashboards stay consistent with the latest profile.

## Live Demo

Frontend: https://applypilot-web.vercel.app

Backend health check: https://applypilot-backend-nrtx.onrender.com/health

Demo account:

- Email: `demo@applypilot.dev`
- Password: `password123`

The backend is hosted on a free Render instance, so the first request may take several seconds if the server is sleeping.

## Problem

New-grad candidates often apply to large numbers of roles without a structured way to decide which postings are realistic. Job descriptions mix required skills, preferred qualifications, seniority signals, sponsorship language, and vague responsibilities in inconsistent formats.

This creates three practical problems:

- Search effort is inefficient because candidates cannot quickly separate strong-fit roles from low-probability roles.
- Traditional application trackers store status but do not evaluate whether a job matches the candidate's profile.
- Resume mismatch is hard to diagnose because candidates may not know which skills or signals a posting expects.

## Solution

ApplyPilot provides a deterministic job-fit engine built around a structured candidate profile and explainable scoring rules.

The system parses job descriptions, extracts hiring signals, compares them against profile data, and stores an analysis record for each job. Instead of producing a black-box response, it returns concrete outputs:

- Multi-factor scores for skill match, resume match, new-grad fit, experience fit, location fit, and authorization risk.
- Missing required and preferred skills with confidence-aware messaging.
- Evidence-backed recommendations: `apply`, `apply_with_caution`, `maybe`, or `skip`.
- Deterministic resume tailoring suggestions based on the saved job analysis and current profile.

## Core Features

### Profile System

- Stores resume text plus structured fields for skills, projects, experience summary, target roles, target locations, graduation date, and work authorization notes.
- Uses work authorization notes when evaluating sponsorship or visa-related risk in job descriptions.
- Provides a single profile source of truth for job scoring, dashboard analytics, and resume tailoring.

### Resume Import

- Imports text-based PDF resumes without OCR and without external AI APIs.
- Extracts resume text and section-aware suggestions for skills, projects, and experience summary.
- Keeps import suggestions reviewable before saving them into the profile.

### Job Analysis Engine

ApplyPilot analyzes jobs through deterministic rules and scoring logic. Scores include:

- Required skills
- Preferred skills
- Resume match
- Experience fit
- Location fit
- New-grad fit
- Authorization risk

The engine extracts structured requirements, seniority signals, domain signals, sponsorship language, and evidence snippets from the job posting. It then compares those signals against the user's profile and stores the resulting analysis.

### Missing Skills Detection

- Detects missing required and preferred skills by comparing extracted job skills against profile text, structured skills, projects, and experience summary.
- Uses confidence-aware messaging when job postings contain sparse or ambiguous technical requirements.
- Avoids presenting sparse postings as if they have no missing skills simply because little structured signal was detected.

### Resume Tailoring

- Generates deterministic suggestions based on the current profile, job posting, and stored analysis.
- Highlights skills to emphasize, keywords to add, project angles, tailored summary guidance, and cautions.
- Avoids suggesting the user claim missing skills as existing experience.

### Application Tracking

- Tracks application status across the job-search pipeline.
- Supports notes, applied dates, next actions, and next action dates.
- Keeps application records scoped to the authenticated user.

### Dashboard & Analytics

- Aggregates application and analysis data into dashboard summaries.
- Surfaces status distribution, recommendation breakdowns, missing-skill trends, upcoming follow-ups, and best opportunities.
- Updates automatically from stored analysis rows after jobs are reanalyzed.

### CSV Export

- Exports applications with related job and analysis data.
- Includes analysis columns such as recommendation, overall score, new-grad fit label, and authorization risk.

### Reanalysis Flow

- Profile changes can affect existing job scores, missing skills, dashboard analytics, and resume tailoring.
- After a successful profile save, the UI shows a callout prompting the user to re-run saved analyses.
- The `Re-run All Analyses` action recomputes all jobs owned by the current user and updates or creates analysis rows.
- This keeps the system consistent without automatically running a potentially expensive operation on every profile save.

## System Architecture

ApplyPilot is organized as a three-tier full-stack application:

- Frontend: Next.js App Router, React, TypeScript, Tailwind CSS.
- Backend: FastAPI with service and repository layers.
- Database: PostgreSQL managed through SQLAlchemy models and Alembic migrations.

High-level flow:

```text
User Profile -> Job Input -> Analysis Engine -> Stored Analysis -> UI
```

Detailed flow:

1. The user creates or updates a profile with resume text and structured fields.
2. The user saves or analyzes a job posting.
3. The FastAPI backend runs the deterministic analysis engine.
4. The backend upserts a `JobAnalysis` row linked to the authenticated user's job.
5. The frontend renders scores, evidence, missing skills, recommendations, tailoring suggestions, and dashboard analytics from stored data.

## Backend Structure

```text
backend/app
  api/routes        FastAPI route handlers and request boundaries
  core              settings, database, security, shared exceptions
  models            SQLAlchemy models
  repositories      database access and persistence operations
  schemas           Pydantic request and response schemas
  services          business logic and workflow orchestration
  services/analysis deterministic analysis provider and scoring logic
```

Important services:

- `ProfileService`: profile creation and updates.
- `JobService`: job CRUD, analyze-new flow, single-job reanalysis, and reanalyze-all flow.
- `ApplicationService`: pipeline tracking and ownership checks.
- `DashboardService`: aggregate analytics.
- `ResumeTailoringService`: deterministic tailoring suggestions.
- `JobAnalyzer`: provider coordinator for analysis.
- `DeterministicRuleBasedProvider`: no-LLM core analysis provider.

## Key Engineering Decisions

### Deterministic Analysis Instead Of LLM Dependency

Core matching uses deterministic parsing and scoring rather than an external LLM. This keeps analysis explainable, testable, cheaper to run, and reliable in local development or demo environments.

### Confidence-Aware Parsing

The engine distinguishes between strong extracted requirements and sparse job descriptions. This prevents misleading outputs such as treating a low-signal posting as a complete skill match.

### Section-Aware Resume Extraction

Resume import uses section-aware parsing to identify technical skills, projects, and summary material from text-based PDFs. The import flow suggests profile changes but leaves final control with the user.

### Layered Backend Design

Routes handle API boundaries, services hold business workflows, and repositories own database access. This keeps authentication, ownership checks, scoring, and persistence easier to test independently.

### Upsert-Based Analysis Storage

Job analysis is stored with upsert behavior. Reanalysis updates existing `JobAnalysis` rows and creates missing rows, which lets dashboards, job views, resume tailoring, and CSV exports all read from the same durable analysis source.

## Example Flow: Profile Change Reanalysis

1. A user updates their profile after adding new skills from a resume PDF.
2. The user saves the profile.
3. ApplyPilot shows: `Your profile changed. Re-run analysis for all saved jobs to update scores and recommendations.`
4. The user clicks `Re-run All Analyses`.
5. The backend processes only jobs owned by that user through `POST /api/jobs/reanalyze-all`.
6. Existing analyses are updated and missing analyses are created.
7. Dashboard analytics, job scores, missing skills, and resume tailoring reflect the updated profile.

## Screenshots

Portfolio screenshots can be added here:

### Dashboard

![Dashboard screenshot placeholder](docs/screenshots/dashboard.png)

### Job Analysis View

![Job analysis screenshot placeholder](docs/screenshots/job-analysis.png)

### Profile Page

![Profile page screenshot placeholder](docs/screenshots/profile.png)

## Tech Stack

Frontend:

- Next.js App Router
- React
- TypeScript
- Tailwind CSS
- Recharts

Backend:

- FastAPI
- Python
- SQLAlchemy
- Alembic
- PostgreSQL
- JWT authentication
- Passlib bcrypt password hashing

Infrastructure:

- Docker
- Docker Compose
- Render backend deployment
- Vercel frontend deployment
- Neon PostgreSQL for hosted database

## Setup Instructions

### Docker Setup

Copy environment examples if desired:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

Start the full stack:

```bash
docker compose up --build
```

Run database migrations:

```bash
docker compose exec backend alembic upgrade head
```

Seed demo data:

```bash
docker compose exec backend python -m app.seed
```

Open:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Health check: http://localhost:8000/health

### Backend Run

Use Docker for PostgreSQL:

```bash
docker compose up -d postgres
```

Run the backend locally:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend Run

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

Backend:

```bash
APP_ENV=development
DATABASE_URL=postgresql+psycopg://applypilot:applypilot@localhost:5432/applypilot
SECRET_KEY=replace-with-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Frontend:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
```

`BACKEND_CORS_ORIGINS` and `CORS_ORIGINS` are both supported for backend CORS configuration. They may be JSON arrays or comma-separated strings.

## API Quick Reference

Auth:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

Profile:

- `GET /api/profile/me`
- `PUT /api/profile/me`
- `POST /api/profile/upload-resume`

Jobs:

- `POST /api/jobs`
- `POST /api/jobs/analyze-new`
- `GET /api/jobs`
- `GET /api/jobs/{job_id}`
- `PATCH /api/jobs/{job_id}`
- `DELETE /api/jobs/{job_id}`
- `POST /api/jobs/{job_id}/analyze`
- `GET /api/jobs/{job_id}/analysis`
- `GET /api/jobs/{job_id}/resume-tailoring`
- `POST /api/jobs/reanalyze-all`

Applications:

- `POST /api/applications`
- `GET /api/applications`
- `GET /api/applications/{application_id}`
- `PATCH /api/applications/{application_id}`
- `DELETE /api/applications/{application_id}`
- `GET /api/applications/export.csv`

Dashboard:

- `GET /api/dashboard/summary`

## Testing

Backend:

```bash
python -m compileall backend/app
PYTHONPATH=backend python -m pytest backend/app/tests
```

Frontend:

```bash
cd frontend
npm run build
```

Whitespace check:

```bash
git diff --check
```

## Security Notes

- Product routes are authenticated and scoped to the current user.
- Job reanalysis only processes jobs owned by the authenticated user.
- User-provided job and profile text is rendered as plain text.
- JWTs are stored in `localStorage` for MVP simplicity.
- For production hardening, migrate auth to `httpOnly`, `Secure`, `SameSite` cookies and add CSRF protection where appropriate.
- Keep real `.env` files out of version control.

## Deployment Notes

Current hosted architecture:

- Frontend: Vercel
- Backend: Render Web Service
- Database: Neon PostgreSQL

Render backend start command:

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Vercel frontend environment variable:

```bash
NEXT_PUBLIC_API_BASE_URL=https://applypilot-backend-nrtx.onrender.com/api
```

## Future Improvements

- Background job queue for large reanalysis workloads.
- URL-based job ingestion with HTML parsing.
- Better skill ontology, aliases, and weighting controls.
- Resume versioning and comparison across tailored variants.
- Real-time updates after long-running analysis operations.
- Stronger production auth with secure cookie storage.
- Deployment preview seed reset flow.
