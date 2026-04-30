from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.user import User
from app.repositories.jobs import JobRepository
from app.schemas.job import AnalyzeNewJobRequest, JobCreate, JobUpdate
from app.services.application_service import ApplicationService


class JobService:
    def __init__(self, db: Session) -> None:
        self.jobs = JobRepository(db)
        self.applications = ApplicationService(db)

    def create_for_user(self, *, user: User, payload: JobCreate) -> Job:
        return self.jobs.create(user_id=user.id, payload=payload)

    def create_and_prepare_analysis(self, *, user: User, payload: AnalyzeNewJobRequest) -> tuple[Job, object]:
        job = self.jobs.create(user_id=user.id, payload=payload)
        application = self.applications.get_or_create_saved_for_job(user_id=user.id, job_id=job.id)
        # TODO: Step 6 will call the deterministic analysis engine here.
        return job, application

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
