from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.application import Application, ApplicationStatus
from app.models.job import Job
from app.schemas.application import ApplicationCreate, ApplicationUpdate


class ApplicationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_user_and_job(self, *, user_id: int, job_id: int) -> Application | None:
        statement = select(Application).where(Application.user_id == user_id, Application.job_id == job_id)
        return self.db.scalar(statement)

    def list_by_user_id(self, user_id: int) -> list[Application]:
        statement = (
            select(Application)
            .where(Application.user_id == user_id)
            .options(selectinload(Application.job).selectinload(Job.analysis))
            .order_by(Application.updated_at.desc(), Application.id.desc())
        )
        return list(self.db.scalars(statement).all())

    def get_by_id_for_user(self, *, application_id: int, user_id: int) -> Application | None:
        statement = (
            select(Application)
            .where(Application.id == application_id, Application.user_id == user_id)
            .options(selectinload(Application.job).selectinload(Job.analysis))
        )
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

    def create(self, *, user_id: int, payload: ApplicationCreate) -> Application:
        application = Application(
            user_id=user_id,
            job_id=payload.job_id,
            status=ApplicationStatus(payload.status.value),
            applied_date=payload.applied_date,
            notes=payload.notes,
            next_action=payload.next_action,
            next_action_date=payload.next_action_date,
        )
        self.db.add(application)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            existing_application = self.get_by_user_and_job(user_id=user_id, job_id=payload.job_id)
            if existing_application is None:
                raise
            return existing_application

        self.db.refresh(application)
        return application

    def update(self, *, application: Application, payload: ApplicationUpdate) -> Application:
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "status" and value is not None:
                setattr(application, field, ApplicationStatus(value.value))
            else:
                setattr(application, field, value)

        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        return application

    def save(self, application: Application) -> Application:
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        return application

    def delete(self, application: Application) -> None:
        self.db.delete(application)
        self.db.commit()
