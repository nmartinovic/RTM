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


def load_rtm_status(settings: Settings) -> RtmStatus:
    token = load_rtm_token(settings)
    if token is None:
        return RtmStatus(connected=False)
    return RtmStatus(connected=True, user=token.user, perms=token.perms)


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
