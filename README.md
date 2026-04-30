# ApplyPilot

ApplyPilot is a production-minded MVP for new-grad software engineering candidates. The product is a job-fit decision engine, not a generic job tracker.

This repository currently contains the initial monorepo scaffold:

- `backend`: FastAPI, SQLAlchemy, Alembic, PostgreSQL configuration
- `frontend`: Next.js App Router, TypeScript, Tailwind CSS
- `docker-compose.yml`: local PostgreSQL, backend, and frontend services

## Local Development

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Health check: http://localhost:8000/health

Verify the backend health check:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Auth API

Auth endpoints:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

Register a user:

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Ada Lovelace",
    "email": "ada@example.com",
    "password": "password123"
  }'
```

Login:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ada@example.com",
    "password": "password123"
  }'
```

Call `/me` with the returned token:

```bash
TOKEN="paste_access_token_here"

curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

## Profile API

Profile data powers the later job matching engine. It stores resume text, skills, projects, target roles, target locations, graduation date, and work authorization notes for the authenticated user.

Profile endpoints:

- `GET /api/profile/me`
- `PUT /api/profile/me`

Get or create your profile:

```bash
curl http://localhost:8000/api/profile/me \
  -H "Authorization: Bearer $TOKEN"
```

Update your profile:

```bash
curl -X PUT http://localhost:8000/api/profile/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Paste resume text here",
    "skills": ["Python", "FastAPI", "React", "PostgreSQL"],
    "projects": ["ApplyPilot - job-fit decision engine"],
    "experience_summary": "New-grad software engineer with full-stack project experience.",
    "target_roles": ["Software Engineer", "Backend Engineer"],
    "target_locations": ["New York", "Remote"],
    "graduation_date": "2026-05-15",
    "work_authorization_notes": "F-1 OPT eligible; may need sponsorship later."
  }'
```

## Jobs API

Real analysis is intentionally deferred to the next implementation step. For now, jobs can be saved and `analyze-new` prepares the workflow by creating a default `saved` application record.

Job endpoints:

- `POST /api/jobs`
- `POST /api/jobs/analyze-new`
- `GET /api/jobs`
- `GET /api/jobs/{job_id}`
- `PATCH /api/jobs/{job_id}`
- `DELETE /api/jobs/{job_id}`

Create a job without an application record:

```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Example Corp",
    "job_title": "New Grad Software Engineer",
    "location": "New York, NY",
    "job_description": "Paste the job description here.",
    "source_url": null,
    "source_type": "manual"
  }'
```

Create a job and default saved application:

```bash
curl -X POST http://localhost:8000/api/jobs/analyze-new \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Example Corp",
    "job_title": "New Grad Software Engineer",
    "location": "New York, NY",
    "job_description": "Paste the job description here.",
    "source_url": "https://example.com/jobs/new-grad-swe",
    "source_type": "url"
  }'
```

List saved jobs:

```bash
curl http://localhost:8000/api/jobs \
  -H "Authorization: Bearer $TOKEN"
```
