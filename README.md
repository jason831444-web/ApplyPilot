# ApplyPilot

ApplyPilot is a full-stack job-fit decision engine for new-grad software engineering candidates.

It is not a generic job tracker. ApplyPilot helps a candidate decide whether a job is worth applying to by analyzing the job description, comparing it against the candidate profile, surfacing sponsorship risk, and turning the result into an explainable recommendation.

## Problem

New-grad candidates often apply to hundreds of roles without knowing which postings are realistic, which require senior experience, which hide sponsorship risk, or which skills are actually missing. Traditional job trackers store status, but they do not help candidates decide where to spend effort.

## Why I Built This

I built ApplyPilot to model the kind of decision support a serious job seeker needs: profile-aware job analysis, new-grad suitability checks, work authorization risk detection, application tracking, and a dashboard that turns search activity into next actions.

## Solution

ApplyPilot lets a user:

- Create a resume/profile with skills, projects, target roles, target locations, graduation date, and work authorization notes
- Paste a job description
- Run deterministic job analysis without paid AI APIs
- Review required skills, preferred skills, seniority signals, sponsorship evidence, missing skills, and match scores
- Get an `Apply`, `Apply with Caution`, `Maybe`, or `Skip` recommendation
- Track the application pipeline
- Review dashboard analytics and next recommended actions

## Core Features

- JWT authentication
- Resume/profile management
- Job creation and detail views
- Deterministic job analysis engine
- New-grad fit scoring
- Sponsorship and work authorization risk detection
- Resume-to-job skill matching
- Application tracking and status editing
- Dashboard analytics
- Demo seed data
- Docker Compose local stack

## Demo Account

After seeding demo data:

- Email: `demo@applypilot.dev`
- Password: `password123`

Seed command:

```bash
docker compose exec backend python -m app.seed
```

The seed is idempotent. Running it multiple times updates the same demo user, jobs, profile, applications, and analyses without duplicating demo records.

## Recommended Demo Flow

1. Log in with the demo account.
2. Open the dashboard.
3. Open a strong-fit job from Best Opportunities.
4. Review the recommendation, scores, evidence, missing skills, and authorization risk.
5. Update the application status or next action.
6. Return to the dashboard and confirm the pipeline insights update.

## Screenshots

Planned portfolio screenshots:

- Dashboard
- Job analysis detail
- Add job flow
- Application pipeline
- Profile editor

## Tech Stack

Frontend:

- Next.js App Router
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

Local development:

- Docker Compose

## Architecture Overview

```text
ApplyPilot
  backend
    app
      api/routes        FastAPI route handlers
      core              settings, database, security, exceptions
      models            SQLAlchemy models
      repositories      database access
      schemas           Pydantic request/response schemas
      services          business logic
      services/analysis deterministic analysis provider
      seed.py           idempotent demo seed script
    alembic             migrations
  frontend
    app                 Next.js App Router pages
    components          UI and feature components
    hooks               auth hook/provider
    lib                 API client, types, format helpers
  docker-compose.yml
```

## Backend Service Structure

- `AuthService`: registration, login, JWT token creation
- `ProfileService`: authenticated profile creation and updates
- `JobService`: job CRUD, analyze-new flow, analysis reruns
- `ApplicationService`: pipeline tracking, ownership checks, status editing
- `DashboardService`: aggregate analytics and recommended next actions
- `JobAnalyzer`: provider coordinator
- `DeterministicRuleBasedProvider`: no-paid-AI analysis provider

## Analysis Pipeline

The deterministic analysis engine:

1. Splits the job description into requirement and preferred sections.
2. Extracts canonical skills from a curated skill dictionary.
3. Detects experience and seniority signals such as `0-2 years`, `junior`, `senior`, and `5+ years`.
4. Detects sponsorship and work authorization language.
5. Compares extracted job skills against the user's profile, resume text, projects, and experience summary.
6. Computes skill, resume, experience, location, authorization, and overall scores.
7. Generates strengths, concerns, evidence, missing skills, next actions, and a recommendation.

The system is provider-based so future `OpenAIAnalysisProvider`, `LocalLLMAnalysisProvider`, or `HybridAnalysisProvider` implementations can be added without rewriting the app flow.

## Scoring And Recommendation Logic

Scores include:

- Required skill score
- Preferred skill score
- Resume match score
- Experience fit score
- Location fit score
- New-grad fit score
- Overall score

Overall score weights:

- Required skills: 35%
- Preferred skills: 15%
- Experience fit: 20%
- Resume match: 15%
- Location fit: 10%
- Authorization adjustment: 5%

Recommendation values:

