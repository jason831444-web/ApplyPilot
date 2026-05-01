from datetime import date, datetime, timedelta
from types import SimpleNamespace

from app.models.application import ApplicationStatus
from app.models.job_analysis import AuthorizationRisk, NewGradFitLabel, Recommendation
from app.services.dashboard_service import DashboardService


def make_service() -> DashboardService:
    return DashboardService.__new__(DashboardService)


def test_upcoming_followups_are_sorted_and_exclude_inactive_statuses() -> None:
    service = make_service()
    today = date.today()
    active_later = SimpleNamespace(
        id=1,
        job_id=10,
        status=ApplicationStatus.applied,
        next_action="Follow up",
        next_action_date=today + timedelta(days=3),
        job=SimpleNamespace(company_name="Later Co", job_title="SWE"),
    )
    active_earlier = SimpleNamespace(
        id=2,
        job_id=11,
        status=ApplicationStatus.recruiter_screen,
        next_action="Prep screen",
        next_action_date=today + timedelta(days=1),
        job=SimpleNamespace(company_name="Soon Co", job_title="Backend SWE"),
    )
    inactive = SimpleNamespace(
        id=3,
        job_id=12,
        status=ApplicationStatus.rejected,
        next_action="Do not show",
        next_action_date=today,
        job=SimpleNamespace(company_name="No Co", job_title="Frontend SWE"),
    )

    followups = service._upcoming_followups([active_later, active_earlier, inactive])

    assert [followup.application_id for followup in followups] == [2, 1]


def test_best_opportunities_exclude_inactive_applications() -> None:
    service = make_service()
    now = datetime.now()
    active_application = SimpleNamespace(id=1, job_id=10, status=ApplicationStatus.applied)
    rejected_application = SimpleNamespace(id=2, job_id=11, status=ApplicationStatus.rejected)
    active_analysis = SimpleNamespace(
        job_id=10,
        overall_score=91,
        updated_at=now,
        recommendation=Recommendation.apply,
        authorization_risk=AuthorizationRisk.low,
        new_grad_fit_label=NewGradFitLabel.strong_fit,
        job=SimpleNamespace(company_name="Active Co", job_title="SWE", location="Remote"),
    )
    rejected_analysis = SimpleNamespace(
        job_id=11,
        overall_score=99,
        updated_at=now,
        recommendation=Recommendation.apply,
        authorization_risk=AuthorizationRisk.low,
        new_grad_fit_label=NewGradFitLabel.strong_fit,
        job=SimpleNamespace(company_name="Rejected Co", job_title="SWE", location="Remote"),
    )

    opportunities = service._best_opportunities(
        [active_analysis, rejected_analysis],
        {10: active_application, 11: rejected_application},
    )

    assert [opportunity.company_name for opportunity in opportunities] == ["Active Co"]


def test_missing_skills_aggregate_required_and_preferred() -> None:
    service = make_service()
    analyses = [
        SimpleNamespace(missing_required_skills=["AWS", "Docker"], missing_preferred_skills=["Kubernetes"]),
        SimpleNamespace(missing_required_skills=["AWS"], missing_preferred_skills=["FastAPI", "Kubernetes"]),
    ]

    skills = service._top_missing_skills(analyses)

    assert [(skill.skill, skill.count) for skill in skills[:2]] == [("AWS", 2), ("Kubernetes", 2)]
