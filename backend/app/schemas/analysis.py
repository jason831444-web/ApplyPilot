from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field, computed_field

from app.services.analysis.rules import DOMAIN_SIGNAL_LABELS


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

    @computed_field
    @property
    def technical_skills(self) -> list[str]:
        return unique_strings(
            [skill for skill in self.required_skills + self.preferred_skills if skill not in DOMAIN_SIGNAL_LABELS]
        )

    @computed_field
    @property
    def domain_signals(self) -> list[str]:
        values = [str(item.get("label", "")) for item in self.evidence if item.get("type") == "domain"]
        return unique_strings([value for value in values if value in DOMAIN_SIGNAL_LABELS])

    @computed_field
    @property
    def missing_technical_skills(self) -> list[str]:
        return unique_strings(
            [
                skill
                for skill in self.missing_required_skills + self.missing_preferred_skills
                if skill not in DOMAIN_SIGNAL_LABELS
            ]
        )

    @computed_field
    @property
    def missing_domain_signals(self) -> list[str]:
        return []

    @computed_field
    @property
    def skill_extraction_confidence(self) -> str:
        technical_skill_count = len(self.technical_skills)
        if technical_skill_count <= 1:
            return "low"
        if technical_skill_count == 2:
            return "medium"
        return "high"

    @computed_field
    @property
    def skill_gap_note(self) -> str | None:
        technical_skill_count = len(self.technical_skills)
        if technical_skill_count == 0:
            return "No structured technical requirements were detected, so skill gap analysis may be incomplete."
        if technical_skill_count == 1:
            return "Only one technical requirement was detected, so missing-skill analysis may be incomplete."
        if technical_skill_count == 2:
            return "Only a small number of technical requirements were detected."
        return None

    model_config = {"from_attributes": True}


def unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.lower()
        if value and key not in seen:
            seen.add(key)
            result.append(value)
    return result
