from sqlalchemy.orm import Session

from app.models.application import Application
from app.repositories.applications import ApplicationRepository


class ApplicationService:
    def __init__(self, db: Session) -> None:
        self.applications = ApplicationRepository(db)

    def get_or_create_saved_for_job(self, *, user_id: int, job_id: int) -> Application:
        return self.applications.get_or_create_saved(user_id=user_id, job_id=job_id)
