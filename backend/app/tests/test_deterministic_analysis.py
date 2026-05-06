from datetime import datetime, timezone
from types import SimpleNamespace

from app.models.job_analysis import AuthorizationRisk, NewGradFitLabel
from app.schemas.analysis import JobAnalysisRead
from app.services.resume_tailoring_service import ResumeTailoringService
from app.services.analysis.deterministic_provider import DeterministicRuleBasedProvider
from app.services.analysis.evidence import dedupe_evidence, extract_sentence_evidence, phrase_window
from app.services.analysis.extraction import extract_experience_signals, extract_skills_by_requirement


SAMPLE_DESCRIPTION = (
    "Requirements: 0-2 years of experience, Python, React, SQL, PostgreSQL, REST API, Git. "
    "Preferred qualifications: Docker, AWS, FastAPI."
)


def test_inline_preferred_skills_are_not_required() -> None:
    required_skills, preferred_skills, _evidence = extract_skills_by_requirement(SAMPLE_DESCRIPTION)

    assert set(required_skills) == {"Python", "React", "SQL", "PostgreSQL", "REST API", "Git"}
    assert set(preferred_skills) == {"Docker", "AWS", "FastAPI"}


def test_benefits_healthcare_text_does_not_create_domain_signal() -> None:
    description = (
        "About the Role: Build backend services for customer workflows. "
        "What We Offer: Top-notch healthcare coverage, medical, dental, vision."
    )

    result = DeterministicRuleBasedProvider().analyze(profile=make_profile(), job=make_job(description))
    domain_signals = {item["label"] for item in result.evidence if item["type"] == "domain"}

    assert "Healthcare" not in domain_signals


def test_healthcare_product_context_creates_domain_signal() -> None:
    description = "About the Role: Build healthcare workflows for clinics and providers."

    result = DeterministicRuleBasedProvider().analyze(profile=make_profile(), job=make_job(description))
    domain_signals = {item["label"] for item in result.evidence if item["type"] == "domain"}

    assert "Healthcare" in domain_signals


def test_backend_systems_posting_extracts_specific_backend_signals_without_node_false_positive() -> None:
    description = (
        "What You'll Do: Design scalable backend services using Go and C++. "
        "Distributed systems, API design, observability, and production debugging. "
        "We believe in the power of single node databases."
    )

    result = DeterministicRuleBasedProvider().analyze(profile=make_profile(), job=make_job(description))
    extracted = set(result.required_skills + result.preferred_skills)

    assert {
        "Go",
        "C++",
        "Distributed Systems",
        "API Design",
        "Observability",
        "Production Debugging",
        "Backend Systems",
    } <= extracted
    assert "Node.js" not in extracted


def test_explicit_nodejs_api_extracts_nodejs() -> None:
    description = "Requirements: Build a Node.js API with PostgreSQL."

    required_skills, _preferred_skills, _evidence = extract_skills_by_requirement(description)

    assert "Node.js" in required_skills


def test_senior_high_ownership_role_generates_concerns() -> None:
    description = (
        "About the Role: Small, senior team. High ownership. Work directly with CTO. "
        "Requirements: API design, event-driven systems, async processing, MongoDB, CI/CD."
    )

    result = DeterministicRuleBasedProvider().analyze(profile=make_profile(), job=make_job(description))
    concern_text = " ".join(result.concerns).lower()

    assert result.new_grad_fit_label in {"not_new_grad_friendly", "weak_fit"}
    assert result.concerns
    assert "senior-level or high-experience signals" in concern_text
    assert "seniority, ownership, or high-agency expectations" in concern_text
    assert "missing technical skills detected" in concern_text
    assert "api design" in concern_text
    assert "event-driven systems" in concern_text
    assert "async processing" in concern_text
    assert "mongodb" in concern_text
    assert "ci/cd" in concern_text
    assert "work authorization requirements are unclear" in concern_text


