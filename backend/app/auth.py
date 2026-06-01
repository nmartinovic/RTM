import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from time import time
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.settings import Settings, get_settings


class AuthenticatedUser(BaseModel):
    username: str


@dataclass(frozen=True)
class SessionPayload:
    username: str
    expires_at: int


bearer_scheme = HTTPBearer(auto_error=False)


def verify_credentials(username: str, password: str, settings: Settings) -> bool:
    username_matches = secrets.compare_digest(username, settings.app_username)
    password_matches = secrets.compare_digest(password, settings.app_password)
    return username_matches and password_matches


def create_session_token(username: str, settings: Settings) -> str:
    payload = {
        "sub": username,
        "exp": int(time()) + settings.session_ttl_seconds,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    encoded_payload = _urlsafe_b64encode(payload_bytes)
    signature = _sign(encoded_payload, settings.session_secret_key)
    return f"{encoded_payload}.{signature}"


def parse_session_token(token: str, settings: Settings) -> SessionPayload:
    try:
        encoded_payload, signature = token.split(".", 1)
    except ValueError as exc:
        raise _invalid_session() from exc

    expected_signature = _sign(encoded_payload, settings.session_secret_key)
    if not secrets.compare_digest(signature, expected_signature):
        raise _invalid_session()

    try:
        payload = json.loads(_urlsafe_b64decode(encoded_payload))
        username = payload["sub"]
        expires_at = int(payload["exp"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise _invalid_session() from exc

    if expires_at < int(time()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
        )

    return SessionPayload(username=username, expires_at=expires_at)


def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthenticatedUser:
    token = _extract_token(request, credentials, settings)
    payload = parse_session_token(token, settings)
    return AuthenticatedUser(username=payload.username)


def _extract_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
    settings: Settings,
) -> str:
    cookie_token = request.cookies.get(settings.session_cookie_name)
    if credentials and credentials.scheme.lower() == "bearer":
        return credentials.credentials
    if cookie_token:
        return cookie_token
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )


def _sign(encoded_payload: str, secret_key: str) -> str:
    digest = hmac.new(
        secret_key.encode(),
        encoded_payload.encode(),
        hashlib.sha256,
    ).digest()
    return _urlsafe_b64encode(digest)


def _urlsafe_b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _urlsafe_b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _invalid_session() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid session",
    )
