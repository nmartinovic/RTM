from typing import Annotated

from fastapi import Depends, FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.auth import AuthenticatedUser, create_session_token, get_current_user, verify_credentials
from app.settings import Settings, get_settings


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    authenticated: bool
    token_type: str
    access_token: str
    user: AuthenticatedUser


class SessionResponse(BaseModel):
    authenticated: bool
    user: AuthenticatedUser


class LogoutResponse(BaseModel):
    authenticated: bool


app = FastAPI(title="RTM Task Organizer API", version="0.1.0")
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginResponse:
    if not verify_credentials(request.username, request.password, settings):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"authenticated": False, "token_type": "bearer", "access_token": "", "user": {"username": ""}}

    token = create_session_token(request.username, settings)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        max_age=settings.session_ttl_seconds,
    )
    return LoginResponse(
        authenticated=True,
        token_type="bearer",
        access_token=token,
        user=AuthenticatedUser(username=request.username),
    )


@app.post("/api/logout", response_model=LogoutResponse)
def logout(
    response: Response,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LogoutResponse:
    response.delete_cookie(settings.session_cookie_name)
    return LogoutResponse(authenticated=False)


@app.get("/api/session", response_model=SessionResponse)
def session(user: Annotated[AuthenticatedUser, Depends(get_current_user)]) -> SessionResponse:
    return SessionResponse(authenticated=True, user=user)
