from fastapi import APIRouter, Response, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.application import (
    ApplicationAnalysisSummary,
    ApplicationCreate,
    ApplicationJobSummary,
    ApplicationRead,
    ApplicationUpdate,
    ApplicationWithJobRead,
    BulkDeleteApplicationsRequest,
    BulkDeleteResponse,
)
from app.services.application_service import ApplicationService

router = APIRouter()


def to_application_with_job(application: object) -> ApplicationWithJobRead:
    base = ApplicationRead.model_validate(application).model_dump()
    analysis = getattr(application.job, "analysis", None)
    return ApplicationWithJobRead(
        **base,
        job=ApplicationJobSummary.model_validate(application.job),
        analysis=ApplicationAnalysisSummary.model_validate(analysis) if analysis is not None else None,
    )


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> ApplicationRead:
    application = ApplicationService(db).create_for_user(user_id=current_user.id, payload=payload)
    return ApplicationRead.model_validate(application)


@router.get("", response_model=list[ApplicationWithJobRead])
def list_applications(current_user: CurrentUser, db: DbSession) -> list[ApplicationWithJobRead]:
    applications = ApplicationService(db).list_for_user(current_user.id)
    return [to_application_with_job(application) for application in applications]


@router.get("/export.csv")
def export_applications_csv(current_user: CurrentUser, db: DbSession) -> Response:
    csv_content = ApplicationService(db).export_csv_for_user(current_user.id)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="applypilot_applications.csv"'},
    )


@router.delete("/bulk", response_model=BulkDeleteResponse)
def bulk_delete_applications(
    payload: BulkDeleteApplicationsRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> BulkDeleteResponse:
    deleted_count = ApplicationService(db).bulk_delete_for_user(
        user_id=current_user.id,
        application_ids=payload.application_ids,
    )
    return BulkDeleteResponse(deleted_count=deleted_count)


@router.get("/{application_id}", response_model=ApplicationWithJobRead)
def read_application(
    application_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> ApplicationWithJobRead:
    application = ApplicationService(db).get_for_user(user_id=current_user.id, application_id=application_id)
    return to_application_with_job(application)


@router.patch("/{application_id}", response_model=ApplicationWithJobRead)
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> ApplicationWithJobRead:
    application = ApplicationService(db).update_for_user(
        user_id=current_user.id,
        application_id=application_id,
        payload=payload,
    )
    return to_application_with_job(application)


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(application_id: int, current_user: CurrentUser, db: DbSession) -> Response:
    ApplicationService(db).delete_for_user(user_id=current_user.id, application_id=application_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
