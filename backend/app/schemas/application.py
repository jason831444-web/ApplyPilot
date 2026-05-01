from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.analysis import AuthorizationRisk, NewGradFitLabel, Recommendation


class ApplicationStatus(str, Enum):
    saved = "saved"
    applied = "applied"
    online_assessment = "online_assessment"
    recruiter_screen = "recruiter_screen"
    technical_interview = "technical_interview"
    final_interview = "final_interview"
    offer = "offer"
    rejected = "rejected"
    withdrawn = "withdrawn"
    archived = "archived"


class ApplicationBase(BaseModel):
    job_id: int
    status: ApplicationStatus = ApplicationStatus.saved
    applied_date: date | None = None
    notes: str | None = Field(default=None, max_length=5000)
    next_action: str | None = Field(default=None, max_length=500)
    next_action_date: date | None = None


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus | None = None
    applied_date: date | None = None
    notes: str | None = Field(default=None, max_length=5000)
    next_action: str | None = Field(default=None, max_length=500)
    next_action_date: date | None = None


class ApplicationRead(ApplicationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicationJobSummary(BaseModel):
    id: int
    company_name: str
    job_title: str
    location: str | None = None

    model_config = {"from_attributes": True}


class ApplicationAnalysisSummary(BaseModel):
    overall_score: int
    recommendation: Recommendation | None = None
    authorization_risk: AuthorizationRisk
    new_grad_fit_label: NewGradFitLabel | None = None

    model_config = {"from_attributes": True}


class ApplicationWithJobRead(ApplicationRead):
    job: ApplicationJobSummary
    analysis: ApplicationAnalysisSummary | None = None
