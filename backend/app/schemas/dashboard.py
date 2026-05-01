from datetime import date

from pydantic import BaseModel

from app.schemas.analysis import AuthorizationRisk, NewGradFitLabel, Recommendation
from app.schemas.application import ApplicationStatus


class DistributionItem(BaseModel):
    label: str
    count: int


class MissingSkillItem(BaseModel):
    skill: str
    count: int


class UpcomingFollowup(BaseModel):
    application_id: int
    job_id: int
    company_name: str
    job_title: str
    status: ApplicationStatus
    next_action: str | None = None
    next_action_date: date


class BestOpportunity(BaseModel):
    job_id: int
    application_id: int | None = None
    company_name: str
    job_title: str
    location: str | None = None
    status: ApplicationStatus | None = None
    overall_score: int
    recommendation: Recommendation | None = None
    authorization_risk: AuthorizationRisk
    new_grad_fit_label: NewGradFitLabel | None = None


class CautionReason(BaseModel):
    reason: str
    count: int


class DashboardSummary(BaseModel):
    total_jobs: int
    total_applications: int
    saved_count: int
    applied_count: int
    interview_count: int
    rejected_count: int
    offer_count: int
    average_match_score: float | None
    applications_by_status: list[DistributionItem]
    recommendation_distribution: list[DistributionItem]
    authorization_risk_distribution: list[DistributionItem]
    new_grad_fit_distribution: list[DistributionItem]
    top_missing_skills: list[MissingSkillItem]
    upcoming_followups: list[UpcomingFollowup]
    best_opportunities: list[BestOpportunity]
    caution_reasons: list[CautionReason]
    next_recommended_actions: list[str]
