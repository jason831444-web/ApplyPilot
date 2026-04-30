import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AuthorizationRisk(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    unknown = "unknown"


class Recommendation(str, enum.Enum):
    apply = "apply"
    apply_with_caution = "apply_with_caution"
    maybe = "maybe"
    skip = "skip"


class NewGradFitLabel(str, enum.Enum):
    strong_fit = "strong_fit"
    good_fit = "good_fit"
    mixed_fit = "mixed_fit"
    weak_fit = "weak_fit"
    not_new_grad_friendly = "not_new_grad_friendly"


class JobAnalysis(Base):
    __tablename__ = "job_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    parsed_title: Mapped[str | None] = mapped_column(String(255))
    parsed_company: Mapped[str | None] = mapped_column(String(255))
    parsed_locations: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    employment_type: Mapped[str | None] = mapped_column(String(100))
    seniority_signals: Mapped[list[dict]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    required_skills: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    preferred_skills: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    experience_requirements: Mapped[list[dict]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    new_grad_fit_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    resume_match_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    required_skill_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    preferred_skill_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    experience_fit_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    location_fit_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    new_grad_fit_label: Mapped[NewGradFitLabel | None] = mapped_column(
        Enum(NewGradFitLabel, name="new_grad_fit_label")
    )
    authorization_risk: Mapped[AuthorizationRisk] = mapped_column(
        Enum(AuthorizationRisk, name="authorization_risk"),
        nullable=False,
        default=AuthorizationRisk.unknown,
        server_default=AuthorizationRisk.unknown.value,
    )
    recommendation: Mapped[Recommendation | None] = mapped_column(
        Enum(Recommendation, name="recommendation")
    )
    recommendation_reason: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    strengths: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    concerns: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    missing_required_skills: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    missing_preferred_skills: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    new_grad_positive_signals: Mapped[list[dict]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    new_grad_negative_signals: Mapped[list[dict]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    authorization_evidence: Mapped[list[dict]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    evidence: Mapped[list[dict]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    next_actions: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    analysis_provider: Mapped[str] = mapped_column(
        String(100), nullable=False, default="deterministic_rule_based", server_default="deterministic_rule_based"
    )
    analysis_confidence: Mapped[float | None] = mapped_column(Float)
    fallback_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    job = relationship("Job", back_populates="analysis")
    user = relationship("User", back_populates="analyses")
