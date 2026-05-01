from collections import Counter
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.application import Application, ApplicationStatus
from app.models.job import Job
from app.models.job_analysis import JobAnalysis, Recommendation
from app.models.user import User
from app.schemas.dashboard import (
    BestOpportunity,
    CautionReason,
    DashboardSummary,
    DistributionItem,
    MissingSkillItem,
    UpcomingFollowup,
)


INTERVIEW_STATUSES = {
    ApplicationStatus.recruiter_screen,
    ApplicationStatus.technical_interview,
    ApplicationStatus.final_interview,
}
INACTIVE_STATUSES = {
    ApplicationStatus.rejected,
    ApplicationStatus.withdrawn,
    ApplicationStatus.archived,
}


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_summary(self, user: User) -> DashboardSummary:
        jobs = self._jobs_for_user(user.id)
        applications = self._applications_for_user(user.id)
        analyses = self._analyses_for_user(user.id)
        application_by_job_id = {application.job_id: application for application in applications}

        status_counts = Counter(application.status.value for application in applications)
        scores = [analysis.overall_score for analysis in analyses if analysis.overall_score is not None]
        average_match_score = round(sum(scores) / len(scores), 1) if scores else None

        top_missing_skills = self._top_missing_skills(analyses)
        upcoming_followups = self._upcoming_followups(applications)
        best_opportunities = self._best_opportunities(analyses, application_by_job_id)
        caution_reasons = self._caution_reasons(analyses)

        return DashboardSummary(
            total_jobs=len(jobs),
            total_applications=len(applications),
            saved_count=status_counts[ApplicationStatus.saved.value],
            applied_count=status_counts[ApplicationStatus.applied.value],
            interview_count=sum(status_counts[status.value] for status in INTERVIEW_STATUSES),
            rejected_count=status_counts[ApplicationStatus.rejected.value],
            offer_count=status_counts[ApplicationStatus.offer.value],
            average_match_score=average_match_score,
            applications_by_status=self._distribution(status_counts),
            recommendation_distribution=self._distribution(
                Counter(str(analysis.recommendation.value) for analysis in analyses if analysis.recommendation is not None)
            ),
            authorization_risk_distribution=self._distribution(
                Counter(str(analysis.authorization_risk.value) for analysis in analyses if analysis.authorization_risk is not None)
            ),
            new_grad_fit_distribution=self._distribution(
                Counter(str(analysis.new_grad_fit_label.value) for analysis in analyses if analysis.new_grad_fit_label is not None)
            ),
            top_missing_skills=top_missing_skills,
            upcoming_followups=upcoming_followups,
            best_opportunities=best_opportunities,
            caution_reasons=caution_reasons,
            next_recommended_actions=self._next_recommended_actions(
                applications=applications,
                analyses=analyses,
                top_missing_skills=top_missing_skills,
                upcoming_followups=upcoming_followups,
                best_opportunities=best_opportunities,
            ),
        )

    def _jobs_for_user(self, user_id: int) -> list[Job]:
        statement = select(Job).where(Job.user_id == user_id)
        return list(self.db.scalars(statement).all())

    def _applications_for_user(self, user_id: int) -> list[Application]:
        statement = (
            select(Application)
            .where(Application.user_id == user_id)
            .options(selectinload(Application.job).selectinload(Job.analysis))
            .order_by(Application.next_action_date.asc().nulls_last(), Application.updated_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def _analyses_for_user(self, user_id: int) -> list[JobAnalysis]:
        statement = (
            select(JobAnalysis)
            .where(JobAnalysis.user_id == user_id)
            .options(selectinload(JobAnalysis.job).selectinload(Job.application))
        )
        return list(self.db.scalars(statement).all())

    def _distribution(self, counts: Counter[str]) -> list[DistributionItem]:
        return [DistributionItem(label=label, count=count) for label, count in sorted(counts.items())]

    def _top_missing_skills(self, analyses: list[JobAnalysis]) -> list[MissingSkillItem]:
        counts: Counter[str] = Counter()
        for analysis in analyses:
            counts.update(analysis.missing_required_skills or [])
            counts.update(analysis.missing_preferred_skills or [])
        return [MissingSkillItem(skill=skill, count=count) for skill, count in counts.most_common(8)]

    def _upcoming_followups(self, applications: list[Application]) -> list[UpcomingFollowup]:
        followups = [
            application
            for application in applications
            if application.next_action_date is not None and application.status not in INACTIVE_STATUSES
        ]
        followups.sort(key=lambda application: (application.next_action_date, application.id))
        return [
            UpcomingFollowup(
                application_id=application.id,
                job_id=application.job_id,
                company_name=application.job.company_name,
                job_title=application.job.job_title,
                status=application.status,
                next_action=application.next_action,
                next_action_date=application.next_action_date,
            )
            for application in followups[:8]
        ]

    def _best_opportunities(
        self,
        analyses: list[JobAnalysis],
        application_by_job_id: dict[int, Application],
    ) -> list[BestOpportunity]:
        candidates: list[JobAnalysis] = []
        for analysis in analyses:
            if analysis.recommendation not in {Recommendation.apply, Recommendation.apply_with_caution}:
                continue
            application = application_by_job_id.get(analysis.job_id)
            if application is not None and application.status in INACTIVE_STATUSES:
                continue
            candidates.append(analysis)

        candidates.sort(key=lambda analysis: (analysis.overall_score, analysis.updated_at), reverse=True)

        opportunities: list[BestOpportunity] = []
        for analysis in candidates[:6]:
            application = application_by_job_id.get(analysis.job_id)
            opportunities.append(
                BestOpportunity(
                    job_id=analysis.job_id,
                    application_id=application.id if application else None,
                    company_name=analysis.job.company_name,
                    job_title=analysis.job.job_title,
                    location=analysis.job.location,
                    status=application.status if application else None,
                    overall_score=analysis.overall_score,
                    recommendation=analysis.recommendation,
                    authorization_risk=analysis.authorization_risk,
                    new_grad_fit_label=analysis.new_grad_fit_label,
                )
            )
        return opportunities

    def _caution_reasons(self, analyses: list[JobAnalysis]) -> list[CautionReason]:
        counts: Counter[str] = Counter()
        for analysis in analyses:
            counts.update(analysis.concerns or [])
        return [CautionReason(reason=reason, count=count) for reason, count in counts.most_common(8)]

    def _next_recommended_actions(
        self,
        *,
        applications: list[Application],
        analyses: list[JobAnalysis],
        top_missing_skills: list[MissingSkillItem],
        upcoming_followups: list[UpcomingFollowup],
        best_opportunities: list[BestOpportunity],
    ) -> list[str]:
        actions: list[str] = []
        today = date.today()
        week_end = today + timedelta(days=7)
        followups_this_week = [
            application
            for application in applications
            if application.next_action_date is not None
            and today <= application.next_action_date <= week_end
            and application.status not in INACTIVE_STATUSES
        ]
        unknown_auth_count = sum(
            1
            for analysis in analyses
            if analysis.authorization_risk is not None and analysis.authorization_risk.value == "unknown"
        )

        if followups_this_week:
            actions.append(f"Follow up on {len(followups_this_week)} application(s) this week.")
        if best_opportunities:
            actions.append("Prioritize jobs with Apply or Apply with Caution recommendations.")
        if top_missing_skills:
            skills = ", ".join(skill.skill for skill in top_missing_skills[:3])
            actions.append(f"Consider improving or better highlighting missing skills: {skills}.")
        if unknown_auth_count:
            actions.append(f"Review {unknown_auth_count} job(s) with unknown authorization risk before investing more time.")
        if not actions:
            actions.append("Analyze a few target jobs to generate stronger dashboard insights.")

        return actions
