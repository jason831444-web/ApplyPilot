from types import SimpleNamespace

from app.models.job_analysis import AuthorizationRisk, NewGradFitLabel
from app.services.resume_tailoring_service import ResumeTailoringService
from app.services.analysis.deterministic_provider import DeterministicRuleBasedProvider
from app.services.analysis.evidence import dedupe_evidence, phrase_window
from app.services.analysis.extraction import extract_experience_signals, extract_skills_by_requirement


SAMPLE_DESCRIPTION = (
    "Requirements: 0-2 years of experience, Python, React, SQL, PostgreSQL, REST API, Git. "
    "Preferred qualifications: Docker, AWS, FastAPI."
)


def test_inline_preferred_skills_are_not_required() -> None:
    required_skills, preferred_skills, _evidence = extract_skills_by_requirement(SAMPLE_DESCRIPTION)

    assert set(required_skills) == {"Python", "React", "SQL", "PostgreSQL", "REST API", "Git"}
    assert set(preferred_skills) == {"Docker", "AWS", "FastAPI"}


def test_range_experience_does_not_trigger_plus_year_signal() -> None:
    seniority_signals, _positive, _negative = extract_experience_signals(SAMPLE_DESCRIPTION)
    labels = [signal["label"] for signal in seniority_signals]

    assert labels == ["0-2 years"]
    assert "2+ years" not in labels


def test_evidence_is_deduplicated_by_type_label_source_and_text() -> None:
    evidence = [
        {"type": "skill", "label": "Python", "source": "job_description", "text": "general: Python"},
        {"type": "skill", "label": "Python", "source": "job_description", "text": "general: Python"},
        {"type": "skill", "label": "Python", "source": "job_description", "text": "Python"},
    ]

    assert dedupe_evidence(evidence) == [evidence[0]]


def make_profile() -> SimpleNamespace:
    return SimpleNamespace(
        resume_text="New grad software engineer with Python, React, FastAPI, PostgreSQL, Docker, AWS, and machine learning projects.",
        skills=["Python", "React", "FastAPI", "PostgreSQL", "Docker", "AWS", "Machine Learning"],
        projects=["AI healthcare workflow prototype", "Backend API project"],
        experience_summary="Built full-stack and backend applications.",
        target_roles=["Software Engineer", "Backend Engineer"],
        target_locations=["New York", "Remote"],
        work_authorization_notes="F-1 OPT candidate. May require future H-1B sponsorship.",
    )


def make_job(description: str) -> SimpleNamespace:
    return SimpleNamespace(
        company_name="Asha Health",
        job_title="Software Engineer, AI x Healthcare",
        location="New York",
        job_description=description,
    )


def test_empty_skill_lists_use_neutral_scores_and_no_fake_skill_strengths() -> None:
    description = "We are looking for curious builders who communicate clearly and care about users."

    result = DeterministicRuleBasedProvider().analyze(profile=make_profile(), job=make_job(description))

    assert result.required_skills == []
    assert result.preferred_skills == []
    assert result.required_skill_score == 50
    assert result.preferred_skill_score == 50
    assert "Strong coverage of required skills." not in result.strengths
    assert "Good overlap with preferred skills." not in result.strengths
    assert any("No explicit required skills were detected" in concern for concern in result.concerns)
    assert any("matching confidence is lower" in strength for strength in result.strengths)


def test_ambiguous_startup_posting_extracts_signals_and_lowers_new_grad_fit() -> None:
    description = (
        "Asha Health is hiring a backend/AI engineer to build AI agents for healthcare workflows. "
        "You will have a high degree of ownership and work in person 5 days a week. "
        "Our team works 6 days a week and expects someone who could ship a production-ready version "
        "of Instagram in 2 days. You are an insanely good product manager, designer, and backend/AI "
        "engineer all in one. Early stage startup experience is important, ideally you have built and "
        "scaled your own projects to significant revenue. Experience with AWS is helpful. "
        "You graduated with a bachelors in computer science."
    )

    result = DeterministicRuleBasedProvider().analyze(profile=make_profile(), job=make_job(description))
    extracted = set(result.required_skills + result.preferred_skills)
    domain_signals = {item["label"] for item in result.evidence if item["type"] == "domain"}
    evidence_text = " ".join(str(item.get("text", "")).lower() for item in result.evidence)
    negative_labels = {str(item.get("label", "")) for item in result.new_grad_negative_signals}

    assert {"Backend", "AWS"} <= extracted
    assert {"AI", "AI Agents", "Product Management", "Healthcare", "Startup"} <= domain_signals
    assert result.new_grad_fit_label in {"mixed_fit", "weak_fit"}
    assert result.new_grad_fit_score <= 50
    assert result.recommendation in {"apply_with_caution", "maybe"}
    assert {"high ownership", "6 days a week", "production-ready product in 2 days", "significant revenue"} <= negative_labels
    assert "ai agents" in evidence_text
    assert "backend/ai engineer" in evidence_text
    assert "high degree of ownership" in evidence_text
    assert "5 days a week" in evidence_text
    assert "6 days a week" in evidence_text
    assert "instagram in 2 days" in evidence_text
    assert "aws" in evidence_text
    assert "early stage startup" in evidence_text
    assert "significant revenue" in evidence_text


def test_evidence_snippet_uses_natural_boundaries_and_length_limit() -> None:
    text = (
        "First sentence should not appear. "
        "You will build AI agents for healthcare workflows with backend systems and AWS. "
        "A final sentence follows."
    )
    start = text.index("AI agents")
    snippet = phrase_window(text, start, start + len("AI agents"))

    assert snippet.startswith("You will build")
    assert len(snippet) <= 280
    assert not snippet[0].islower()
    assert snippet.endswith(".")


def test_similar_duplicate_domain_evidence_is_reduced() -> None:
    evidence = [
        {"type": "domain", "label": "AI", "source": "job_description", "text": "You will build AI agents for healthcare workflows."},
        {"type": "domain", "label": "AI", "source": "job_description", "text": "You will build AI agents for healthcare workflows and backend systems."},
        {"type": "domain", "label": "AI", "source": "job_description", "text": "Passion for AI in healthcare is important."},
    ]

    deduped = dedupe_evidence(evidence)

    assert len(deduped) == 2


def test_resume_tailoring_uses_natural_backend_wording() -> None:
    profile = make_profile()
    job = make_job("Backend role using AWS.")
    analysis = SimpleNamespace(
        required_skills=["Backend", "AWS"],
        preferred_skills=[],
        missing_required_skills=[],
        missing_preferred_skills=[],
        evidence=[],
        authorization_risk=AuthorizationRisk.unknown,
        new_grad_fit_label=NewGradFitLabel.mixed_fit,
    )
    service = ResumeTailoringService.__new__(ResumeTailoringService)

    result = service._generate(profile=profile, job=job, analysis=analysis)

    assert "experience in Backend" not in result.tailored_summary
    assert "backend engineering" in result.tailored_summary or "backend systems" in result.tailored_summary
