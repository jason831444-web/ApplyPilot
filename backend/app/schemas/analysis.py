from enum import Enum

from pydantic import BaseModel


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
    overall_score: int
    new_grad_fit_score: int
    resume_match_score: int
    authorization_risk: AuthorizationRisk
    recommendation: Recommendation | None = None
    recommendation_reason: str | None = None

    model_config = {"from_attributes": True}
