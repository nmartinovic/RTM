from fastapi.testclient import TestClient

from app.main import app
from app.settings import Settings, get_settings


def override_settings() -> Settings:
    return Settings(
        APP_USERNAME="test-user",
        APP_PASSWORD="test-password",
        FRONTEND_ORIGIN="https://nmartinovic.github.io",
        SESSION_SECRET_KEY="test-secret",
        SESSION_COOKIE_NAME="rtm_session",
        SESSION_TTL_SECONDS=3600,
    )


def client() -> TestClient:
    app.dependency_overrides[get_settings] = override_settings
    return TestClient(app)


def test_health_is_public() -> None:
    response = client().get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_configured_frontend_origin() -> None:
    response = client().options(
        "/api/session",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_rejects_unconfigured_origin() -> None:
    response = client().options(
        "/api/session",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_session_rejects_unauthenticated_request() -> None:
    response = client().get("/api/session")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_login_sets_cookie_and_session_returns_user() -> None:
    test_client = client()

    login_response = test_client.post(
        "/api/login",
        json={"username": "test-user", "password": "test-password"},
    )
    session_response = test_client.get("/api/session")

    assert login_response.status_code == 200
    assert login_response.json()["authenticated"] is True
    assert "rtm_session" in login_response.cookies
    assert session_response.status_code == 200
    assert session_response.json() == {
        "authenticated": True,
        "user": {"username": "test-user"},
    }


def test_bearer_token_authenticates_session() -> None:
    test_client = client()
    login_response = test_client.post(
        "/api/login",
        json={"username": "test-user", "password": "test-password"},
    )
    access_token = login_response.json()["access_token"]

    session_response = TestClient(app).get(
        "/api/session",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert session_response.status_code == 200
    assert session_response.json()["user"] == {"username": "test-user"}


def test_login_rejects_bad_credentials() -> None:
    response = client().post(
        "/api/login",
        json={"username": "test-user", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["authenticated"] is False


def test_logout_requires_authentication() -> None:
    response = client().post("/api/logout")

    assert response.status_code == 401


def test_logout_clears_authenticated_session() -> None:
    test_client = client()
    test_client.post(
        "/api/login",
        json={"username": "test-user", "password": "test-password"},
    )

    logout_response = test_client.post("/api/logout")
    session_response = test_client.get("/api/session")

    assert logout_response.status_code == 200
    assert logout_response.json() == {"authenticated": False}
    assert session_response.status_code == 401
