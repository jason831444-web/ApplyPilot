from datetime import date

from pydantic import BaseModel, Field, field_validator


class ProfileBase(BaseModel):
    resume_text: str = ""
    skills: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    experience_summary: str = ""
    target_roles: list[str] = Field(default_factory=list)
    target_locations: list[str] = Field(default_factory=list)
    graduation_date: date | None = None
    work_authorization_notes: str = ""

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
        return [str(item).strip() for item in value if str(item).strip()]


class ProfileUpdate(BaseModel):
    resume_text: str | None = None
    skills: list[str] | None = None
    projects: list[str] | None = None
    experience_summary: str | None = None
    target_roles: list[str] | None = None
    target_locations: list[str] | None = None
    graduation_date: date | None = None
    work_authorization_notes: str | None = None

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
        return [str(item).strip() for item in value if str(item).strip()]


class ProfileRead(ProfileBase):
    id: int
    user_id: int

    model_config = {"from_attributes": True}
