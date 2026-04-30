from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.profile import ProfileRead, ProfileUpdate
from app.services.profile_service import ProfileService

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
