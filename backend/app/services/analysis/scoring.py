import re

from app.services.analysis.rules import SKILL_PATTERNS, USER_SPONSORSHIP_NEED_PATTERNS


def clamp_score(value: float) -> int:
    return max(0, min(100, round(value)))


def score_skill_match(skills: list[str], profile_text: str) -> tuple[int, list[str]]:
    if not skills:
        return 100, []

    matched: list[str] = []
    missing: list[str] = []
    haystack = profile_text.lower()

    for skill in skills:
        patterns = skill_match_patterns(skill)
        if any(re.search(pattern, haystack, re.IGNORECASE) for pattern in patterns):
            matched.append(skill)
        else:
            missing.append(skill)

    return clamp_score((len(matched) / len(skills)) * 100), missing


def skill_match_patterns(skill: str) -> list[str]:
    patterns = list(SKILL_PATTERNS.get(skill, [rf"\b{re.escape(skill)}\b"]))
    if skill == "SQL":
        patterns.extend([r"\bpostgres(?:ql)?\b", r"\bmysql\b", r"\bsqlite\b"])
    if skill == "REST API":
        patterns.extend([r"\bapi(?:s)?\b", r"\bbackend\b"])
    return patterns


def score_resume_match(all_skills: list[str], profile_text: str) -> int:
    if not all_skills:
        return 60 if profile_text.strip() else 30
    score, _missing = score_skill_match(all_skills, profile_text)
    return score


def score_location(job_location: str | None, target_locations: list[str]) -> int:
    location = (job_location or "").lower()
    targets = [target.lower() for target in target_locations if target]

    if "remote" in location:
        return 100
    if not location:
        return 60
    if not targets:
        return 60
    if any(target in location or location in target for target in targets):
        return 100
    if any("remote" in target for target in targets):
        return 80
    return 35


def user_likely_needs_sponsorship(work_authorization_notes: str | None) -> bool:
    text = work_authorization_notes or ""
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in USER_SPONSORSHIP_NEED_PATTERNS)


def authorization_score(risk: str) -> int:
    if risk == "high":
        return 20
    if risk == "medium":
        return 55
    return 80


def overall_score(
    *,
    required_skill_score: int,
    preferred_skill_score: int,
    experience_fit_score: int,
    resume_match_score: int,
    location_fit_score: int,
    authorization_risk: str,
) -> int:
    return clamp_score(
        required_skill_score * 0.35
        + preferred_skill_score * 0.15
        + experience_fit_score * 0.20
        + resume_match_score * 0.15
        + location_fit_score * 0.10
        + authorization_score(authorization_risk) * 0.05
    )


def score_new_grad_fit(
    *,
    positive_signals: list[dict],
    negative_signals: list[dict],
    seniority_signals: list[dict],
) -> tuple[str, int]:
    labels = {str(signal.get("label", "")).lower() for signal in seniority_signals}
    has_strong_positive = bool(labels & {"new grad", "entry-level", "university graduate", "0-1 years", "0-2 years"})
    has_good_positive = bool(labels & {"junior", "1+ years"})
    has_mixed_requirement = bool(labels & {"2+ years"})
    has_senior_title = bool(labels & {"senior", "staff", "principal", "lead", "architect"})
    has_very_high_experience = "5+ years" in labels
    has_high_experience = "3+ years" in labels

    if has_senior_title or has_very_high_experience:
        return "not_new_grad_friendly", 15
    if has_high_experience:
        return "weak_fit", 35
    if has_strong_positive and not negative_signals:
        return "strong_fit", 90
    if has_good_positive and not negative_signals:
        return "good_fit", 78
    if has_strong_positive and negative_signals:
        return "mixed_fit", 58
    if has_mixed_requirement:
        return "mixed_fit", 55
    if positive_signals:
        return "good_fit", 72
    return "mixed_fit", 52


def recommend(
    *,
    overall: int,
    new_grad_fit_label: str,
    authorization_risk: str,
    missing_required_skills: list[str],
    user_needs_sponsorship: bool,
) -> tuple[str, str]:
    if authorization_risk == "high" and user_needs_sponsorship:
        return "skip", "The posting has explicit no-sponsorship or restricted work-authorization language, and your profile suggests future sponsorship may be needed."
    if new_grad_fit_label == "not_new_grad_friendly":
        return "skip", "The role shows senior-level or high-experience signals that are not new-grad friendly."
    if overall < 40:
        return "skip", "The match score is low after considering skills, experience fit, location, and authorization risk."
    if overall >= 78 and new_grad_fit_label in {"strong_fit", "good_fit"} and authorization_risk != "high":
        if authorization_risk in {"medium", "unknown"}:
            return "apply_with_caution", "The role is a strong job-fit match, but work authorization evidence is not clearly low risk."
        return "apply", "The role matches your profile well and appears new-grad friendly with no major authorization concern."
    if overall >= 65 and authorization_risk != "high":
        return "apply_with_caution", "The role has a workable match, but there are gaps or uncertainties worth checking before applying."
    if missing_required_skills and len(missing_required_skills) >= 3:
        return "maybe", "Several required skills appear missing, so this is worth applying only if the role is otherwise strategic."
    if new_grad_fit_label in {"mixed_fit", "weak_fit"}:
        return "maybe", "The posting has mixed new-grad signals, so the fit is plausible but not clearly strong."
    return "maybe", "The role has some useful overlap, but the evidence is not strong enough for a clear apply recommendation."