def test_job_analysis_read_exposes_concerns() -> None:
    now = datetime.now(timezone.utc)
    analysis = SimpleNamespace(
        id=1,
        job_id=2,
        user_id=3,
        parsed_title="Backend Engineer",
        parsed_company="Example",
        parsed_locations=[],
        employment_type=None,
        seniority_signals=[],
        required_skills=[],
        preferred_skills=[],
        experience_requirements=[],
        overall_score=20,
        new_grad_fit_score=15,
        resume_match_score=20,
        required_skill_score=20,
        preferred_skill_score=20,
        experience_fit_score=15,
        location_fit_score=60,
        new_grad_fit_label="not_new_grad_friendly",
        authorization_risk="unknown",
        recommendation="skip",
        recommendation_reason="Not new-grad friendly.",
        summary="Summary",
        strengths=[],
        concerns=["This role shows senior-level or high-experience signals that may not be new-grad friendly."],
        missing_required_skills=[],
        missing_preferred_skills=[],
        new_grad_positive_signals=[],
        new_grad_negative_signals=[],
        authorization_evidence=[],
        evidence=[],
        next_actions=[],
        analysis_provider="deterministic_rule_based",
        analysis_confidence=0.8,
        fallback_used=False,
        created_at=now,
        updated_at=now,
    )

    result = JobAnalysisRead.model_validate(analysis)

    assert result.concerns == analysis.concerns


def test_data_annotation_style_alternative_language_list_and_platform_signals() -> None:
    description = (
        "Remote coding tasks for AI models with a flexible schedule. Choose projects and receive hourly pay "
        "through PayPal after assessment-based onboarding. Paid work becomes available through the platform, "
        "availability may be limited by country, and some people fit this work alongside a full-time role. "
        "Requirements: proficiency in at least one of JavaScript, TypeScript, Python, C++, React, Go, Java. "
        "Preferred qualifications: Kotlin and Android development."
    )

    result = DeterministicRuleBasedProvider().analyze(profile=make_profile(), job=make_job(description))
    extracted = set(result.required_skills + result.preferred_skills)
    domain_signals = {item["label"] for item in result.evidence if item["type"] == "domain"}

    assert {"Kotlin", "Android Development"} <= extracted
    assert "Python" in result.required_skills
    assert "React" in result.required_skills
    assert "C++" not in result.missing_required_skills
    assert "Go" not in result.missing_required_skills
    assert "Java" not in result.missing_required_skills
    strengths_text = " ".join(result.strengths)
    assert "Python" in strengths_text
    assert "React" in strengths_text
    assert "C++" not in strengths_text
    assert "Go" not in strengths_text
    assert "Nontraditional Work" in domain_signals
    assert any("platform-based or gig-like" in concern for concern in result.concerns)


def test_alternative_group_unmatched_options_are_not_matched_strengths_or_required_missing() -> None:
    profile = make_profile()
    profile.resume_text = f"{profile.resume_text} JavaScript TypeScript Java."
    profile.skills = [*profile.skills, "JavaScript", "TypeScript", "Java"]
    description = "Requirements: proficiency in at least one of JavaScript, TypeScript, Python, C++, React, Go, Java."

    result = DeterministicRuleBasedProvider().analyze(profile=profile, job=make_job(description))
    strengths_text = " ".join(result.strengths)

    assert "C++" not in result.missing_required_skills
    assert "Go" not in result.missing_required_skills
    assert "C++" not in strengths_text
    assert "Go" not in strengths_text
    assert "JavaScript" in strengths_text
    assert "TypeScript" in strengths_text
    assert "Java" in strengths_text


