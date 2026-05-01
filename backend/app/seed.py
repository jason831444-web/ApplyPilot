from datetime import date, timedelta

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.application import Application, ApplicationStatus
from app.models.job import Job, JobSourceType
from app.models.profile import Profile
from app.models.user import User
from app.repositories.analyses import AnalysisRepository
from app.services.analysis.analyzer import JobAnalyzer


DEMO_EMAIL = "demo@applypilot.dev"
DEMO_PASSWORD = "password123"


DEMO_PROFILE = {
    "resume_text": (
        "New-grad computer science candidate with full-stack engineering experience across React, Next.js, "
        "TypeScript, Python, FastAPI, PostgreSQL, Docker, REST API design, machine learning, and computer vision. "
        "Built production-minded projects involving OCR document parsing, facility congestion analytics, and "
        "job-fit decision support."
    ),
    "skills": [
        "React",
        "Next.js",
        "TypeScript",
        "Python",
        "FastAPI",
        "PostgreSQL",
        "Docker",
        "Git",
        "REST API",
        "Machine Learning",
        "Computer Vision",
    ],
    "projects": [
        "ApplyPilot job-fit decision engine",
        "DocuParse OCR document parser",
        "Smart Seat facility congestion analysis system",
    ],
    "experience_summary": (
        "New-grad software engineer with strong full-stack project experience, API development, database design, "
        "and applied ML/computer vision coursework."
    ),
    "target_roles": ["Software Engineer", "Full-Stack Engineer", "Backend Engineer"],
    "target_locations": ["New York", "New Jersey", "Remote"],
    "graduation_date": date(2026, 5, 20),
    "work_authorization_notes": "F-1 OPT candidate. May require future H-1B sponsorship.",
}


DEMO_JOBS = [
    {
        "company_name": "MetroSoft",
        "job_title": "Software Engineer I / New Grad",
        "location": "New York",
        "job_description": (
            "Requirements: 0-2 years of experience building web applications. Experience with Python, React, "
            "SQL, PostgreSQL, REST API design, and Git. Preferred qualifications: Docker, AWS, FastAPI. "
            "You will work with mentors to ship customer-facing product features."
        ),
        "status": ApplicationStatus.saved,
        "notes": "Strong new-grad fit. Review company sponsorship policy before applying.",
        "next_action": "Tailor resume and apply",
        "next_action_date": date.today() + timedelta(days=2),
    },
    {
        "company_name": "OpenBridge Health",
        "job_title": "Backend Engineer, Early Career",
        "location": "Remote",
        "job_description": (
            "Minimum qualifications: early career backend engineer with 0-2 years of experience. Build Python "
            "and FastAPI services backed by PostgreSQL, Docker, REST APIs, and Git workflows. "
            "OPT and CPT candidates are welcome, and visa sponsorship is available for qualified candidates."
        ),
        "status": ApplicationStatus.applied,
        "notes": "Sponsorship-friendly language. Application submitted through Greenhouse.",
        "next_action": "Check recruiter response",
        "next_action_date": date.today() + timedelta(days=5),
    },
    {
        "company_name": "ScaleForge",
        "job_title": "Senior Backend Engineer",
        "location": "San Francisco",
        "job_description": (
            "Requirements: Senior backend engineer with 5+ years of production experience owning distributed "
            "systems at scale. Deep Kubernetes, AWS, CI/CD, and platform infrastructure experience required. "
            "Candidates must be authorized to work without current or future sponsorship. No sponsorship available."
        ),
        "status": ApplicationStatus.rejected,
        "notes": "Seeded as a clear skip example due to seniority and sponsorship language.",
        "next_action": None,
        "next_action_date": None,
    },
    {
        "company_name": "Hudson Labs",
        "job_title": "Full-Stack Engineer",
        "location": "Hybrid New York",
        "job_description": (
            "Qualifications: 1-3 years of experience with React, TypeScript, Node.js, SQL, HTML, CSS, and Git. "
            "Preferred: AWS, Kubernetes, CI/CD, and GraphQL. Join a small product team building internal tools."
        ),
        "status": ApplicationStatus.online_assessment,
        "notes": "Good product fit, but cloud/platform gaps should be handled honestly.",
        "next_action": "Complete online assessment",
        "next_action_date": date.today() + timedelta(days=1),
    },
    {
        "company_name": "Garden State Robotics",
        "job_title": "Software Engineer, Platform",
        "location": "New Jersey",
        "job_description": (
            "Requirements: Software engineer with Python, PostgreSQL, Docker, REST API development, Linux, and Git. "
            "Preferred qualifications: machine learning or computer vision exposure. Collaborate on platform tooling "
            "for robotics data systems."
        ),
        "status": ApplicationStatus.recruiter_screen,
        "notes": "High technical match. Authorization risk is unknown, so ask during recruiter screen.",
        "next_action": "Prepare recruiter questions",
        "next_action_date": date.today() + timedelta(days=3),
    },
]


def get_or_create_demo_user(db) -> User:
    user = db.scalar(select(User).where(User.email == DEMO_EMAIL))
    if user is None:
        user = User(email=DEMO_EMAIL, full_name="Demo User", hashed_password=hash_password(DEMO_PASSWORD))
        db.add(user)
    else:
        user.full_name = "Demo User"
        user.hashed_password = hash_password(DEMO_PASSWORD)
    db.commit()
    db.refresh(user)
    return user


def upsert_demo_profile(db, user: User) -> Profile:
    profile = db.scalar(select(Profile).where(Profile.user_id == user.id))
    if profile is None:
        profile = Profile(user_id=user.id)
    for field, value in DEMO_PROFILE.items():
        setattr(profile, field, value)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def upsert_demo_job(db, user: User, job_data: dict) -> Job:
    job = db.scalar(
        select(Job).where(
            Job.user_id == user.id,
            Job.company_name == job_data["company_name"],
            Job.job_title == job_data["job_title"],
        )
    )
    if job is None:
        job = Job(user_id=user.id)

    job.company_name = job_data["company_name"]
    job.job_title = job_data["job_title"]
    job.location = job_data["location"]
    job.job_description = job_data["job_description"]
    job.source_url = None
    job.source_type = JobSourceType.manual
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def upsert_application(db, user: User, job: Job, job_data: dict) -> Application:
    application = db.scalar(select(Application).where(Application.user_id == user.id, Application.job_id == job.id))
    if application is None:
        application = Application(user_id=user.id, job_id=job.id)

    application.status = job_data["status"]
    application.applied_date = date.today() - timedelta(days=2) if job_data["status"] != ApplicationStatus.saved else None
    application.notes = job_data["notes"]
    application.next_action = job_data["next_action"]
    application.next_action_date = job_data["next_action_date"]
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def run_seed() -> None:
    db = SessionLocal()
    try:
        user = get_or_create_demo_user(db)
        profile = upsert_demo_profile(db, user)
        analyzer = JobAnalyzer()
        analyses = AnalysisRepository(db)
        jobs: list[Job] = []
        applications: list[Application] = []

        for job_data in DEMO_JOBS:
            job = upsert_demo_job(db, user, job_data)
            application = upsert_application(db, user, job, job_data)
            result = analyzer.analyze(profile=profile, job=job)
            analyses.upsert(job=job, user=user, result=result)
            jobs.append(job)
            applications.append(application)

        print("ApplyPilot demo data seeded successfully.")
        print(f"Demo credentials: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        print(f"User ID: {user.id}")
        print(f"Jobs: {len(jobs)}")
        print(f"Applications: {len(applications)}")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
