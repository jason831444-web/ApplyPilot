from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.models.user import User
from app.repositories.profiles import ProfileRepository
from app.schemas.profile import ProfileUpdate


class ProfileService:
    def __init__(self, db: Session) -> None:
        self.profiles = ProfileRepository(db)

    def get_or_create_for_user(self, user: User) -> Profile:
        profile = self.profiles.get_by_user_id(user.id)
        if profile is not None:
            return profile
        return self.profiles.create_default(user.id)

    def update_for_user(self, user: User, payload: ProfileUpdate) -> Profile:
        profile = self.get_or_create_for_user(user)
        update_data = payload.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(profile, field, value)

        return self.profiles.save(profile)
