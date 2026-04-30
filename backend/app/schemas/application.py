from datetime import date
from enum import Enum

from pydantic import BaseModel


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
    notes: str | None = None
    next_action: str | None = None
    next_action_date: date | None = None


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus | None = None
    applied_date: date | None = None
    notes: str | None = None
    next_action: str | None = None
    next_action_date: date | None = None


class ApplicationRead(ApplicationBase):
    id: int
    user_id: int

    model_config = {"from_attributes": True}
