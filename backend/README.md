# Backend workspace

This workspace is reserved for the backend API that protects secrets and performs RTM, Gemma, persistence, and file-processing work.

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

The service shell has not been scaffolded yet. Once packaging is added, the expected flow will be:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Keep local configuration in ignored `.env` files or shell environment variables. Secret-bearing values include RTM credentials, Gemma credentials, database URLs, session keys, and storage credentials.
