from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class JobAnalysisResult:
    parsed_title: str | None = None
    parsed_company: str | None = None
    parsed_locations: list[str] = field(default_factory=list)
    employment_type: str | None = None
    seniority_signals: list[dict] = field(default_factory=list)
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    experience_requirements: list[dict] = field(default_factory=list)
    overall_score: int = 0
    new_grad_fit_score: int = 0
    resume_match_score: int = 0
    required_skill_score: int = 0
    preferred_skill_score: int = 0
    experience_fit_score: int = 0
    location_fit_score: int = 0
    new_grad_fit_label: str = "mixed_fit"
    authorization_risk: str = "unknown"
    recommendation: str = "maybe"
    recommendation_reason: str = ""
    summary: str = ""
    strengths: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
    missing_required_skills: list[str] = field(default_factory=list)
    missing_preferred_skills: list[str] = field(default_factory=list)
    new_grad_positive_signals: list[dict] = field(default_factory=list)
    new_grad_negative_signals: list[dict] = field(default_factory=list)
    authorization_evidence: list[dict] = field(default_factory=list)
    evidence: list[dict] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    analysis_provider: str = "deterministic_rule_based"
    analysis_confidence: float = 0.74
    fallback_used: bool = False


class AnalysisProvider(Protocol):
    def analyze(self, profile: object, job: object) -> JobAnalysisResult:
        """Analyze a job against a profile and return a structured result."""
        ...
