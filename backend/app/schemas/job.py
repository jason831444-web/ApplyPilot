from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, HttpUrl, field_validator

from app.schemas.analysis import JobAnalysisRead
from app.schemas.application import ApplicationRead


class JobSourceType(str, Enum):
    manual = "manual"
    url = "url"


class JobBase(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    job_title: str = Field(min_length=1, max_length=255)
    location: str = Field(default="", max_length=255)
    job_description: str = Field(min_length=20, max_length=50000)
    source_url: HttpUrl | None = Field(default=None, max_length=2000)
    source_type: JobSourceType = JobSourceType.manual

    @field_validator("company_name", "job_title", "location", "job_description", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @field_validator("source_url", mode="before")
    @classmethod
    def normalize_source_url(cls, value: object) -> object:
        if value is None or str(value).strip() == "":
            return None
        return value


class JobCreate(JobBase):
    pass


class AnalyzeNewJobRequest(JobCreate):
    pass


class JobUpdate(BaseModel):
    company_name: str | None = Field(default=None, min_length=1, max_length=255)
    job_title: str | None = Field(default=None, min_length=1, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    job_description: str | None = Field(default=None, min_length=20, max_length=50000)
    source_url: HttpUrl | None = Field(default=None, max_length=2000)
    source_type: JobSourceType | None = None

    @field_validator("company_name", "job_title", "location", "job_description", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: object) -> str | None:
        if value is None:
            return None
        return str(value).strip()

    @field_validator("source_url", mode="before")
    @classmethod
    def normalize_optional_source_url(cls, value: object) -> object:
        if value is None or str(value).strip() == "":
            return None
        return value


class JobRead(JobBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobWithApplicationRead(JobRead):
    application: ApplicationRead | None = None
    analysis: JobAnalysisRead | None = None


class AnalyzeNewJobResponse(BaseModel):
    job: JobRead
    application: ApplicationRead
    analysis: JobAnalysisRead


PositiveId = Annotated[int, Field(gt=0)]


class BulkDeleteJobsRequest(BaseModel):
    job_ids: list[PositiveId] = Field(min_length=1, max_length=100)


class BulkDeleteResponse(BaseModel):
    deleted_count: int = Field(ge=0)


class ReanalyzeAllJobsResponse(BaseModel):
    reanalyzed_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
