import re

from app.models.job import Job
from app.models.profile import Profile
from app.services.analysis.evidence import dedupe_evidence
from app.services.analysis.extraction import (
    detect_employment_type,
    extract_alternative_skill_groups,
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
    skill_match_patterns,
    user_likely_needs_sponsorship,
)


class DeterministicRuleBasedProvider:
    """No-paid-AI provider that analyzes job fit with deterministic rules."""

    def analyze(self, profile: Profile, job: Job) -> JobAnalysisResult:
        description = job.job_description or ""
        required_skills, preferred_skills, skill_evidence = extract_skills_by_requirement(description)
        alternative_skill_groups = extract_alternative_skill_groups(description)
        has_clean_skill_sections = self._has_clean_skill_sections(description)
        analysis_text = f"{job.job_title or ''}\n{description}"
        seniority_signals, positive_signals, negative_signals = extract_experience_signals(analysis_text)
        authorization_risk, authorization_evidence = extract_authorization(description)
        context_labels = {item["label"] for item in skill_evidence if item.get("type") == "domain"}
        new_grad_fit_label, new_grad_fit_score = score_new_grad_fit(
            positive_signals=positive_signals,
            negative_signals=negative_signals,
            seniority_signals=seniority_signals,
        )

        profile_text = self._profile_text(profile)
        required_skill_score, missing_required_skills = score_skill_match(required_skills, profile_text)
        preferred_skill_score, missing_preferred_skills = score_skill_match(preferred_skills, profile_text)
        missing_required_skills = self._remove_satisfied_alternative_gaps(
            missing_skills=missing_required_skills,
            alternative_skill_groups=alternative_skill_groups,
            profile_text=profile_text,
        )
        if len(missing_required_skills) != len(required_skills):
            required_skill_score = self._rescore(required_skills, missing_required_skills)
        all_job_skills = unique_preserve(required_skills + preferred_skills)
        scored_job_skills = self._collapse_satisfied_alternatives(
            skills=all_job_skills,
            alternative_skill_groups=alternative_skill_groups,
            profile_text=profile_text,
        )
        resume_match_score = score_resume_match(scored_job_skills, profile_text)
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
            context_labels=context_labels,
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
            matched_skills=self._matched_profile_skills(all_job_skills, profile_text),
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
            context_labels=context_labels,
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
                context_labels=context_labels,
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
        context_labels: set[str],
    ) -> list[str]:
        concerns: list[str] = []
        sparse_concern = "Only limited structured technical requirements were detected, so match confidence is lower."
        if not has_required_skills:
            concerns.append(sparse_concern)
        if not has_preferred_skills and not has_clean_skill_sections:
            concerns.append(sparse_concern)
        if technical_skill_count <= 2:
            concerns.append(sparse_concern)
        if technical_skill_count <= 1:
            concerns.append(sparse_concern)
        if not has_clean_skill_sections and technical_skill_count <= 2:
            concerns.append(sparse_concern)
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
            concerns.append(f"Startup intensity and ownership expectations may raise the bar for this role: {', '.join(labels)}.")
        if authorization_risk == "high":
            concerns.append("Work authorization language appears high risk.")
            concerns.append("This role may require work authorization or sponsorship that is not currently met.")
        elif authorization_risk == "unknown":
            concerns.append("Work authorization requirements are unclear from the job posting.")
        if "Nontraditional Work" in context_labels:
            concerns.append("This appears to be a flexible platform-based or gig-like role rather than a standard full-time SWE position.")
        if "Staffing/Training Placement" in context_labels:
            concerns.append("This posting appears to have staffing, training, or client-placement signals; verify employment terms carefully.")
        if location_fit_score < 50:
            concerns.append("Location does not appear to match the profile targets.")
        return self._dedupe_concerns(concerns)

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

    def _dedupe_concerns(self, values: list[str]) -> list[str]:
        normalized_groups = [
            ("missing technical skills", "missing technical skills detected"),
            ("authorization unclear", "work authorization requirements are unclear"),
            ("sparse technical evidence", "limited structured technical requirements"),
            ("ownership intensity", "ownership expectations may raise the bar"),
            ("staffing placement", "staffing, training, or client-placement"),
            ("gig platform", "platform-based or gig-like"),
        ]
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            lowered = value.lower().strip().rstrip(".")
            if lowered.startswith(("missing required skills:", "missing preferred skills:")):
                continue
            if lowered.startswith("no clear sponsorship or work authorization evidence"):
                continue
            key = lowered
            for group_key, marker in normalized_groups:
                if marker in lowered:
                    key = group_key
                    break
            if key and key not in seen:
                seen.add(key)
                result.append(value)
        return result

    def _remove_satisfied_alternative_gaps(
        self,
        *,
        missing_skills: list[str],
        alternative_skill_groups: list[list[str]],
        profile_text: str,
    ) -> list[str]:
        filtered = list(missing_skills)
        for group in alternative_skill_groups:
            if any(self._profile_matches_skill(skill, profile_text) for skill in group):
                filtered = [skill for skill in filtered if skill not in group]
        return filtered

    def _collapse_satisfied_alternatives(
        self,
        *,
        skills: list[str],
        alternative_skill_groups: list[list[str]],
        profile_text: str,
    ) -> list[str]:
        collapsed = list(skills)
        for group in alternative_skill_groups:
            matched = [skill for skill in group if self._profile_matches_skill(skill, profile_text)]
            if matched:
                collapsed = [skill for skill in collapsed if skill not in group or skill in matched]
        return collapsed

    def _profile_matches_skill(self, skill: str, profile_text: str) -> bool:
        return any(re.search(pattern, profile_text, re.IGNORECASE) for pattern in skill_match_patterns(skill))

    def _matched_profile_skills(self, skills: list[str], profile_text: str) -> list[str]:
        return [skill for skill in skills if self._profile_matches_skill(skill, profile_text)]

    def _rescore(self, skills: list[str], missing_skills: list[str]) -> int:
        if not skills:
            return 50
        matched_count = max(0, len(skills) - len(missing_skills))
        return round((matched_count / len(skills)) * 100)

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
        context_labels: set[str],
    ) -> float:
        evidence_count = len(required_skills) + len(preferred_skills) + len(seniority_signals) + len(authorization_evidence)
        if "Staffing/Training Placement" in context_labels and len(required_skills) + len(preferred_skills) <= 3:
            return 0.48
        if not has_clean_skill_sections and len(required_skills) + len(preferred_skills) <= 2:
            return 0.52
        if evidence_count >= 8:
            return 0.86
        if evidence_count >= 4:
            return 0.78
        return 0.64
