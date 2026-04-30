from fastapi import APIRouter, Response, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.application import ApplicationRead
from app.schemas.job import (
    AnalyzeNewJobRequest,
    AnalyzeNewJobResponse,
    JobCreate,
    JobRead,
    JobUpdate,
    JobWithApplicationRead,
)
from app.services.job_service import JobService

router = APIRouter()


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def create_job(payload: JobCreate, current_user: CurrentUser, db: DbSession) -> JobRead:
    job = JobService(db).create_for_user(user=current_user, payload=payload)
    return JobRead.model_validate(job)


@router.post("/analyze-new", response_model=AnalyzeNewJobResponse, status_code=status.HTTP_201_CREATED)
def analyze_new_job(
    payload: AnalyzeNewJobRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> AnalyzeNewJobResponse:
    job, application = JobService(db).create_and_prepare_analysis(user=current_user, payload=payload)
    return AnalyzeNewJobResponse(job=JobRead.model_validate(job), application=ApplicationRead.model_validate(application))


@router.get("", response_model=list[JobWithApplicationRead])
def list_jobs(current_user: CurrentUser, db: DbSession) -> list[JobWithApplicationRead]:
    jobs = JobService(db).list_for_user(current_user)
    return [JobWithApplicationRead.model_validate(job) for job in jobs]


@router.get("/{job_id}", response_model=JobWithApplicationRead)
def read_job(job_id: int, current_user: CurrentUser, db: DbSession) -> JobWithApplicationRead:
    job = JobService(db).get_for_user(user=current_user, job_id=job_id)
    return JobWithApplicationRead.model_validate(job)


@router.patch("/{job_id}", response_model=JobRead)
def update_job(
    job_id: int,
    payload: JobUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> JobRead:
    job = JobService(db).update_for_user(user=current_user, job_id=job_id, payload=payload)
    return JobRead.model_validate(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: int, current_user: CurrentUser, db: DbSession) -> Response:
    JobService(db).delete_for_user(user=current_user, job_id=job_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{job_id}/analyze")
def analyze_job_placeholder(job_id: int) -> dict[str, str | int]:
    return {"job_id": job_id, "message": "Job analysis business logic is not implemented yet."}


@router.get("/{job_id}/analysis")
def read_job_analysis_placeholder(job_id: int) -> dict[str, str | int]:
    return {"job_id": job_id, "message": "Analysis read business logic is not implemented yet."}