def test_junior_python_role_ignores_senior_collaboration_context_and_extracts_data_skills() -> None:
    job = SimpleNamespace(
        company_name="Example Health",
        job_title="Python Programmer - Junior",
        location="Remote",
        job_description=(
            "We seek a motivated Junior Python Programmer eager to learn in a mentorship environment. "
            "You will collaborate with senior developers and assist in designing data tools. "
            "Requirements: 2+ years professional Python experience, PySpark, Pandas, NumPy, Polars, "
            "Snowflake, NoSQL, Agile, Scrum, JIRA, unit testing, integration testing, test automation, "
            "HIPAA, and healthcare compliance. Bachelor's degree completed or in progress. "
            "Preferred qualifications: AWS, Azure."
        ),
    )

    result = DeterministicRuleBasedProvider().analyze(profile=make_profile(), job=job)
    extracted = set(result.required_skills + result.preferred_skills)
    negative_labels = {str(signal.get("label", "")) for signal in result.new_grad_negative_signals}
    positive_labels = {str(signal.get("label", "")) for signal in result.new_grad_positive_signals}

    assert "senior" not in negative_labels
    assert {"junior", "eager to learn", "mentorship"} <= positive_labels
    assert result.new_grad_fit_label != "not_new_grad_friendly"
    assert result.recommendation != "skip"
    assert {
        "PySpark",
        "Pandas",
        "NumPy",
        "Polars",
        "Snowflake",
        "NoSQL",
        "Agile",
        "JIRA",
        "Unit Testing",
        "Integration Testing",
        "HIPAA",
        "Healthcare Compliance",
    } <= extracted
    assert "AWS" in result.preferred_skills
    assert "Azure" in result.preferred_skills
    assert "AWS" not in result.missing_required_skills
    assert "Azure" not in result.missing_required_skills


def test_senior_collaboration_context_is_not_negative_or_ownership_concern() -> None:
    description = "Collaborate with senior developers and other team members. Requirements: Python."

    result = DeterministicRuleBasedProvider().analyze(profile=make_profile(), job=make_job(description))
    negative_labels = {str(signal.get("label", "")) for signal in result.new_grad_negative_signals}
    concern_text = " ".join(result.concerns).lower()

    assert "senior" not in negative_labels
    assert "senior team" not in negative_labels
    assert "ownership" not in concern_text


def test_preferred_cloud_skills_are_not_required_missing() -> None:
    description = "Requirements: Python. Preferred Qualifications: AWS, Azure."

    result = DeterministicRuleBasedProvider().analyze(profile=make_profile(), job=make_job(description))

    assert "AWS" in result.preferred_skills
    assert "Azure" in result.preferred_skills
    assert "AWS" not in result.required_skills
    assert "Azure" not in result.required_skills
    assert "AWS" not in result.missing_required_skills
    assert "Azure" not in result.missing_required_skills


def test_forward_deployed_role_avoids_leading_venture_false_positive_and_extracts_context() -> None:
    description = (
        "Forward Deployed Engineering role backed by leading venture capital firms. "
        "You will mentor junior teammates, lead scoped engagements, independently own customer-facing engineering work, "
        "and build quantitative modeling, forecasting, optimization, LLM workflows, and data pipelines. "
        "Requirements: 1-4 years of experience."
    )

    result = DeterministicRuleBasedProvider().analyze(profile=make_profile(), job=make_job(description))
    extracted = set(result.required_skills + result.preferred_skills)
    negative_labels = {str(signal.get("label", "")) for signal in result.new_grad_negative_signals}
    positive_labels = {str(signal.get("label", "")) for signal in result.new_grad_positive_signals}

    assert "lead" in negative_labels
    assert not any("leading venture capital firms" in str(signal.get("text", "")).lower() for signal in result.new_grad_negative_signals)
    assert "junior" not in positive_labels
    assert "mentor junior teammates" in negative_labels
    assert {
        "Forward Deployed Engineering",
        "Customer-Facing Engineering",
        "Quantitative Modeling",
        "Forecasting",
        "Optimization",
        "LLM Workflows",
        "Data Pipelines",
    } <= extracted
    assert result.new_grad_fit_label in {"mixed_fit", "weak_fit"}


def test_staffing_training_role_caps_sparse_generic_score_and_ignores_generic_performance() -> None:
    profile = make_profile()
    profile.skills = [*profile.skills, "Java"]
    profile.resume_text = f"{profile.resume_text} Java applications."
    description = (
        "Java Developer role for OPT/CPT candidates. We provide pre-job training with assignments and case studies "
        "during training, mock sessions before interviews, and multiple interview rounds with different clients. "
        "After joining a client project, visa sponsorship may be discussed. Build generic applications with good "
        "performance and support client project delivery."
    )

    result = DeterministicRuleBasedProvider().analyze(profile=profile, job=make_job(description))
    extracted = set(result.required_skills + result.preferred_skills)
    domain_signals = {item["label"] for item in result.evidence if item["type"] == "domain"}

    assert "Staffing/Training Placement" in domain_signals
    assert "Performance" not in extracted
    assert result.overall_score <= 58
    assert result.analysis_confidence <= 0.52
    assert any("staffing, training, or client-placement" in concern for concern in result.concerns)


