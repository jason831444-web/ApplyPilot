from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.job_analysis import JobAnalysis
from app.models.user import User
from app.repositories.analyses import AnalysisRepository
from app.repositories.jobs import JobRepository
from app.schemas.job import AnalyzeNewJobRequest, JobCreate, JobUpdate
from app.services.analysis.analyzer import JobAnalyzer
from app.services.application_service import ApplicationService
from app.services.profile_service import ProfileService


class JobService:
    def __init__(self, db: Session) -> None:
        self.jobs = JobRepository(db)
        self.applications = ApplicationService(db)
        self.profiles = ProfileService(db)
        self.analyses = AnalysisRepository(db)
        self.analyzer = JobAnalyzer()

    def create_for_user(self, *, user: User, payload: JobCreate) -> Job:
        return self.jobs.create(user_id=user.id, payload=payload)

    def create_and_prepare_analysis(self, *, user: User, payload: AnalyzeNewJobRequest) -> tuple[Job, object, JobAnalysis]:
        job = self.jobs.create(user_id=user.id, payload=payload)
        application = self.applications.get_or_create_saved_for_job(user_id=user.id, job_id=job.id)
        analysis = self._run_analysis(user=user, job=job)
        return job, application, analysis

    def list_for_user(self, user: User) -> list[Job]:
        return self.jobs.list_by_user_id(user.id)

    def get_for_user(self, *, user: User, job_id: int) -> Job:
        job = self.jobs.get_by_id_for_user(job_id=job_id, user_id=user.id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
        return job

    def update_for_user(self, *, user: User, job_id: int, payload: JobUpdate) -> Job:
        job = self.get_for_user(user=user, job_id=job_id)
        return self.jobs.update(job=job, payload=payload)

    def delete_for_user(self, *, user: User, job_id: int) -> None:
        job = self.get_for_user(user=user, job_id=job_id)
        self.jobs.delete(job=job)

    def analyze_for_user(self, *, user: User, job_id: int) -> JobAnalysis:
        job = self.get_for_user(user=user, job_id=job_id)
        return self._run_analysis(user=user, job=job)

    def get_analysis_for_user(self, *, user: User, job_id: int) -> JobAnalysis:
        self.get_for_user(user=user, job_id=job_id)
        analysis = self.analyses.get_by_job_for_user(job_id=job_id, user_id=user.id)
        if analysis is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found.")
        return analysis

    def _run_analysis(self, *, user: User, job: Job) -> JobAnalysis:
        profile = self.profiles.get_or_create_for_user(user)
        result = self.analyzer.analyze(profile=profile, job=job)
        return self.analyses.upsert(job=job, user=user, result=result)
