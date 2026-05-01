from app.services.analysis.evidence import dedupe_evidence
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

    assert dedupe_evidence(evidence) == [evidence[0], evidence[2]]
