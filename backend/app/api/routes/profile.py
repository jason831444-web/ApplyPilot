from fastapi import APIRouter, File, UploadFile

from app.api.deps import CurrentUser, DbSession
from app.schemas.profile import ProfileRead, ProfileUpdate
from app.schemas.resume_import import ResumeImportRead
from app.services.profile_service import ProfileService
from app.services.resume_import_service import ResumeImportService

router = APIRouter()


@router.get("/me", response_model=ProfileRead)
def read_my_profile(current_user: CurrentUser, db: DbSession) -> ProfileRead:
    profile = ProfileService(db).get_or_create_for_user(current_user)
    return ProfileRead.model_validate(profile)


@router.put("/me", response_model=ProfileRead)
def update_my_profile(
    payload: ProfileUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> ProfileRead:
    profile = ProfileService(db).update_for_user(current_user, payload)
    return ProfileRead.model_validate(profile)


@router.post("/upload-resume", response_model=ResumeImportRead)
async def upload_resume(
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> ResumeImportRead:
    _ = current_user
    return await ResumeImportService().parse_upload(file)
