# Backend workspace

FastAPI backend for the RTM task organizer. This service protects secrets and performs RTM, Gemma, persistence, and file-processing work.

## Intended stack

- Python 3.12+
- FastAPI
- SQLAlchemy/Alembic
- Postgres for managed deployments, or SQLite only where durable storage is available

## Responsibilities

- Handle RTM authentication and signed RTM API calls.
- Call Gemma and validate structured model outputs.
- Store task snapshots, proposals, source-document metadata, and audit logs.
- Extract text from uploaded files.
- Apply approved or low-risk validated RTM writes.
- Expose HTTPS APIs consumed by the static frontend.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --app-dir backend --reload
```

The API will be available at `http://127.0.0.1:8000`. Keep local configuration in ignored `.env` files or shell environment variables.

## Required environment variables

- `APP_ENV`: deployment environment name, such as `development` or `production`.
- `APP_USERNAME`: single-user login name. The local default is `admin`; set a real value for deployments.
- `APP_PASSWORD`: single-user login password. The local default is `change-me`; set a secret value for deployments.
- `FRONTEND_ORIGIN`: exact GitHub Pages origin allowed by CORS, for example `https://nmartinovic.github.io`.
- `SESSION_SECRET_KEY`: secret used to sign session tokens. Set this to a long random value outside local development.
- `SESSION_COOKIE_SECURE`: set to `true` for HTTPS deployments.
- `RTM_API_KEY`: Remember The Milk API key.
- `RTM_SHARED_SECRET`: Remember The Milk shared secret used for API signatures.
- `RTM_PERMS`: requested RTM auth permissions. Use `read` for the read-only integration milestone.
- `RTM_TOKEN_STORE_PATH`: backend-only file path for MVP RTM token storage. Defaults to ignored `local-data/rtm-token.json`.

Future Gemma, database, and storage credentials also belong in backend-only environment variables or the hosting provider's secret manager. Do not put those values in GitHub Pages variables.

## CORS

The backend only allows browser calls from `FRONTEND_ORIGIN`. Do not use `*` in production because authenticated requests include cookies and bearer tokens.

For GitHub Pages, set `FRONTEND_ORIGIN` to the site origin only, without a path. If the dashboard URL is `https://nmartinovic.github.io/RTM/`, the origin is `https://nmartinovic.github.io`.

## Deployment notes

Deploy the backend to Cloud Run, Railway, Render, Fly.io, or another HTTPS-capable host. Configure the environment variables above in the provider dashboard or secret manager, then set the frontend repository variable `VITE_API_BASE_URL` to the deployed backend origin, such as `https://rtm-api.example.com`.

Use managed Postgres for durable production storage when persistence is added. Use SQLite only on hosts that provide durable persistent volumes.

## Endpoints

- `GET /health`: public health check.
- `POST /api/login`: accepts `{"username": "...", "password": "..."}` and returns a bearer token while also setting an HTTP-only session cookie.
- `POST /api/logout`: clears the session cookie. Requires authentication.
- `GET /api/session`: returns the current authenticated user. Requires authentication.
- `GET /api/rtm/status`: returns the server-side RTM connection state. Requires authentication.
- `POST /api/rtm/connect`: returns a signed RTM authorization URL. Requires authentication.
- `GET /api/rtm/callback`: exchanges RTM's `frob` for an auth token and stores it on the backend. Requires authentication.
- `GET /api/rtm/sync`: fetches RTM lists and incomplete tasks with read-only API methods and returns PRD-style task snapshots with `state_hash`. Requires authentication and an RTM connection.

The read-only RTM sync calls `rtm.lists.getList` and `rtm.tasks.getList` with `filter=status:incomplete`. It does not call RTM write methods.
