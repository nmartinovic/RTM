import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.settings import Settings


class RtmUser(BaseModel):
    id: str
    username: str
    fullname: str = ""


class RtmToken(BaseModel):
    token: str
    perms: str
    user: RtmUser


class RtmStatus(BaseModel):
    connected: bool
    user: RtmUser | None = None
    perms: str | None = None


class RtmList(BaseModel):
    id: str
    name: str
    deleted: bool
    locked: bool
    archived: bool
    position: int | None = None
    smart: bool
    filter: str | None = None


class RtmTask(BaseModel):
    list_id: str
    taskseries_id: str
    task_id: str
    name: str
    created: str
    modified: str
    source: str
    url: str
    location_id: str
    tags: list[str]
    notes: list[str]
    due: str
    start: str
    has_due_time: bool
    added: str
    completed: str
    deleted: str
    priority: str
    postponed: int
    estimate: str
    recurrence: str | None


class TaskSnapshot(BaseModel):
    list_id: str
    list_name: str | None
    taskseries_id: str
    task_id: str
    name: str
    notes: list[str]
    tags: list[str]
    due: str | None
    start: str | None
    priority: str
    estimate: str | None
    url: str | None
    recurrence: str | None
    completed: str | None
    deleted: str | None
    state_hash: str


class RtmReadResponse(BaseModel):
    lists: list[RtmList]
    tasks: list[RtmTask]
    snapshots: list[TaskSnapshot]
    list_count: int
    active_task_count: int


def build_rtm_auth_url(settings: Settings) -> str:
    _require_rtm_credentials(settings)
    params = {
        "api_key": settings.rtm_api_key,
        "perms": settings.rtm_perms,
    }
    params["api_sig"] = sign_rtm_params(params, settings.rtm_shared_secret)
    return f"{settings.rtm_auth_url}?{urlencode(params)}"


def sign_rtm_params(params: dict[str, str], shared_secret: str) -> str:
    payload = shared_secret + "".join(f"{key}{params[key]}" for key in sorted(params))
    return hashlib.md5(payload.encode()).hexdigest()


def redeem_rtm_frob(frob: str, settings: Settings) -> RtmToken:
    _require_rtm_credentials(settings)
    params = {
        "api_key": settings.rtm_api_key,
        "format": "json",
        "frob": frob,
        "method": "rtm.auth.getToken",
    }
    params["api_sig"] = sign_rtm_params(params, settings.rtm_shared_secret)

    try:
        response = httpx.get(settings.rtm_rest_url, params=params, timeout=settings.rtm_request_timeout_seconds)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="RTM token exchange failed",
        ) from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="RTM returned an invalid response",
        ) from exc

    return parse_rtm_token_response(payload)


def fetch_rtm_read_data(settings: Settings) -> RtmReadResponse:
    token = require_rtm_token(settings)
    lists_payload = call_rtm_method("rtm.lists.getList", settings, token)
    tasks_payload = call_rtm_method("rtm.tasks.getList", settings, token, {"filter": "status:incomplete"})
    lists = parse_rtm_lists_response(lists_payload)
    tasks = parse_rtm_tasks_response(tasks_payload)
    snapshots = build_task_snapshots(lists, tasks)
    return RtmReadResponse(
        lists=lists,
        tasks=tasks,
        snapshots=snapshots,
        list_count=len(lists),
        active_task_count=len(tasks),
    )


def call_rtm_method(
    method: str,
    settings: Settings,
    token: RtmToken,
    extra_params: dict[str, str] | None = None,
) -> dict[str, Any]:
    _require_rtm_credentials(settings)
    params = {
        "api_key": settings.rtm_api_key,
        "auth_token": token.token,
        "format": "json",
        "method": method,
    }
    if extra_params:
        params.update(extra_params)
    params["api_sig"] = sign_rtm_params(params, settings.rtm_shared_secret)
    return _get_rtm_json(settings, params)


def parse_rtm_token_response(payload: dict[str, Any]) -> RtmToken:
    rsp = payload.get("rsp")
    if not isinstance(rsp, dict):
        raise _bad_rtm_response()

    if rsp.get("stat") == "fail":
        err = rsp.get("err") if isinstance(rsp.get("err"), dict) else {}
        message = err.get("msg") or "RTM authorization failed"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    auth = rsp.get("auth")
    if rsp.get("stat") != "ok" or not isinstance(auth, dict):
        raise _bad_rtm_response()

    user = auth.get("user")
    if not isinstance(user, dict):
        raise _bad_rtm_response()

    try:
        return RtmToken(
            token=str(auth["token"]),
            perms=str(auth["perms"]),
            user=RtmUser(
                id=str(user["id"]),
                username=str(user["username"]),
                fullname=str(user.get("fullname", "")),
            ),
        )
    except KeyError as exc:
        raise _bad_rtm_response() from exc


def parse_rtm_lists_response(payload: dict[str, Any]) -> list[RtmList]:
    rsp = _require_ok_rsp(payload)
    lists_payload = _as_list(_require_dict(rsp.get("lists"), "lists").get("list"))
    lists: list[RtmList] = []

    for item in lists_payload:
        list_payload = _require_dict(item, "list")
        lists.append(
            RtmList(
                id=str(list_payload["id"]),
                name=str(list_payload["name"]),
                deleted=_rtm_bool(list_payload.get("deleted")),
                locked=_rtm_bool(list_payload.get("locked")),
                archived=_rtm_bool(list_payload.get("archived")),
                position=_optional_int(list_payload.get("position")),
                smart=_rtm_bool(list_payload.get("smart")),
                filter=_optional_text(list_payload.get("filter")),
            )
        )

    return lists


def parse_rtm_tasks_response(payload: dict[str, Any]) -> list[RtmTask]:
    rsp = _require_ok_rsp(payload)
    list_payloads = _as_list(_require_dict(rsp.get("tasks"), "tasks").get("list"))
    tasks: list[RtmTask] = []

    for item in list_payloads:
        list_payload = _require_dict(item, "list")
        list_id = str(list_payload["id"])
        taskseries_payloads = _as_list(list_payload.get("taskseries"))

        for taskseries_item in taskseries_payloads:
            taskseries = _require_dict(taskseries_item, "taskseries")
            task_payloads = _as_list(taskseries.get("task"))
            tags = _parse_tags(taskseries.get("tags"))
            notes = _parse_notes(taskseries.get("notes"))

            for task_item in task_payloads:
                task = _require_dict(task_item, "task")
                if task.get("completed") or task.get("deleted"):
                    continue
                tasks.append(
                    RtmTask(
                        list_id=list_id,
                        taskseries_id=str(taskseries["id"]),
                        task_id=str(task["id"]),
                        name=str(taskseries["name"]),
                        created=str(taskseries.get("created", "")),
                        modified=str(taskseries.get("modified", "")),
                        source=str(taskseries.get("source", "")),
                        url=str(taskseries.get("url", "")),
                        location_id=str(taskseries.get("location_id", "")),
                        tags=tags,
                        notes=notes,
                        due=str(task.get("due", "")),
                        start=str(task.get("start", "")),
                        has_due_time=_rtm_bool(task.get("has_due_time")),
                        added=str(task.get("added", "")),
                        completed=str(task.get("completed", "")),
                        deleted=str(task.get("deleted", "")),
                        priority=str(task.get("priority", "")),
                        postponed=_optional_int(task.get("postponed")) or 0,
                        estimate=str(task.get("estimate", "")),
                        recurrence=_parse_recurrence(taskseries.get("rrule")),
                    )
                )

    return tasks


def build_task_snapshots(lists: list[RtmList], tasks: list[RtmTask]) -> list[TaskSnapshot]:
    list_names = {rtm_list.id: rtm_list.name for rtm_list in lists}
    return [build_task_snapshot(task, list_names.get(task.list_id)) for task in tasks]