- `apply`
- `apply_with_caution`
- `maybe`
- `skip`

The recommendation considers overall score, new-grad suitability, missing required skills, authorization evidence, and whether the user's profile suggests OPT, CPT, F-1, visa, or future sponsorship needs.

## Database Models

- `User`: account identity and hashed password
- `Profile`: resume text, skills, projects, targets, graduation date, work authorization notes
- `Job`: job posting data and source metadata
- `Application`: user-specific pipeline status, applied date, notes, next action
- `JobAnalysis`: parsed job data, scores, decision fields, evidence, and metadata

## Local Development Setup

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

Open:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Health check: http://localhost:8000/health

Run migrations:

```bash
docker compose exec backend alembic upgrade head
```

Seed demo data:

```bash
docker compose exec backend python -m app.seed
```

## Full Docker Mode

```bash
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed
```

Verify:

```bash
curl http://localhost:8000/health
```

## Hybrid Development Mode

Use Docker for PostgreSQL:

```bash
docker compose up -d postgres
```

Run backend locally:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Run frontend locally:

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

Root/backend:

```bash
APP_ENV=development
DATABASE_URL=postgresql+psycopg://applypilot:applypilot@localhost:5432/applypilot
SECRET_KEY=change-me-in-development
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

Frontend:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

`BACKEND_CORS_ORIGINS` and `CORS_ORIGINS` are both supported for backend CORS configuration.

## API Quick Reference

Auth:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

Profile:

- `GET /api/profile/me`
- `PUT /api/profile/me`

Jobs:

- `POST /api/jobs`
- `POST /api/jobs/analyze-new`
- `GET /api/jobs`
- `GET /api/jobs/{job_id}`
- `PATCH /api/jobs/{job_id}`
- `DELETE /api/jobs/{job_id}`
- `POST /api/jobs/{job_id}/analyze`
- `GET /api/jobs/{job_id}/analysis`

Applications:

- `POST /api/applications`
- `GET /api/applications`
- `GET /api/applications/{application_id}`
- `PATCH /api/applications/{application_id}`
- `DELETE /api/applications/{application_id}`

Dashboard:

- `GET /api/dashboard/summary`

## Useful Curl Examples

Login:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@applypilot.dev","password":"password123"}'
```

Read dashboard:

```bash
curl http://localhost:8000/api/dashboard/summary \
  -H "Authorization: Bearer $TOKEN"
```

Analyze a new job:

```bash
curl -X POST http://localhost:8000/api/jobs/analyze-new \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Example Corp",
    "job_title": "New Grad Software Engineer",
    "location": "Remote",
    "job_description": "Requirements: 0-2 years, Python, React, SQL. Preferred: Docker, AWS.",
    "source_url": null,
    "source_type": "manual"
  }'
```

Update application status:

```bash
curl -X PATCH http://localhost:8000/api/applications/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"applied","next_action":"Follow up","next_action_date":"2026-05-08"}'
```

## Deployment Guide

Frontend:

- Deploy `frontend` to Vercel.
- Set `NEXT_PUBLIC_API_BASE_URL` to the deployed backend URL.
- Vercel build command: `npm run build`.

Backend:

- Deploy `backend` to Render or Railway.
- Install dependencies from `requirements.txt`.
- Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Database:

- Use Render PostgreSQL, Railway PostgreSQL, or Neon.
- Set `DATABASE_URL` in the backend environment.
- Run migrations after deploy:

```bash
alembic upgrade head
```

Backend deployment environment variables:

```bash
APP_ENV=production
DATABASE_URL=...
SECRET_KEY=...
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=["https://your-frontend.vercel.app"]
```

Optional demo seed after deployment:

```bash
python -m app.seed
```

## Testing Commands

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

Docker health check:

```bash
curl http://localhost:8000/health
```

## Future Improvements

- URL ingestion and scraping
- Chrome extension
- Local LLM or OpenAI provider
- Resume tailoring suggestions
- Recruiter message generator
- Better skill taxonomy and weighting controls
- Team or coach view
- Email/calendar integrations
- Deployment preview seed reset flow

## Resume Bullet Examples

- Built ApplyPilot, a full-stack job-fit decision engine that analyzes software engineering job descriptions, extracts hiring signals, evaluates new-grad suitability, and ranks job fit against a candidate resume.
- Implemented FastAPI and PostgreSQL services for deterministic job parsing, sponsorship risk detection, resume-to-job matching, application tracking, and dashboard analytics.
- Developed a Next.js dashboard that visualizes application status, match scores, missing skills, sponsorship signals, and actionable follow-up insights.
