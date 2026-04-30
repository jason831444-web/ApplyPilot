from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profile import Profile


class ProfileRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_user_id(self, user_id: int) -> Profile | None:
        statement = select(Profile).where(Profile.user_id == user_id)
        return self.db.scalar(statement)

    def create_default(self, user_id: int) -> Profile:
        profile = Profile(
            user_id=user_id,
            resume_text="",
            skills=[],
            projects=[],
            experience_summary="",
            target_roles=[],
            target_locations=[],
            graduation_date=None,
            work_authorization_notes="",
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def save(self, profile: Profile) -> Profile:
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile
