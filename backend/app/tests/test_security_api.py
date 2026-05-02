from datetime import timedelta
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
