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
