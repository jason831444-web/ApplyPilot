from datetime import date

from pydantic import BaseModel, Field, field_validator


class ProfileBase(BaseModel):
    resume_text: str = Field(default="", max_length=30000)
    skills: list[str] = Field(default_factory=list, max_length=100)
    projects: list[str] = Field(default_factory=list, max_length=50)
    experience_summary: str = Field(default="", max_length=5000)
    target_roles: list[str] = Field(default_factory=list, max_length=30)
    target_locations: list[str] = Field(default_factory=list, max_length=30)
    graduation_date: date | None = None
    work_authorization_notes: str = Field(default="", max_length=2000)

    @field_validator("resume_text", "experience_summary", "work_authorization_notes", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @field_validator("skills", "projects", "target_roles", "target_locations", mode="before")
    @classmethod
    def normalize_string_list(cls, value: object) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            return []
        items = [str(item).strip() for item in value if str(item).strip()]
        if any(len(item) > 300 for item in items):
            raise ValueError("List items must be 300 characters or fewer.")
        return items


class ProfileUpdate(BaseModel):
    resume_text: str | None = Field(default=None, max_length=30000)
    skills: list[str] | None = Field(default=None, max_length=100)
    projects: list[str] | None = Field(default=None, max_length=50)
    experience_summary: str | None = Field(default=None, max_length=5000)
    target_roles: list[str] | None = Field(default=None, max_length=30)
    target_locations: list[str] | None = Field(default=None, max_length=30)
    graduation_date: date | None = None
    work_authorization_notes: str | None = Field(default=None, max_length=2000)

    @field_validator("resume_text", "experience_summary", "work_authorization_notes", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @field_validator("skills", "projects", "target_roles", "target_locations", mode="before")
    @classmethod
    def normalize_optional_string_list(cls, value: object) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            return []
        items = [str(item).strip() for item in value if str(item).strip()]
        if any(len(item) > 300 for item in items):
            raise ValueError("List items must be 300 characters or fewer.")
        return items


class ProfileRead(ProfileBase):
    id: int
    user_id: int

    model_config = {"from_attributes": True}
