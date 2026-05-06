from app.models.job import Job
from app.models.profile import Profile
from app.services.analysis.evidence import dedupe_evidence
from app.services.analysis.extraction import (
    detect_employment_type,
    extract_authorization,
    extract_experience_signals,
    extract_skills_by_requirement,
    section_kind,
    split_sections,
    unique_preserve,
)
from app.services.analysis.provider import JobAnalysisResult
from app.services.analysis.scoring import (
    apply_sparse_skill_caps,
    cap_overall_score,
    overall_score,
    recommend,
    score_location,
    score_new_grad_fit,
    score_resume_match,
    score_skill_match,
    user_likely_needs_sponsorship,
)


class DeterministicRuleBasedProvider:
    """No-paid-AI provider that analyzes job fit with deterministic rules."""

    def analyze(self, profile: Profile, job: Job) -> JobAnalysisResult:
        description = job.job_description or ""
        required_skills, preferred_skills, skill_evidence = extract_skills_by_requirement(description)
        has_clean_skill_sections = self._has_clean_skill_sections(description)
        seniority_signals, positive_signals, negative_signals = extract_experience_signals(description)
        authorization_risk, authorization_evidence = extract_authorization(description)
        new_grad_fit_label, new_grad_fit_score = score_new_grad_fit(
            positive_signals=positive_signals,
            negative_signals=negative_signals,
            seniority_signals=seniority_signals,
        )

        profile_text = self._profile_text(profile)
        required_skill_score, missing_required_skills = score_skill_match(required_skills, profile_text)
        preferred_skill_score, missing_preferred_skills = score_skill_match(preferred_skills, profile_text)
        all_job_skills = unique_preserve(required_skills + preferred_skills)
        resume_match_score = score_resume_match(all_job_skills, profile_text)
        technical_skill_count = len(all_job_skills)
        required_skill_score, preferred_skill_score, resume_match_score = apply_sparse_skill_caps(
            required_skill_score=required_skill_score,
            preferred_skill_score=preferred_skill_score,
            resume_match_score=resume_match_score,
            technical_skill_count=technical_skill_count,
            has_clean_skill_sections=has_clean_skill_sections,
        )
        location_fit_score = score_location(job.location, profile.target_locations or [])
        experience_fit_score = new_grad_fit_score
        total_score = overall_score(
            required_skill_score=required_skill_score,
            preferred_skill_score=preferred_skill_score,
            experience_fit_score=experience_fit_score,
            resume_match_score=resume_match_score,
            location_fit_score=location_fit_score,
            authorization_risk=authorization_risk,
        )
        total_score = cap_overall_score(
            score=total_score,
            technical_skill_count=technical_skill_count,
            has_clean_skill_sections=has_clean_skill_sections,
            new_grad_fit_label=new_grad_fit_label,
            new_grad_fit_score=new_grad_fit_score,
            authorization_risk=authorization_risk,
            negative_signals=negative_signals,
        )
        recommendation, recommendation_reason = recommend(
            overall=total_score,
            new_grad_fit_label=new_grad_fit_label,
            authorization_risk=authorization_risk,
            missing_required_skills=missing_required_skills,
            user_needs_sponsorship=user_likely_needs_sponsorship(profile.work_authorization_notes),
        )

        strengths = self._strengths(
            required_skill_score=required_skill_score,
            preferred_skill_score=preferred_skill_score,
            has_required_skills=bool(required_skills),
            has_preferred_skills=bool(preferred_skills),
            has_clean_skill_sections=has_clean_skill_sections,
            technical_skill_count=technical_skill_count,
            location_fit_score=location_fit_score,
            new_grad_fit_label=new_grad_fit_label,
            matched_skills=[skill for skill in all_job_skills if skill not in missing_required_skills + missing_preferred_skills],
        )
        concerns = self._concerns(
            authorization_risk=authorization_risk,
            new_grad_fit_label=new_grad_fit_label,
            missing_required_skills=missing_required_skills,
            missing_preferred_skills=missing_preferred_skills,
            has_required_skills=bool(required_skills),
            has_preferred_skills=bool(preferred_skills),
            has_clean_skill_sections=has_clean_skill_sections,
            technical_skill_count=technical_skill_count,
            location_fit_score=location_fit_score,
            negative_signals=negative_signals,
        )
        next_actions = self._next_actions(
            recommendation=recommendation,
            missing_required_skills=missing_required_skills,
            authorization_risk=authorization_risk,
            user_needs_sponsorship=user_likely_needs_sponsorship(profile.work_authorization_notes),
        )

        evidence = dedupe_evidence(skill_evidence + seniority_signals + authorization_evidence)
        summary = (
            f"{job.job_title} at {job.company_name} scored {total_score}/100. "
            f"New-grad fit is {new_grad_fit_label.replace('_', ' ')} and authorization risk is {authorization_risk}."
        )

        return JobAnalysisResult(
            parsed_title=job.job_title,
            parsed_company=job.company_name,
            parsed_locations=[job.location] if job.location else [],
            employment_type=detect_employment_type(description),
            seniority_signals=seniority_signals,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            experience_requirements=seniority_signals,
            overall_score=total_score,
            new_grad_fit_score=new_grad_fit_score,
            resume_match_score=resume_match_score,
            required_skill_score=required_skill_score,
            preferred_skill_score=preferred_skill_score,
            experience_fit_score=experience_fit_score,
            location_fit_score=location_fit_score,
            new_grad_fit_label=new_grad_fit_label,
            authorization_risk=authorization_risk,
            recommendation=recommendation,
            recommendation_reason=recommendation_reason,
            summary=summary,
            strengths=strengths,
            concerns=concerns,
            missing_required_skills=missing_required_skills,
            missing_preferred_skills=missing_preferred_skills,
            new_grad_positive_signals=positive_signals,
            new_grad_negative_signals=negative_signals,
            authorization_evidence=authorization_evidence,
            evidence=evidence,
            next_actions=next_actions,
            analysis_confidence=self._confidence(
                required_skills,
                preferred_skills,
                seniority_signals,
                authorization_evidence,
                has_clean_skill_sections=has_clean_skill_sections,
            ),
        )

    def _profile_text(self, profile: Profile) -> str:
        projects = profile.projects or []
        return " ".join(
            [
                profile.resume_text or "",
                " ".join(profile.skills or []),
                " ".join(str(project) for project in projects),
                profile.experience_summary or "",
                " ".join(profile.target_roles or []),
                " ".join(profile.target_locations or []),
                profile.work_authorization_notes or "",
            ]
        )

    def _strengths(
        self,
        *,
        required_skill_score: int,
        preferred_skill_score: int,
        has_required_skills: bool,
        has_preferred_skills: bool,
        has_clean_skill_sections: bool,
        technical_skill_count: int,
        location_fit_score: int,
        new_grad_fit_label: str,
        matched_skills: list[str],
    ) -> list[str]:
        strengths: list[str] = []
        if matched_skills:
            strengths.append(f"Profile matches key skills: {', '.join(matched_skills[:8])}.")
        if has_required_skills and required_skill_score >= 75 and technical_skill_count >= 3 and has_clean_skill_sections:
            strengths.append("Strong coverage of required skills.")
        if has_preferred_skills and preferred_skill_score >= 75:
            strengths.append("Good overlap with preferred skills.")
        if not has_clean_skill_sections:
            strengths.append("The posting does not list clean required/preferred skill sections, so matching confidence is lower.")
        if technical_skill_count <= 2:
            strengths.append("The posting provides limited technical skill evidence, so matching confidence is lower.")
        if new_grad_fit_label in {"strong_fit", "good_fit"}:
            strengths.append("Posting includes new-grad friendly seniority signals.")
        if location_fit_score >= 80:
            strengths.append("Location appears aligned with target locations or remote preference.")
        return strengths or ["Some profile overlap was found, but the strongest evidence is limited."]

    def _concerns(
        self,
        *,
        authorization_risk: str,
        new_grad_fit_label: str,
        missing_required_skills: list[str],
        missing_preferred_skills: list[str],
        has_required_skills: bool,
        has_preferred_skills: bool,
        has_clean_skill_sections: bool,
        technical_skill_count: int,
        location_fit_score: int,
        negative_signals: list[dict],
    ) -> list[str]:
        concerns: list[str] = []
        if not has_required_skills:
            concerns.append("No explicit required skills were detected, so the skill score is based on limited evidence.")
        if not has_preferred_skills and not has_clean_skill_sections:
            concerns.append("No explicit preferred skills were detected in a clean preferred-skills section.")
        if technical_skill_count <= 2:
            concerns.append("Only limited technical skill evidence was detected, so match confidence is lower.")
        if technical_skill_count <= 1:
            concerns.append("Skill matching confidence is limited due to sparse or unstructured technical requirements.")
        if not has_clean_skill_sections and technical_skill_count <= 2:
            concerns.append("This posting is unstructured, so the score should be interpreted cautiously.")
        if missing_required_skills:
            concerns.append(f"Missing required skills: {', '.join(missing_required_skills[:8])}.")
        if missing_preferred_skills:
            concerns.append(f"Missing preferred skills: {', '.join(missing_preferred_skills[:8])}.")
        missing_technical_skills = self._dedupe_text(missing_required_skills + missing_preferred_skills)
        if missing_technical_skills:
            concerns.append(f"Missing technical skills detected: {', '.join(missing_technical_skills[:8])}.")
        if new_grad_fit_label == "not_new_grad_friendly":
            concerns.append("This role shows senior-level or high-experience signals that may not be new-grad friendly.")
        if new_grad_fit_label in {"weak_fit", "not_new_grad_friendly"}:
            concerns.append("Seniority or experience requirements may be above a new-grad level.")
        if new_grad_fit_label == "weak_fit":
            concerns.append("This role may not be well-aligned with typical new-grad expectations.")
        if negative_signals:
            labels = [str(signal.get("label", "")).replace("_", " ") for signal in negative_signals[:4]]
            if self._has_seniority_or_ownership_signal(negative_signals):
                concerns.append("The posting emphasizes seniority, ownership, or high-agency expectations.")
            concerns.append(f"Startup intensity or ownership signals may raise the bar for a new grad: {', '.join(labels)}.")
            concerns.append("Startup intensity and ownership expectations may raise the bar for this role.")
        if authorization_risk == "high":
            concerns.append("Work authorization language appears high risk.")
            concerns.append("This role may require work authorization or sponsorship that is not currently met.")
        elif authorization_risk == "unknown":
            concerns.append("No clear sponsorship or work authorization evidence was found.")
            concerns.append("Work authorization requirements are unclear from the job posting.")
        if location_fit_score < 50:
            concerns.append("Location does not appear to match the profile targets.")
        return self._dedupe_text(concerns)

    def _has_seniority_or_ownership_signal(self, signals: list[dict]) -> bool:
        keywords = {"senior", "staff", "principal", "lead", "architect", "ownership", "cto", "all rounder"}
        labels = " ".join(str(signal.get("label", "")).lower() for signal in signals)
        return any(keyword in labels for keyword in keywords)

    def _dedupe_text(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            key = value.lower().strip().rstrip(".")
            if key and key not in seen:
                seen.add(key)
                result.append(value)
        return result

    def _has_clean_skill_sections(self, description: str) -> bool:
        return any(section_kind(heading) in {"required", "preferred"} for heading, _body in split_sections(description))

    def _next_actions(
        self,
        *,
        recommendation: str,
        missing_required_skills: list[str],
        authorization_risk: str,
        user_needs_sponsorship: bool,
    ) -> list[str]:
        actions: list[str] = []
        if recommendation in {"apply", "apply_with_caution", "maybe"}:
            actions.append("Tailor the resume summary to the strongest matched required skills.")
        if missing_required_skills:
            actions.append(f"Decide whether to address or de-emphasize gaps in: {', '.join(missing_required_skills[:5])}.")
        if authorization_risk in {"medium", "unknown"}:
            actions.append("Check the company careers page or recruiter notes for sponsorship language before investing heavily.")
        if authorization_risk == "high" and user_needs_sponsorship:
            actions.append("Skip or only proceed if you can confirm an exception with a recruiter.")
        if recommendation == "skip":
            actions.append("Prioritize roles with clearer new-grad fit and fewer authorization concerns.")
        return actions

    def _confidence(
        self,
        required_skills: list[str],
        preferred_skills: list[str],
        seniority_signals: list[dict],
        authorization_evidence: list[dict],
        *,
        has_clean_skill_sections: bool,
    ) -> float:
        evidence_count = len(required_skills) + len(preferred_skills) + len(seniority_signals) + len(authorization_evidence)
        if not has_clean_skill_sections and len(required_skills) + len(preferred_skills) <= 2:
            return 0.52
        if evidence_count >= 8:
            return 0.86
        if evidence_count >= 4:
            return 0.78
        return 0.64
