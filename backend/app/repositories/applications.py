from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.application import Application, ApplicationStatus


class ApplicationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_user_and_job(self, *, user_id: int, job_id: int) -> Application | None:
        statement = select(Application).where(Application.user_id == user_id, Application.job_id == job_id)
        return self.db.scalar(statement)

    def get_or_create_saved(self, *, user_id: int, job_id: int) -> Application:
        existing_application = self.get_by_user_and_job(user_id=user_id, job_id=job_id)
        if existing_application is not None:
            return existing_application

        application = Application(user_id=user_id, job_id=job_id, status=ApplicationStatus.saved)
        self.db.add(application)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            existing_application = self.get_by_user_and_job(user_id=user_id, job_id=job_id)
            if existing_application is None:
                raise
            return existing_application

        self.db.refresh(application)
        return application