def test_concern_deduplication_prefers_concise_unique_messages() -> None:
    provider = DeterministicRuleBasedProvider()

    concerns = provider._dedupe_concerns(
        [
            "Missing required skills: Python.",
            "Missing technical skills detected: Python.",
            "No clear sponsorship or work authorization evidence was found.",
            "Work authorization requirements are unclear from the job posting.",
            "Only limited structured technical requirements were detected, so match confidence is lower.",
            "Only limited structured technical requirements were detected, so match confidence is lower.",
            "Startup intensity and ownership expectations may raise the bar for this role: high ownership.",
            "Startup intensity and ownership expectations may raise the bar for this role: high ownership.",
        ]
    )

    assert "Missing technical skills detected: Python." in concerns
    assert "Work authorization requirements are unclear from the job posting." in concerns
    assert len([concern for concern in concerns if "limited structured technical requirements" in concern]) == 1
    assert len([concern for concern in concerns if "ownership expectations" in concern]) == 1
    assert not any(concern.startswith("Missing required skills") for concern in concerns)
    assert not any(concern.startswith("No clear sponsorship") for concern in concerns)


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
    assert any("limited structured technical requirements" in concern for concern in result.concerns)
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


ASHA_SAMPLE_TEXT = """
About The Role
We are building AI agents for healthcare workflows. But we're still small enough that we're looking for all rounders that take a high degree of ownership.

Who Should Apply
The role is in person 5 days a week, most of the team works 6 days a week. :)

Who Should Not Apply
If you are not super confident in your engineering & product skills, for example if we asked you to build a production-ready version of Instagram in 2 days and that sounds difficult, hit that X button.
"""


def test_asha_evidence_sentence_excerpts_are_not_mid_word_fragments() -> None:
    high_ownership = extract_sentence_evidence(ASHA_SAMPLE_TEXT, "high degree of ownership")
    in_person = extract_sentence_evidence(ASHA_SAMPLE_TEXT, "5 days a week")
    six_days = extract_sentence_evidence(ASHA_SAMPLE_TEXT, "6 days a week")
    production_ready = extract_sentence_evidence(ASHA_SAMPLE_TEXT, "production-ready version of Instagram in 2 days")
    snippets = [high_ownership, in_person, six_days, production_ready]

    assert high_ownership.startswith("But we're still small enough")
    assert in_person.startswith("The role is in person")
    assert not six_days.startswith("le :)")
    assert production_ready.startswith("If you are not super confident")
    assert not production_ready.startswith("er confident")
    assert all(len(snippet) <= 300 for snippet in snippets)
    assert all(not snippet[0].islower() for snippet in snippets)


def test_sparse_technical_startup_posting_caps_match_scores() -> None:
    description = (
        "Asha Health is hiring a backend/AI engineer to build AI agents for healthcare workflows. "
        "But we're still small enough that we're looking for all rounders that take a high degree of ownership. "
        "The role is in person 5 days a week, most of the team works 6 days a week. "
        "If you are not super confident in your engineering & product skills, for example if we asked you "
        "to build a production-ready version of Instagram in 2 days and that sounds difficult, hit that X button. "
        "Early stage startup experience is important."
    )

    result = DeterministicRuleBasedProvider().analyze(profile=make_profile(), job=make_job(description))

    assert result.required_skills == ["Backend"]
    assert result.required_skill_score < 100
    assert result.required_skill_score <= 70
    assert result.resume_match_score < 100
    assert result.resume_match_score <= 65
    assert result.overall_score < 60
    assert result.new_grad_fit_label == "weak_fit"
    assert result.authorization_risk == "unknown"
    assert "Strong coverage of required skills." not in result.strengths
    assert any("limited structured technical requirements" in concern for concern in result.concerns)
    assert any("typical new-grad expectations" in concern for concern in result.concerns)
    assert any("Startup intensity and ownership expectations" in concern for concern in result.concerns)
    assert any("Work authorization requirements are unclear" in concern for concern in result.concerns)
    assert len(result.concerns) >= 4
