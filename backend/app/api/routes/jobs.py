from fastapi import APIRouter, Response, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.analysis import JobAnalysisRead
from app.schemas.application import ApplicationRead
from app.schemas.job import (
    AnalyzeNewJobRequest,
    AnalyzeNewJobResponse,
    BulkDeleteJobsRequest,
    BulkDeleteResponse,
    JobCreate,
    JobRead,
    JobUpdate,
    JobWithApplicationRead,
    ReanalyzeAllJobsResponse,
)
from app.schemas.resume_tailoring import ResumeTailoringRead
from app.services.job_service import JobService
from app.services.resume_tailoring_service import ResumeTailoringService

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
    job, application, analysis = JobService(db).create_and_prepare_analysis(user=current_user, payload=payload)
    return AnalyzeNewJobResponse(
        job=JobRead.model_validate(job),
        application=ApplicationRead.model_validate(application),
        analysis=JobAnalysisRead.model_validate(analysis),
    )


@router.get("", response_model=list[JobWithApplicationRead])
def list_jobs(current_user: CurrentUser, db: DbSession) -> list[JobWithApplicationRead]:
    jobs = JobService(db).list_for_user(current_user)
    return [JobWithApplicationRead.model_validate(job) for job in jobs]


@router.delete("/bulk", response_model=BulkDeleteResponse)
def bulk_delete_jobs(
    payload: BulkDeleteJobsRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> BulkDeleteResponse:
    deleted_count = JobService(db).bulk_delete_for_user(user=current_user, job_ids=payload.job_ids)
    return BulkDeleteResponse(deleted_count=deleted_count)


@router.post("/reanalyze-all", response_model=ReanalyzeAllJobsResponse)
def reanalyze_all_jobs(current_user: CurrentUser, db: DbSession) -> ReanalyzeAllJobsResponse:
    reanalyzed_count, failed_count = JobService(db).reanalyze_all_for_user(current_user)
    return ReanalyzeAllJobsResponse(reanalyzed_count=reanalyzed_count, failed_count=failed_count)


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


@router.post("/{job_id}/analyze", response_model=JobAnalysisRead)
def analyze_job(job_id: int, current_user: CurrentUser, db: DbSession) -> JobAnalysisRead:
    analysis = JobService(db).analyze_for_user(user=current_user, job_id=job_id)
    return JobAnalysisRead.model_validate(analysis)


@router.get("/{job_id}/analysis", response_model=JobAnalysisRead)
def read_job_analysis(job_id: int, current_user: CurrentUser, db: DbSession) -> JobAnalysisRead:
    analysis = JobService(db).get_analysis_for_user(user=current_user, job_id=job_id)
    return JobAnalysisRead.model_validate(analysis)


@router.get("/{job_id}/resume-tailoring", response_model=ResumeTailoringRead)
def read_resume_tailoring(job_id: int, current_user: CurrentUser, db: DbSession) -> ResumeTailoringRead:
    return ResumeTailoringService(db).generate_for_user(user=current_user, job_id=job_id)
