from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import app
from app.rtm import RtmToken, RtmUser, save_rtm_token, sign_rtm_params
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


def store_token(settings: Settings) -> None:
    save_rtm_token(
        RtmToken(
            token="stored-token",
            perms="read",
            user=RtmUser(id="123", username="rtm-user", fullname="RTM User"),
        ),
        settings,
    )


def test_rtm_sync_requires_stored_token(tmp_path: Path) -> None:
    response = authenticated_client(make_settings(tmp_path / "token.json")).get("/api/rtm/sync")

    assert response.status_code == 409
    assert response.json()["detail"] == "RTM is not connected"


def test_rtm_sync_fetches_lists_and_incomplete_tasks(tmp_path: Path, monkeypatch: Any) -> None:
    settings = make_settings(tmp_path / "token.json")
    store_token(settings)
    called_methods: list[str] = []

    class FakeResponse:
        def __init__(self, payload: dict[str, Any]) -> None:
            self.payload = payload

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return self.payload

    def fake_get(url: str, params: dict[str, str], timeout: float) -> FakeResponse:
        assert url == "https://api.rememberthemilk.com/services/rest/"
        assert timeout == 10.0
        assert params["api_key"] == "test-key"
        assert params["auth_token"] == "stored-token"
        assert params["format"] == "json"
        assert params["api_sig"] == sign_rtm_params(
            {key: value for key, value in params.items() if key != "api_sig"},
            "test-secret",
        )
        called_methods.append(params["method"])

        if params["method"] == "rtm.lists.getList":
            return FakeResponse(
                {
                    "rsp": {
                        "stat": "ok",
                        "lists": {
                            "list": [
                                {
                                    "id": "100653",
                                    "name": "Inbox",
                                    "deleted": "0",
                                    "locked": "1",
                                    "archived": "0",
                                    "position": "-1",
                                    "smart": "0",
                                },
                                {
                                    "id": "387549",
                                    "name": "High Priority",
                                    "deleted": "0",
                                    "locked": "0",
                                    "archived": "0",
                                    "position": "0",
                                    "smart": "1",
                                    "filter": "(priority:1)",
                                },
                            ]
                        },
                    }
                }
            )

        assert params["method"] == "rtm.tasks.getList"
        assert params["filter"] == "status:incomplete"
        return FakeResponse(
            {
                "rsp": {
                    "stat": "ok",
                    "tasks": {
                        "list": {
                            "id": "100653",
                            "taskseries": [
                                {
                                    "id": "123456789",
                                    "created": "2015-05-07T10:19:54Z",
                                    "modified": "2015-05-07T10:20:00Z",
                                    "name": "Get Bananas",
                                    "source": "api",
                                    "url": "https://example.com/task",
                                    "location_id": "",
                                    "tags": {"tag": ["errand", "food"]},
                                    "notes": {"note": [{"$t": "Buy ripe ones"}]},
                                    "task": {
                                        "id": "987654321",
                                        "due": "",
                                        "has_due_time": "0",
                                        "added": "2015-05-07T10:19:54Z",
                                        "completed": "",
                                        "deleted": "",
                                        "priority": "N",
                                        "postponed": "0",
                                        "estimate": "",
                                    },
                                },
                                {
                                    "id": "completed-series",
                                    "name": "Already Done",
                                    "tags": {},
                                    "notes": {},
                                    "task": {
                                        "id": "done-task",
                                        "completed": "2015-05-07T11:00:00Z",
                                        "deleted": "",
                                    },
                                },
                            ],
                        }
                    },
                }
            }
        )

    monkeypatch.setattr("app.rtm.httpx.get", fake_get)

    response = authenticated_client(settings).get("/api/rtm/sync")

    assert response.status_code == 200
    assert called_methods == ["rtm.lists.getList", "rtm.tasks.getList"]
    assert response.json() == {
        "lists": [
            {
                "id": "100653",
                "name": "Inbox",
                "deleted": False,
                "locked": True,
                "archived": False,
                "position": -1,
                "smart": False,
                "filter": None,
            },
            {
                "id": "387549",
                "name": "High Priority",
                "deleted": False,
                "locked": False,
                "archived": False,
                "position": 0,
                "smart": True,
                "filter": "(priority:1)",
            },
        ],
        "tasks": [
            {
                "list_id": "100653",
                "taskseries_id": "123456789",
                "task_id": "987654321",
                "name": "Get Bananas",
                "created": "2015-05-07T10:19:54Z",
                "modified": "2015-05-07T10:20:00Z",
                "source": "api",
                "url": "https://example.com/task",
                "location_id": "",
                "tags": ["errand", "food"],
                "notes": ["Buy ripe ones"],
                "due": "",
                "has_due_time": False,
                "added": "2015-05-07T10:19:54Z",
                "completed": "",
                "deleted": "",
                "priority": "N",
                "postponed": 0,
                "estimate": "",
            }
        ],
        "list_count": 2,
        "active_task_count": 1,
    }


def test_rtm_sync_surfaces_rtm_errors(tmp_path: Path, monkeypatch: Any) -> None:
    settings = make_settings(tmp_path / "token.json")
    store_token(settings)

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {"rsp": {"stat": "fail", "err": {"code": "98", "msg": "Invalid auth token"}}}

    monkeypatch.setattr("app.rtm.httpx.get", lambda *args, **kwargs: FakeResponse())

    response = authenticated_client(settings).get("/api/rtm/sync")

    assert response.status_code == 502
    assert response.json()["detail"] == "Invalid auth token"
