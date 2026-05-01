from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.job_analysis import JobAnalysis
from app.models.user import User
from app.services.analysis.provider import JobAnalysisResult


class AnalysisRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_job_for_user(self, *, job_id: int, user_id: int) -> JobAnalysis | None:
        statement = select(JobAnalysis).where(JobAnalysis.job_id == job_id, JobAnalysis.user_id == user_id)
        return self.db.scalar(statement)

    def upsert(self, *, job: Job, user: User, result: JobAnalysisResult) -> JobAnalysis:
        analysis = self.get_by_job_for_user(job_id=job.id, user_id=user.id)
        if analysis is None:
            analysis = JobAnalysis(job_id=job.id, user_id=user.id)

        for field, value in asdict(result).items():
            setattr(analysis, field, value)

        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis
