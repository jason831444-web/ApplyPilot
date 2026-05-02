from datetime import date
import csv
from io import StringIO

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.application import Application, ApplicationStatus
from app.repositories.applications import ApplicationRepository
from app.repositories.jobs import JobRepository
from app.schemas.application import ApplicationCreate, ApplicationUpdate


class ApplicationService:
    def __init__(self, db: Session) -> None:
        self.applications = ApplicationRepository(db)
        self.jobs = JobRepository(db)

    def get_or_create_saved_for_job(self, *, user_id: int, job_id: int) -> Application:
        return self.applications.get_or_create_saved(user_id=user_id, job_id=job_id)

    def create_for_user(self, *, user_id: int, payload: ApplicationCreate) -> Application:
        job = self.jobs.get_by_id_for_user(job_id=payload.job_id, user_id=user_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

        existing_application = self.applications.get_by_user_and_job(user_id=user_id, job_id=payload.job_id)
        if existing_application is not None:
            return existing_application

        if payload.status.value == ApplicationStatus.applied.value and payload.applied_date is None:
            payload = payload.model_copy(update={"applied_date": date.today()})

        return self.applications.create(user_id=user_id, payload=payload)

    def list_for_user(self, user_id: int) -> list[Application]:
        return self.applications.list_by_user_id(user_id)

    def get_for_user(self, *, user_id: int, application_id: int) -> Application:
        application = self.applications.get_by_id_for_user(application_id=application_id, user_id=user_id)
        if application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
        return application

    def update_for_user(self, *, user_id: int, application_id: int, payload: ApplicationUpdate) -> Application:
        application = self.get_for_user(user_id=user_id, application_id=application_id)
        updated_application = self.applications.update(application=application, payload=payload)

        if updated_application.status == ApplicationStatus.applied and updated_application.applied_date is None:
            updated_application.applied_date = date.today()
            updated_application = self.applications.save(updated_application)

        return updated_application

    def delete_for_user(self, *, user_id: int, application_id: int) -> None:
        application = self.get_for_user(user_id=user_id, application_id=application_id)
        self.applications.delete(application)

    def bulk_delete_for_user(self, *, user_id: int, application_ids: list[int]) -> int:
        return self.applications.bulk_delete_for_user(user_id=user_id, application_ids=application_ids)

    def export_csv_for_user(self, user_id: int) -> str:
        output = StringIO()
        fieldnames = [
            "application_id",
            "status",
            "applied_date",
            "next_action",
            "next_action_date",
            "notes",
            "job_id",
            "company_name",
            "job_title",
            "location",
            "source_url",
            "recommendation",
            "overall_score",
            "new_grad_fit_label",
            "authorization_risk",
            "created_at",
            "updated_at",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for application in self.list_for_user(user_id):
            analysis = getattr(application.job, "analysis", None)
            writer.writerow(
                {
                    "application_id": application.id,
                    "status": self._value(application.status),
                    "applied_date": application.applied_date or "",
                    "next_action": application.next_action or "",
                    "next_action_date": application.next_action_date or "",
                    "notes": application.notes or "",
                    "job_id": application.job_id,
                    "company_name": application.job.company_name,
                    "job_title": application.job.job_title,
                    "location": application.job.location or "",
                    "source_url": application.job.source_url or "",
                    "recommendation": self._value(getattr(analysis, "recommendation", "")) if analysis else "",
                    "overall_score": getattr(analysis, "overall_score", "") if analysis else "",
                    "new_grad_fit_label": self._value(getattr(analysis, "new_grad_fit_label", "")) if analysis else "",
                    "authorization_risk": self._value(getattr(analysis, "authorization_risk", "")) if analysis else "",
                    "created_at": application.created_at.isoformat() if application.created_at else "",
                    "updated_at": application.updated_at.isoformat() if application.updated_at else "",
                }
            )

        return output.getvalue()

    def _value(self, value: object) -> str:
        return str(getattr(value, "value", value))
