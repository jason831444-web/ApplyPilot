from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models.application import Application
from app.models.job import Job
from app.models.job_analysis import JobAnalysis
from app.schemas.job import JobCreate, JobUpdate


class JobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, *, user_id: int, payload: JobCreate) -> Job:
        job = Job(
            user_id=user_id,
            company_name=payload.company_name,
            job_title=payload.job_title,
            location=payload.location,
            job_description=payload.job_description,
            source_url=str(payload.source_url) if payload.source_url else None,
            source_type=payload.source_type.value,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def list_by_user_id(self, user_id: int) -> list[Job]:
        statement = (
            select(Job)
            .where(Job.user_id == user_id)
            .options(selectinload(Job.application), selectinload(Job.analysis))
            .order_by(Job.created_at.desc(), Job.id.desc())
        )
        return list(self.db.scalars(statement).all())

    def get_by_id_for_user(self, *, job_id: int, user_id: int) -> Job | None:
        statement = (
            select(Job)
            .where(Job.id == job_id, Job.user_id == user_id)
            .options(selectinload(Job.application), selectinload(Job.analysis))
        )
        return self.db.scalar(statement)

    def update(self, *, job: Job, payload: JobUpdate) -> Job:
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "source_url":
                setattr(job, field, str(value) if value else None)
            elif field == "source_type" and value is not None:
                setattr(job, field, value.value)
            else:
                setattr(job, field, value)

        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def delete(self, *, job: Job) -> None:
        self.db.execute(delete(JobAnalysis).where(JobAnalysis.job_id == job.id))
        self.db.execute(delete(Application).where(Application.job_id == job.id, Application.user_id == job.user_id))
        self.db.delete(job)
        self.db.commit()