def build_task_snapshot(task: RtmTask, list_name: str | None) -> TaskSnapshot:
    snapshot_fields = {
        "list_id": task.list_id,
        "list_name": list_name,
        "taskseries_id": task.taskseries_id,
        "task_id": task.task_id,
        "name": task.name,
        "notes": task.notes,
        "tags": sorted(task.tags),
        "due": _optional_text(task.due),
        "start": _optional_text(task.start),
        "priority": task.priority,
        "estimate": _optional_text(task.estimate),
        "url": _optional_text(task.url),
        "recurrence": task.recurrence,
        "completed": _optional_text(task.completed),
        "deleted": _optional_text(task.deleted),
    }
    return TaskSnapshot(
        **snapshot_fields,
        state_hash=compute_state_hash(snapshot_fields),
    )


def compute_state_hash(snapshot_fields: dict[str, Any]) -> str:
    encoded = json.dumps(snapshot_fields, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def load_rtm_status(settings: Settings) -> RtmStatus:
    token = load_rtm_token(settings)
    if token is None:
        return RtmStatus(connected=False)
    return RtmStatus(connected=True, user=token.user, perms=token.perms)


def require_rtm_token(settings: Settings) -> RtmToken:
    token = load_rtm_token(settings)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="RTM is not connected",
        )
    return token


def load_rtm_token(settings: Settings) -> RtmToken | None:
    path = Path(settings.rtm_token_store_path)
    if not path.exists():
        return None

    try:
        return RtmToken.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored RTM token is unreadable",
        ) from exc


def save_rtm_token(token: RtmToken, settings: Settings) -> None:
    path = Path(settings.rtm_token_store_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(token.model_dump_json(), encoding="utf-8")
    path.chmod(0o600)


def _get_rtm_json(settings: Settings, params: dict[str, str]) -> dict[str, Any]:
    try:
        response = httpx.get(settings.rtm_rest_url, params=params, timeout=settings.rtm_request_timeout_seconds)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="RTM API request failed",
        ) from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="RTM returned an invalid response",
        ) from exc

    if not isinstance(payload, dict):
        raise _bad_rtm_response()
    return payload


def _require_rtm_credentials(settings: Settings) -> None:
    if not settings.rtm_api_key or not settings.rtm_shared_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RTM API credentials are not configured",
        )


def _bad_rtm_response() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="RTM returned an unexpected response",
    )


def _require_ok_rsp(payload: dict[str, Any]) -> dict[str, Any]:
    rsp = payload.get("rsp")
    if not isinstance(rsp, dict):
        raise _bad_rtm_response()

    if rsp.get("stat") == "fail":
        err = rsp.get("err") if isinstance(rsp.get("err"), dict) else {}
        message = err.get("msg") or "RTM API request failed"
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=message)

    if rsp.get("stat") != "ok":
        raise _bad_rtm_response()
    return rsp


def _require_dict(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"RTM response missing {field_name}",
        )
    return value


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _rtm_bool(value: Any) -> bool:
    return str(value) == "1"


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _optional_text(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _parse_tags(tags_payload: Any) -> list[str]:
    tags = _require_dict(tags_payload or {}, "tags").get("tag")
    return [str(tag) for tag in _as_list(tags)]


def _parse_notes(notes_payload: Any) -> list[str]:
    notes = _require_dict(notes_payload or {}, "notes").get("note")
    parsed_notes: list[str] = []
    for item in _as_list(notes):
        if isinstance(item, dict):
            parsed_notes.append(str(item.get("$t", "")))
        else:
            parsed_notes.append(str(item))
    return parsed_notes


def _parse_recurrence(rrule_payload: Any) -> str | None:
    if rrule_payload in (None, ""):
        return None
    if isinstance(rrule_payload, dict):
        return _optional_text(rrule_payload.get("$t"))
    return str(rrule_payload)
