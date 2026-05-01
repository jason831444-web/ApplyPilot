from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field


class NewGradFitLabel(str, Enum):
    strong_fit = "strong_fit"
    good_fit = "good_fit"
    mixed_fit = "mixed_fit"
    weak_fit = "weak_fit"
    not_new_grad_friendly = "not_new_grad_friendly"


class AuthorizationRisk(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    unknown = "unknown"


class Recommendation(str, Enum):
    apply = "apply"
    apply_with_caution = "apply_with_caution"
    maybe = "maybe"
    skip = "skip"


class JobAnalysisRead(BaseModel):
    id: int
    job_id: int
    user_id: int
    parsed_title: str | None = None
    parsed_company: str | None = None
    parsed_locations: list[str]
    employment_type: str | None = None
    seniority_signals: list[dict]
    required_skills: list[str]
    preferred_skills: list[str]
    experience_requirements: list[dict]
    overall_score: int = Field(ge=0, le=100)
    new_grad_fit_score: int = Field(ge=0, le=100)
    resume_match_score: int = Field(ge=0, le=100)
    required_skill_score: int = Field(ge=0, le=100)
    preferred_skill_score: int = Field(ge=0, le=100)
    experience_fit_score: int = Field(ge=0, le=100)
    location_fit_score: int = Field(ge=0, le=100)
    new_grad_fit_label: NewGradFitLabel | None = None
    authorization_risk: AuthorizationRisk
    recommendation: Recommendation | None = None
    recommendation_reason: str | None = None
    summary: str | None = None
    strengths: list[str]
    concerns: list[str]
    missing_required_skills: list[str]
    missing_preferred_skills: list[str]
    new_grad_positive_signals: list[dict]
    new_grad_negative_signals: list[dict]
    authorization_evidence: list[dict]
    evidence: list[dict]
    next_actions: list[str]
    analysis_provider: str
    analysis_confidence: float | None = None
    fallback_used: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
