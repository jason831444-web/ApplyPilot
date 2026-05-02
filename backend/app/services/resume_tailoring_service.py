import re

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.job_analysis import JobAnalysis
from app.models.profile import Profile
from app.models.user import User
from app.repositories.analyses import AnalysisRepository
from app.schemas.resume_tailoring import ResumeTailoringRead
from app.services.analysis.scoring import skill_match_patterns
from app.services.analysis.rules import DOMAIN_SIGNAL_LABELS
from app.services.job_service import JobService
from app.services.profile_service import ProfileService


class ResumeTailoringService:
    def __init__(self, db: Session) -> None:
        self.jobs = JobService(db)
        self.profiles = ProfileService(db)
        self.analyses = AnalysisRepository(db)

    def generate_for_user(self, *, user: User, job_id: int) -> ResumeTailoringRead:
        job = self.jobs.get_for_user(user=user, job_id=job_id)
        analysis = self.analyses.get_by_job_for_user(job_id=job.id, user_id=user.id)
        if analysis is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Run job analysis before generating resume tailoring suggestions.",
            )

        profile = self.profiles.get_or_create_for_user(user)
        return self._generate(profile=profile, job=job, analysis=analysis)

    def _generate(self, *, profile: Profile, job: Job, analysis: JobAnalysis) -> ResumeTailoringRead:
        profile_text = self._profile_text(profile)
        matched_skills = self._matched_skills(analysis=analysis, profile_text=profile_text)
        missing_skills = self._unique((analysis.missing_required_skills or []) + (analysis.missing_preferred_skills or []))
        project_suggestions = self._project_suggestions(profile=profile, job=job, analysis=analysis, matched_skills=matched_skills)

        return ResumeTailoringRead(
            tailored_summary=self._tailored_summary(
                profile=profile,
                job=job,
                analysis=analysis,
                matched_skills=matched_skills,
                project_suggestions=project_suggestions,
            ),
            bullet_suggestions=self._bullet_suggestions(
                profile=profile,
                job=job,
                analysis=analysis,
                matched_skills=matched_skills,
                project_suggestions=project_suggestions,
            ),
            keywords_to_add=missing_skills[:12],
            skills_to_emphasize=matched_skills[:12],
            project_suggestions=project_suggestions,
            cautions=self._cautions(analysis=analysis, missing_skills=missing_skills),
        )

    def _tailored_summary(
        self,
        *,
        profile: Profile,
        job: Job,
        analysis: JobAnalysis,
        matched_skills: list[str],
        project_suggestions: list[str],
    ) -> str:
        role = self._first(profile.target_roles or []) or job.job_title or "software engineering"
        if len(matched_skills) <= 1 and matched_skills:
            skill_phrase = f"emphasizing {self._natural_skill_phrase(matched_skills)} where relevant"
        else:
            skill_phrase = self._natural_skill_phrase(matched_skills[:8]) if matched_skills else "software engineering fundamentals"
        project_theme = self._project_theme(project_suggestions, profile.projects or [])
        domain_signals = self._domain_signals(analysis)

        sentences = [
            self._summary_skill_sentence(role=role, skill_phrase=skill_phrase, matched_skill_count=len(matched_skills)),
            f"Project experience includes {project_theme}, with emphasis on production-minded backend, data, and dashboard workflows.",
        ]
        if domain_signals:
            sentences.append(f"For this role, emphasize relevant exposure to {self._natural_skill_phrase(domain_signals[:3])} without overstating experience.")
        return " ".join(sentences)

    def _summary_skill_sentence(self, *, role: str, skill_phrase: str, matched_skill_count: int) -> str:
        if matched_skill_count <= 1:
            return f"Computer Science new-grad candidate targeting {role} roles, with resume tailoring focused on {skill_phrase}."
        return f"Computer Science new-grad candidate targeting {role} roles with hands-on experience in {skill_phrase}."

    def _bullet_suggestions(
        self,
        *,
        profile: Profile,
        job: Job,
        analysis: JobAnalysis,
        matched_skills: list[str],
        project_suggestions: list[str],
    ) -> list[str]:
        bullets: list[str] = []
        skills = self._natural_skill_phrase(matched_skills[:5]) if matched_skills else "the most relevant existing technical skills"

        if project_suggestions:
            bullets.append(f"Highlight {project_suggestions[0]} as relevant project experience using {skills}.")
        if any(self._contains_signal(skill, {"Backend", "REST API", "FastAPI", "Python", "PostgreSQL", "SQL"}) for skill in matched_skills):
            bullets.append("Emphasize backend API design, database work, structured data handling, and production-minded implementation from existing projects.")
        if any(self._contains_signal(skill, {"React", "Next.js", "TypeScript", "JavaScript"}) for skill in matched_skills):
            bullets.append("Show full-stack delivery by connecting frontend dashboard work to backend services and persisted data.")
        if any(self._contains_signal(skill, {"AI", "AI Agents", "Machine Learning", "Computer Vision", "Healthcare", "Health-tech"}) for skill in self._analysis_signals(analysis)):
            bullets.append("If applying to AI, healthcare, or automation roles, mention relevant AI/CV project experience without overstating domain-specific healthcare experience.")
        if self._enum_value(analysis.new_grad_fit_label) in {"mixed_fit", "weak_fit", "not_new_grad_friendly"}:
            bullets.append("Tailor one bullet toward ownership, shipping complete features, and debugging production-style issues using work already represented in the profile.")

        return self._unique(bullets)[:5]

    def _project_suggestions(
        self,
        *,
        profile: Profile,
        job: Job,
        analysis: JobAnalysis,
        matched_skills: list[str],
    ) -> list[str]:
        projects = [str(project).strip() for project in profile.projects or [] if str(project).strip()]
        if not projects:
            return []

        job_terms = " ".join([job.job_title, job.job_description, " ".join(analysis.required_skills or []), " ".join(analysis.preferred_skills or [])]).lower()
        scored: list[tuple[int, str]] = []
        for project in projects:
            project_lower = project.lower()
            score = sum(1 for skill in matched_skills if re.search(rf"\b{re.escape(skill.lower())}\b", project_lower))
            score += sum(1 for token in ["ai", "backend", "dashboard", "parser", "computer vision", "healthcare", "job-fit"] if token in project_lower and token in job_terms)
            scored.append((score, project))

        scored.sort(key=lambda item: (-item[0], projects.index(item[1])))
        return [project for _score, project in scored[:4]]

    def _cautions(self, *, analysis: JobAnalysis, missing_skills: list[str]) -> list[str]:
        cautions: list[str] = []
        if missing_skills:
            cautions.append(f"Do not claim hands-on experience with missing skills unless they are genuinely represented in your background: {self._join(missing_skills[:6])}.")
        if self._enum_value(analysis.authorization_risk) in {"unknown", "high"}:
            cautions.append("Verify sponsorship and work authorization language before investing heavily in this application.")
        if self._enum_value(analysis.new_grad_fit_label) in {"mixed_fit", "weak_fit", "not_new_grad_friendly"}:
            cautions.append("Because new-grad fit is not clearly strong, tailor the resume toward ownership, production experience, and relevant projects.")
        if not analysis.required_skills:
            cautions.append("The posting does not list explicit required skills, so treat keyword suggestions as low-confidence signals.")
        return cautions

    def _matched_skills(self, *, analysis: JobAnalysis, profile_text: str) -> list[str]:
        job_skills = self._unique((analysis.required_skills or []) + (analysis.preferred_skills or []))
        return [skill for skill in job_skills if self._skill_in_profile(skill, profile_text)]

    def _skill_in_profile(self, skill: str, profile_text: str) -> bool:
        return any(re.search(pattern, profile_text, re.IGNORECASE) for pattern in skill_match_patterns(skill))

    def _profile_text(self, profile: Profile) -> str:
        return " ".join(
            [
                profile.resume_text or "",
                " ".join(profile.skills or []),
                " ".join(str(project) for project in profile.projects or []),
                profile.experience_summary or "",
                " ".join(profile.target_roles or []),
                " ".join(profile.target_locations or []),
            ]
        )

    def _domain_signals(self, analysis: JobAnalysis) -> list[str]:
        domain_values = {"AI", "AI Agents", "Healthcare", "Health-tech", "Startup", "Product Management"}
        return [skill for skill in self._analysis_signals(analysis) if skill in domain_values]

    def _analysis_signals(self, analysis: JobAnalysis) -> list[str]:
        domain_values = [
            str(item.get("label", ""))
            for item in analysis.evidence or []
            if item.get("type") == "domain" and str(item.get("label", "")) in DOMAIN_SIGNAL_LABELS
        ]
        return self._unique((analysis.required_skills or []) + (analysis.preferred_skills or []) + domain_values)

    def _project_theme(self, project_suggestions: list[str], projects: list[str]) -> str:
        selected = project_suggestions or [str(project) for project in projects if str(project).strip()]
        if selected:
            return self._join(selected[:3])
        return "applied software projects"

    def _contains_signal(self, value: str, signals: set[str]) -> bool:
        return value in signals

    def _first(self, values: list[str]) -> str | None:
        return next((value for value in values if value), None)

    def _join(self, values: list[str]) -> str:
        clean_values = [value for value in values if value]
        if len(clean_values) <= 1:
            return "".join(clean_values)
        return ", ".join(clean_values[:-1]) + f", and {clean_values[-1]}"

    def _natural_skill_phrase(self, values: list[str]) -> str:
        phrase_map = {
            "Backend": "backend engineering",
            "AI": "AI systems",
            "AI Agents": "AI agent workflows",
            "Healthcare": "healthcare workflows",
            "Health-tech": "health-tech products",
            "Startup": "startup environments",
            "Product Management": "product management collaboration",
        }
        return self._join([phrase_map.get(value, value) for value in values])

    def _unique(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            normalized = value.strip()
            key = normalized.lower()
            if normalized and key not in seen:
                seen.add(key)
                result.append(normalized)
        return result

    def _enum_value(self, value: object) -> str:
        return str(getattr(value, "value", value))
