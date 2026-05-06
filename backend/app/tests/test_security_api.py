from datetime import timedelta
import csv
from io import BytesIO, StringIO
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app


client = TestClient(app)


def unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def register_and_login(prefix: str = "security") -> str:
    email = unique_email(prefix)
    password = "password123"
    register_response = client.post(
        "/api/auth/register",
        json={"full_name": "Security User", "email": email, "password": password},
    )
    assert register_response.status_code == 201

    login_response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def make_text_pdf(text: str) -> bytes:
    escaped_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 720 Td ({escaped_text}) Tj ET".encode()
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        f"5 0 obj << /Length {len(stream)} >> stream\n".encode() + stream + b"\nendstream endobj\n",
    ]
    output = BytesIO()
    output.write(b"%PDF-1.4\n")
    offsets: list[int] = []
    for obj in objects:
        offsets.append(output.tell())
        output.write(obj)
    xref_position = output.tell()
    output.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets:
        output.write(f"{offset:010d} 00000 n \n".encode())
    output.write(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_position}\n%%EOF".encode())
    return output.getvalue()


def create_job(token: str) -> int:
    response = client.post(
        "/api/jobs",
        headers=auth_headers(token),
        json={
            "company_name": "Security Corp",
            "job_title": "Software Engineer",
            "location": "Remote",
            "job_description": "Requirements: Python, React, SQL, PostgreSQL, REST API, Git. Preferred: Docker.",
            "source_url": None,
            "source_type": "manual",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_analyzed_job(token: str) -> tuple[int, int]:
    response = client.post(
        "/api/jobs/analyze-new",
        headers=auth_headers(token),
        json={
            "company_name": "Analysis Corp",
            "job_title": "Software Engineer I",
            "location": "Remote",
            "job_description": (
                "Requirements: 0-2 years of experience, Python, React, SQL, PostgreSQL, REST API, Git. "
                "Preferred qualifications: Docker, AWS, FastAPI."
            ),
            "source_url": None,
            "source_type": "manual",
        },
    )
    assert response.status_code == 201
    data = response.json()
    return data["job"]["id"], data["application"]["id"]


def update_profile_for_tailoring(token: str) -> None:
    response = client.put(
        "/api/profile/me",
        headers=auth_headers(token),
        json={
            "resume_text": "Computer Science new grad with React, Next.js, Python, FastAPI, PostgreSQL, Docker, AWS, and machine learning experience.",
            "skills": ["React", "Next.js", "Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "REST API"],
            "projects": ["ApplyPilot job-fit decision engine", "DocuParse OCR document parser"],
            "experience_summary": "Built backend APIs, dashboards, OCR workflows, and production-minded full-stack projects.",
            "target_roles": ["Software Engineer", "Backend Engineer"],
            "target_locations": ["Remote", "New York"],
            "graduation_date": "2026-05-20",
            "work_authorization_notes": "F-1 OPT candidate. May require future H-1B sponsorship.",
        },
    )
    assert response.status_code == 200


def test_protected_routes_require_auth() -> None:
    for path in ["/api/profile/me", "/api/jobs", "/api/applications", "/api/dashboard/summary"]:
        response = client.get(path)
        assert response.status_code == 401


def test_invalid_and_expired_tokens_return_401() -> None:
    invalid_response = client.get("/api/auth/me", headers=auth_headers("not-a-token"))
    assert invalid_response.status_code == 401

    expired_token = create_access_token(subject="1", expires_delta=timedelta(minutes=-1))
    expired_response = client.get("/api/auth/me", headers=auth_headers(expired_token))
    assert expired_response.status_code == 401


def test_user_cannot_access_another_users_job() -> None:
    owner_token = register_and_login("job-owner")
    other_token = register_and_login("job-other")
    job_id = create_job(owner_token)

    response = client.get(f"/api/jobs/{job_id}", headers=auth_headers(other_token))

    assert response.status_code == 404


def test_user_cannot_access_another_users_application() -> None:
    owner_token = register_and_login("app-owner")
    other_token = register_and_login("app-other")
    job_id = create_job(owner_token)
    create_response = client.post(
        "/api/applications",
        headers=auth_headers(owner_token),
        json={"job_id": job_id, "status": "saved"},
    )
    assert create_response.status_code == 201
    application_id = create_response.json()["id"]

    read_response = client.get(f"/api/applications/{application_id}", headers=auth_headers(other_token))
    patch_response = client.patch(
        f"/api/applications/{application_id}",
        headers=auth_headers(other_token),
        json={"status": "applied"},
    )

    assert read_response.status_code == 404
    assert patch_response.status_code == 404


def test_validation_rejects_overly_long_job_description() -> None:
    token = register_and_login("long-job")
    response = client.post(
        "/api/jobs",
        headers=auth_headers(token),
        json={
            "company_name": "Long Corp",
            "job_title": "Software Engineer",
            "location": "Remote",
            "job_description": "x" * 50001,
            "source_url": None,
            "source_type": "manual",
        },
    )

    assert response.status_code == 422


def test_validation_rejects_invalid_application_status() -> None:
    token = register_and_login("bad-status")
    job_id = create_job(token)
    response = client.post(
        "/api/applications",
        headers=auth_headers(token),
        json={"job_id": job_id, "status": "not_a_status"},
    )

    assert response.status_code == 422


def test_bulk_delete_requires_auth() -> None:
    jobs_response = client.request("DELETE", "/api/jobs/bulk", json={"job_ids": [1]})
    applications_response = client.request("DELETE", "/api/applications/bulk", json={"application_ids": [1]})

    assert jobs_response.status_code == 401
    assert applications_response.status_code == 401


def test_user_can_bulk_delete_own_jobs_and_related_records() -> None:
    token = register_and_login("bulk-job-owner")
    job_id, application_id = create_analyzed_job(token)

    response = client.request("DELETE", "/api/jobs/bulk", headers=auth_headers(token), json={"job_ids": [job_id]})

    assert response.status_code == 200
    assert response.json() == {"deleted_count": 1}
    assert client.get(f"/api/jobs/{job_id}", headers=auth_headers(token)).status_code == 404
    assert client.get(f"/api/applications/{application_id}", headers=auth_headers(token)).status_code == 404
    assert client.get(f"/api/jobs/{job_id}/analysis", headers=auth_headers(token)).status_code == 404


def test_user_cannot_bulk_delete_another_users_jobs() -> None:
    owner_token = register_and_login("bulk-job-owner-scope")
    other_token = register_and_login("bulk-job-other-scope")
    job_id = create_job(owner_token)

    response = client.request("DELETE", "/api/jobs/bulk", headers=auth_headers(other_token), json={"job_ids": [job_id]})

    assert response.status_code == 200
    assert response.json() == {"deleted_count": 0}
    assert client.get(f"/api/jobs/{job_id}", headers=auth_headers(owner_token)).status_code == 200


def test_reanalyze_all_requires_auth() -> None:
    response = client.post("/api/jobs/reanalyze-all")

    assert response.status_code == 401


def test_reanalyze_all_only_processes_current_users_jobs() -> None:
    owner_token = register_and_login("reanalyze-owner")
    other_token = register_and_login("reanalyze-other")
    owner_job_id = create_job(owner_token)
    other_job_id = create_job(other_token)

    response = client.post("/api/jobs/reanalyze-all", headers=auth_headers(owner_token))

    assert response.status_code == 200
    assert response.json() == {"reanalyzed_count": 1, "failed_count": 0}
    assert client.get(f"/api/jobs/{owner_job_id}/analysis", headers=auth_headers(owner_token)).status_code == 200
    assert client.get(f"/api/jobs/{other_job_id}/analysis", headers=auth_headers(other_token)).status_code == 404


def test_reanalyze_all_updates_existing_analyses() -> None:
    token = register_and_login("reanalyze-update")
    job_id, _application_id = create_analyzed_job(token)
    initial_response = client.get(f"/api/jobs/{job_id}/analysis", headers=auth_headers(token))
    assert initial_response.status_code == 200
    initial_analysis = initial_response.json()
    assert "Docker" in initial_analysis["missing_preferred_skills"]

    update_profile_for_tailoring(token)
    response = client.post("/api/jobs/reanalyze-all", headers=auth_headers(token))
    updated_response = client.get(f"/api/jobs/{job_id}/analysis", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json() == {"reanalyzed_count": 1, "failed_count": 0}
    assert updated_response.status_code == 200
    updated_analysis = updated_response.json()
    assert updated_analysis["id"] == initial_analysis["id"]
    assert updated_analysis["resume_match_score"] > initial_analysis["resume_match_score"]
    assert "Docker" not in updated_analysis["missing_preferred_skills"]


def test_reanalyze_all_creates_missing_analyses() -> None:
    token = register_and_login("reanalyze-create")
    job_id = create_job(token)
    assert client.get(f"/api/jobs/{job_id}/analysis", headers=auth_headers(token)).status_code == 404

    response = client.post("/api/jobs/reanalyze-all", headers=auth_headers(token))
    analysis_response = client.get(f"/api/jobs/{job_id}/analysis", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json() == {"reanalyzed_count": 1, "failed_count": 0}
    assert analysis_response.status_code == 200
    assert analysis_response.json()["job_id"] == job_id


def test_reanalyze_all_returns_zero_when_user_has_no_jobs() -> None:
    token = register_and_login("reanalyze-empty")

    response = client.post("/api/jobs/reanalyze-all", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json() == {"reanalyzed_count": 0, "failed_count": 0}


def test_user_can_bulk_delete_own_applications_without_deleting_jobs() -> None:
    token = register_and_login("bulk-application-owner")
    job_id = create_job(token)
    create_response = client.post(
        "/api/applications",
        headers=auth_headers(token),
        json={"job_id": job_id, "status": "saved"},
    )
    assert create_response.status_code == 201
    application_id = create_response.json()["id"]

    response = client.request(
        "DELETE",
        "/api/applications/bulk",
        headers=auth_headers(token),
        json={"application_ids": [application_id]},
    )

    assert response.status_code == 200
    assert response.json() == {"deleted_count": 1}
    assert client.get(f"/api/applications/{application_id}", headers=auth_headers(token)).status_code == 404
    assert client.get(f"/api/jobs/{job_id}", headers=auth_headers(token)).status_code == 200


def test_user_cannot_bulk_delete_another_users_applications() -> None:
    owner_token = register_and_login("bulk-application-owner-scope")
    other_token = register_and_login("bulk-application-other-scope")
    job_id = create_job(owner_token)
    create_response = client.post(
        "/api/applications",
        headers=auth_headers(owner_token),
        json={"job_id": job_id, "status": "saved"},
    )
    assert create_response.status_code == 201
    application_id = create_response.json()["id"]

    response = client.request(
        "DELETE",
        "/api/applications/bulk",
        headers=auth_headers(other_token),
        json={"application_ids": [application_id]},
    )

    assert response.status_code == 200
    assert response.json() == {"deleted_count": 0}
    assert client.get(f"/api/applications/{application_id}", headers=auth_headers(owner_token)).status_code == 200


def test_bulk_delete_rejects_empty_id_lists() -> None:
    token = register_and_login("bulk-empty")

    jobs_response = client.request("DELETE", "/api/jobs/bulk", headers=auth_headers(token), json={"job_ids": []})
    applications_response = client.request(
        "DELETE",
        "/api/applications/bulk",
        headers=auth_headers(token),
        json={"application_ids": []},
    )

    assert jobs_response.status_code == 422
    assert applications_response.status_code == 422


def test_resume_tailoring_requires_auth() -> None:
    response = client.get("/api/jobs/1/resume-tailoring")

    assert response.status_code == 401


def test_resume_tailoring_returns_404_without_analysis() -> None:
    token = register_and_login("tailoring-no-analysis")
    job_id = create_job(token)

    response = client.get(f"/api/jobs/{job_id}/resume-tailoring", headers=auth_headers(token))

    assert response.status_code == 404
    assert response.json()["detail"] == "Run job analysis before generating resume tailoring suggestions."


def test_user_cannot_access_another_users_resume_tailoring() -> None:
    owner_token = register_and_login("tailoring-owner")
    other_token = register_and_login("tailoring-other")
    update_profile_for_tailoring(owner_token)
    job_id, _application_id = create_analyzed_job(owner_token)

    response = client.get(f"/api/jobs/{job_id}/resume-tailoring", headers=auth_headers(other_token))

    assert response.status_code == 404


def test_resume_tailoring_uses_matched_skills_and_cautions_without_claiming_missing_skills() -> None:
    token = register_and_login("tailoring-match")
    update_profile_for_tailoring(token)
    response = client.post(
        "/api/jobs/analyze-new",
        headers=auth_headers(token),
        json={
            "company_name": "Tailor Corp",
            "job_title": "Backend Software Engineer",
            "location": "Remote",
            "job_description": (
                "Requirements: Python, FastAPI, PostgreSQL, REST API, Docker, Kubernetes. "
                "Preferred qualifications: AWS, React. Must be comfortable with high degree of ownership."
            ),
            "source_url": None,
            "source_type": "manual",
        },
    )
    assert response.status_code == 201
    job_id = response.json()["job"]["id"]

    tailoring_response = client.get(f"/api/jobs/{job_id}/resume-tailoring", headers=auth_headers(token))

    assert tailoring_response.status_code == 200
    data = tailoring_response.json()
    bullet_text = " ".join(data["bullet_suggestions"]).lower()
    caution_text = " ".join(data["cautions"]).lower()
    assert "Python" in data["skills_to_emphasize"]
    assert "FastAPI" in data["skills_to_emphasize"]
    assert "Kubernetes" in data["keywords_to_add"]
    assert "kubernetes" not in bullet_text
    assert "do not claim" in caution_text
    assert "work authorization" in caution_text or "sponsorship" in caution_text


def test_analysis_concerns_survive_persist_and_readback() -> None:
    token = register_and_login("analysis-concerns")
    update_profile_for_tailoring(token)
    response = client.post(
        "/api/jobs/analyze-new",
        headers=auth_headers(token),
        json={
            "company_name": "Concern Corp",
            "job_title": "Founding Engineer",
            "location": "New York",
            "job_description": (
                "About the Role: Small, senior team. High ownership. Work directly with CTO. "
                "Requirements: API design, event-driven systems, async processing, MongoDB, CI/CD."
            ),
            "source_url": None,
            "source_type": "manual",
        },
    )
    assert response.status_code == 201
    data = response.json()
    job_id = data["job"]["id"]
    created_concerns = data["analysis"]["concerns"]

    read_response = client.get(f"/api/jobs/{job_id}/analysis", headers=auth_headers(token))

    assert read_response.status_code == 200
    read_concerns = read_response.json()["concerns"]
    assert created_concerns == read_concerns
    assert any("senior-level or high-experience signals" in concern for concern in read_concerns)
    assert any("seniority, ownership, or high-agency expectations" in concern for concern in read_concerns)
    assert any("Missing technical skills detected: API Design, Event-driven Systems, Async Processing, MongoDB, CI/CD." == concern for concern in read_concerns)
    assert any("Work authorization requirements are unclear" in concern for concern in read_concerns)


def test_analyze_new_preserves_required_and_preferred_missing_skill_split() -> None:
    token = register_and_login("analysis-skill-split")
    response = client.put(
        "/api/profile/me",
        headers=auth_headers(token),
        json={
            "resume_text": "Python SQL Git Docker",
            "skills": ["Python", "SQL", "Git", "Docker"],
            "projects": [],
            "experience_summary": "",
            "target_roles": [],
            "target_locations": [],
            "graduation_date": None,
            "work_authorization_notes": "",
        },
    )
    assert response.status_code == 200

    analyze_response = client.post(
        "/api/jobs/analyze-new",
        headers=auth_headers(token),
        json={
            "company_name": "Split Corp",
            "job_title": "Junior Data Programmer",
            "location": "Remote",
            "job_description": (
                "MINIMUM QUALIFICATIONS:\n"
                "Python, SQL, Git.\n\n"
                "PREFERRED QUALIFICATIONS:\n"
                "Knowledge of containerization tools (e.g., Docker) and cloud environments "
                "(AWS, Azure, or other providers)."
            ),
            "source_url": None,
            "source_type": "manual",
        },
    )

    assert analyze_response.status_code == 201
    analysis = analyze_response.json()["analysis"]
    assert {"Python", "SQL", "Git"} <= set(analysis["required_skills"])
    assert {"Docker", "AWS", "Azure"} <= set(analysis["preferred_skills"])
    assert "AWS" not in analysis["missing_required_skills"]
    assert "Azure" not in analysis["missing_required_skills"]
    assert "AWS" not in analysis["missing_technical_skills"]
    assert "Azure" not in analysis["missing_technical_skills"]
    assert {"AWS", "Azure"} <= set(analysis["missing_preferred_technical_skills"])
    assert {"AWS", "Azure"} <= set(analysis["keywords_to_consider"])


def test_application_csv_export_requires_auth() -> None:
    response = client.get("/api/applications/export.csv")

    assert response.status_code == 401


def test_application_csv_export_is_user_scoped_and_includes_analysis_columns() -> None:
    owner_token = register_and_login("csv-owner")
    other_token = register_and_login("csv-other")
    update_profile_for_tailoring(owner_token)
    owner_job_id, owner_application_id = create_analyzed_job(owner_token)
    other_job_id = create_job(other_token)
    other_application_response = client.post(
        "/api/applications",
        headers=auth_headers(other_token),
        json={"job_id": other_job_id, "status": "saved"},
    )
    assert other_application_response.status_code == 201

    response = client.get("/api/applications/export.csv", headers=auth_headers(owner_token))

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "applypilot_applications.csv" in response.headers["content-disposition"]
    rows = list(csv.DictReader(StringIO(response.text)))
    assert len(rows) == 1
    assert rows[0]["application_id"] == str(owner_application_id)
    assert rows[0]["job_id"] == str(owner_job_id)
    assert rows[0]["company_name"] == "Analysis Corp"
    assert "recommendation" in rows[0]
    assert rows[0]["overall_score"]
    assert rows[0]["new_grad_fit_label"]
    assert rows[0]["authorization_risk"]


def test_resume_upload_requires_file() -> None:
    token = register_and_login("resume-file-required")

    response = client.post("/api/profile/upload-resume", headers=auth_headers(token))

    assert response.status_code == 422


def test_resume_upload_rejects_non_pdf() -> None:
    token = register_and_login("resume-non-pdf")

    response = client.post(
        "/api/profile/upload-resume",
        headers=auth_headers(token),
        files={"file": ("resume.txt", b"Python React FastAPI", "text/plain")},
    )

    assert response.status_code == 400


def test_resume_upload_extracts_pdf_text_and_suggestions() -> None:
    token = register_and_login("resume-pdf")
    pdf = make_text_pdf(
        "Computer Science new grad. Built ApplyPilot using Python, React, FastAPI, PostgreSQL, and Docker. "
        "Developed DocuParse OCR parser with machine learning workflows."
    )

    response = client.post(
        "/api/profile/upload-resume",
        headers=auth_headers(token),
        files={"file": ("resume.pdf", pdf, "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()
    assert "Built ApplyPilot" in data["resume_text"]
    assert {"Python", "React", "FastAPI", "PostgreSQL", "Docker"} <= set(data["skills_suggestions"])
    assert "ApplyPilot" in data["projects_suggestions"]
    assert data["experience_summary_suggestion"]


def test_resume_import_section_parser_extracts_clean_projects_and_technical_skills() -> None:
    from app.services.resume_import_service import (
        build_experience_summary,
        extract_project_names,
        extract_skills_from_technical_skills_section,
        normalize_resume_text,
    )

    resume_text = """
    Jae Yoon
    jae@example.com | github.com/example | linkedin.com/in/example

    E DUCATION
    Rutgers University, B.S. Computer Science
    Relevant Coursework:
    Data Structures, Foundations of Computer Science, Programming
    Abstractions,
    Systems
    Fundamentals
    I
    &
    II,
    Software
    Development

    WORK EXPERIENCE & PROJECTS
    Teaching Assistant | Rutgers University
    - Helped students debug Java and Python assignments

    PROJECTS
    DocuParse – AI-Powered Document Understanding System | FastAPI, Next.js, PostgreSQL, Docker
    - a multi-stage processing pipeline for document parsing workflows.
    Smart Seat & Facility Congestion Analysis System | Python, Computer Vision
    - product-facing features for facility congestion analysis.
    ApplyPilot – Rule-Based Job-Fit Evaluation Platform | FastAPI, React, PostgreSQL
    - backend persistence and job saving for analyzed applications.
    Student Academic Management System (SAM) | Spring Boot, MySQL, React, GitHub Actions
    - developed academic management workflows.
    CNN vs. SNN Image Classification Comparison | Python, NumPy, PyTorch, Matplotlib
    - and tested a 3-layer Spiking Neural Network.

    TECHNICAL SKILLS
    Technical Languages: C, Java, Python, HTML, CSS, JavaScript, SQL
    Frameworks: React, Next.js, Node.js, Express.js, Spring Boot, FastAPI, REST API
    Databases: MySQL, PostgreSQL
    Tools: Git, GitHub, Docker, Linux, Visual Studio Code, Microsoft Excel
    Languages: Korean, English
    """

    normalized = normalize_resume_text(resume_text)
    skills = extract_skills_from_technical_skills_section(normalized)
    projects = extract_project_names(normalized)
    summary = build_experience_summary(normalized, skills, projects)

    assert len(summary) <= 600
    assert "Systems\nFundamentals\nI\n&\nII" not in normalized
    assert "Systems Fundamentals I & II, Software Development" in normalized
    assert "DocuParse – AI-Powered Document Understanding System" in projects
    assert "Smart Seat & Facility Congestion Analysis System" in projects
    assert "ApplyPilot – Rule-Based Job-Fit Evaluation Platform" in projects
    assert "Student Academic Management System (SAM)" in projects
    assert "CNN vs. SNN Image Classification Comparison" in projects
    assert not any("jae@example.com" in project.lower() for project in projects)
    assert not any("Rutgers University" in project for project in projects)
    assert not any("and tested a 3-layer Spiking Neural Network" in project for project in projects)
    assert not any("a multi-stage processing pipeline" in project for project in projects)
    assert not any("product-facing features" in project for project in projects)
    assert not any("backend persistence" in project for project in projects)
    assert not any("job saving" in project for project in projects)
    assert "and tested a 3-layer Spiking Neural Network" not in summary
    assert "a multi-stage processing pipeline" not in summary
    assert {"React", "Next.js", "FastAPI", "PostgreSQL", "Docker"} <= set(skills)
    assert "Korean" not in skills
    assert "English" not in skills


def test_resume_import_handles_inline_projects_heading_and_rejects_fragments() -> None:
    from app.services.resume_import_service import (
        build_experience_summary,
        extract_project_names,
        extract_skills_from_technical_skills_section,
        normalize_resume_text,
    )

    resume_text = """
    PROJECTS DocuParse – AI-Powered Document Understanding System | FastAPI, Next.js, PostgreSQL,
    Docker
    - a multi-stage processing pipeline for OCR and document parsing.
    AI inference with fallback routing across multiple document formats
    Smart Seat & Facility Congestion Analysis System | Next.js, FastAPI, PostgreSQL, Docker
    - product-facing features for facility congestion analysis.
    ApplyPilot – Rule-Based Job-Fit Evaluation Platform | Next.js, FastAPI, PostgreSQL, Docker - Built profile using structured rules for new-grad fit,
    skills,
    location, and work authorization risk.
    - backend persistence and job saving for analyzed applications.
    Student Academic Management System (SAM) | Spring Boot, MySQL, React, GitHub Actions - Developed management workflows.
    CNN vs. SNN Image Classification Comparison | Python, NumPy, PyTorch, Matplotlib - Conducted image classification experiments.
    - and tested a 3-layer Spiking Neural Network.
    - Built a custom 3-layer Spiking Neural Network (SNN) and compared it with ResNet.

    TECHNICAL SKILLS Technical Languages: C, Java, Python, HTML, CSS, JavaScript, SQL
    Frameworks: React, Next.js, Node.js, Express.js, Spring Boot, FastAPI, REST API
    Databases: MySQL, PostgreSQL
    Tools: Git, GitHub, Docker, Linux
    """

    normalized = normalize_resume_text(resume_text)
    projects = extract_project_names(normalized)
    skills = extract_skills_from_technical_skills_section(normalized)
    summary = build_experience_summary(normalized, skills, projects)

    assert "PROJECTS\nDocuParse" in normalized
    assert "TECHNICAL SKILLS\nTechnical Languages" in normalized
    assert "profile using structured rules for new-grad fit, SKILLS location" not in normalized
    assert "\nSKILLS\nlocation" not in normalized
    assert "profile using structured rules for new-grad fit,\nskills, location" in normalized
    assert projects == [
        "DocuParse – AI-Powered Document Understanding System",
        "Smart Seat & Facility Congestion Analysis System",
        "ApplyPilot – Rule-Based Job-Fit Evaluation Platform",
        "Student Academic Management System (SAM)",
        "CNN vs. SNN Image Classification Comparison",
    ]
    assert len(projects) == 5
    assert "AI inference with fallback routing across multiple document formats" not in projects
    assert "Spiking Neural Network (SNN)" not in projects
    assert "Spiking Neural Network" not in projects
    assert "Built projects including DocuParse" in summary
    assert "Student Academic Management System (SAM)" in summary
    assert "CNN vs. SNN Image Classification Comparison" in summary
    for fragment in [
        "AI inference",
        "fallback routing",
        "and tested a 3",
        "a multi",
        "product",
        "backend persistence",
        "job saving",
    ]:
        assert fragment not in summary
