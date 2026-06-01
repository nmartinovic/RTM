from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from app.main import app
from app.rtm import sign_rtm_params
from app.settings import Settings, get_settings


def make_settings(token_path: Path) -> Settings:
    return Settings(
        APP_USERNAME="test-user",
        APP_PASSWORD="test-password",
        FRONTEND_ORIGIN="https://nmartinovic.github.io",
        SESSION_SECRET_KEY="test-secret",
        SESSION_COOKIE_NAME="rtm_session",
        SESSION_TTL_SECONDS=3600,
        RTM_API_KEY="test-key",
        RTM_SHARED_SECRET="test-secret",
        RTM_TOKEN_STORE_PATH=str(token_path),
    )


def authenticated_client(settings: Settings) -> TestClient:
    app.dependency_overrides[get_settings] = lambda: settings
    test_client = TestClient(app)
    test_client.post(
        "/api/login",
        json={"username": "test-user", "password": "test-password"},
    )
    return test_client


def test_rtm_signature_matches_documented_algorithm() -> None:
    signature = sign_rtm_params(
        {"yxz": "foo", "feg": "bar", "abc": "baz"},
        "BANANAS",
    )

    assert signature == "82044aae4dd676094f23f1ec152159ba"


def test_rtm_status_requires_authentication(tmp_path: Path) -> None:
    app.dependency_overrides[get_settings] = lambda: make_settings(tmp_path / "token.json")

    response = TestClient(app).get("/api/rtm/status")

    assert response.status_code == 401


def test_rtm_status_reports_disconnected_without_stored_token(tmp_path: Path) -> None:
    response = authenticated_client(make_settings(tmp_path / "token.json")).get("/api/rtm/status")

    assert response.status_code == 200
    assert response.json() == {"connected": False, "user": None, "perms": None}


def test_rtm_connect_returns_signed_authorization_url(tmp_path: Path) -> None:
    response = authenticated_client(make_settings(tmp_path / "token.json")).post("/api/rtm/connect")

    assert response.status_code == 200
    auth_url = response.json()["authorization_url"]
    parsed = urlparse(auth_url)
    params = parse_qs(parsed.query)

    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == "https://www.rememberthemilk.com/services/auth/"
    assert params["api_key"] == ["test-key"]
    assert params["perms"] == ["read"]
    assert params["api_sig"] == [
        sign_rtm_params({"api_key": "test-key", "perms": "read"}, "test-secret"),
    ]


def test_rtm_callback_redeems_frob_and_stores_token(tmp_path: Path, monkeypatch: Any) -> None:
    token_path = tmp_path / "rtm-token.json"
    captured_params: dict[str, str] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {
                "rsp": {
                    "stat": "ok",
                    "auth": {
                        "token": "rtm-token",
                        "perms": "read",
                        "user": {
                            "id": "123",
                            "username": "rtm-user",
                            "fullname": "RTM User",
                        },
                    },
                },
            }

    def fake_get(url: str, params: dict[str, str], timeout: float) -> FakeResponse:
        captured_params.update(params)
        assert url == "https://api.rememberthemilk.com/services/rest/"
        assert timeout == 10.0
        return FakeResponse()

    monkeypatch.setattr("app.rtm.httpx.get", fake_get)
    test_client = authenticated_client(make_settings(token_path))

    callback_response = test_client.get("/api/rtm/callback?frob=test-frob")
    status_response = test_client.get("/api/rtm/status")

    assert callback_response.status_code == 200
    assert callback_response.json() == {
        "connected": True,
        "perms": "read",
        "user": {"id": "123", "username": "rtm-user", "fullname": "RTM User"},
    }
    assert status_response.json() == callback_response.json()
    assert token_path.exists()
    assert token_path.stat().st_mode & 0o777 == 0o600
    assert captured_params["method"] == "rtm.auth.getToken"
    assert captured_params["frob"] == "test-frob"
    assert captured_params["api_sig"] == sign_rtm_params(
        {
            "api_key": "test-key",
            "format": "json",
            "frob": "test-frob",
            "method": "rtm.auth.getToken",
        },
        "test-secret",
    )


def test_rtm_connect_reports_missing_credentials(tmp_path: Path) -> None:
    settings = make_settings(tmp_path / "token.json")
    settings.rtm_api_key = ""

    response = authenticated_client(settings).post("/api/rtm/connect")

    assert response.status_code == 503
    assert response.json()["detail"] == "RTM API credentials are not configured"
