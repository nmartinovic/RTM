# RTM AI Task Organizer

RTM AI Task Organizer is a split frontend/backend application for keeping Remember The Milk (RTM) as the source of truth while using an LLM-assisted workflow to review, clean up, and extract tasks from source documents.

The product follows the architecture in [`PRD.md`](PRD.md): a static GitHub Pages dashboard talks to a separately hosted backend API that owns all RTM, Gemma, database, and file-processing secrets.

## Repository layout

```text
.
├── frontend/   # Static React/Vite dashboard intended for GitHub Pages
├── backend/    # Python FastAPI API for RTM, Gemma, storage, and audit logs
├── docs/       # Product, architecture, roadmap, and operations documentation
├── scripts/    # Repository automation and maintenance scripts
└── PRD.md      # Product requirements document
```

## Architecture notes

- **Frontend:** A static React/Vite app served by GitHub Pages. It should never contain RTM shared secrets, Gemma API keys, or long-lived RTM tokens.
- **Backend:** A Python FastAPI service deployed to Cloud Run, Railway, Render, Fly.io, or similar. It signs RTM API requests, calls Gemma, extracts uploaded file text, stores proposals, and writes audit logs.
- **Database:** Backend-managed persistence. Use Postgres on managed hosting, or SQLite only when the host provides durable persistent storage.
- **Security boundary:** Browser code calls the backend over HTTPS. All secret-bearing configuration lives in backend environment variables or a hosting-provider secret manager.

## Local setup

This repository currently contains the baseline monorepo skeleton. Each workspace has its own README with the expected setup path and will gain concrete commands as the app shell is implemented.

### Frontend workspace

```bash
cd frontend
```

Planned local development flow:

1. Install Node.js LTS.
2. Install dependencies once a `package.json` exists.
3. Run the Vite development server.
4. Configure the dashboard with the backend API base URL through a non-secret environment variable such as `VITE_API_BASE_URL`.

See [`frontend/README.md`](frontend/README.md) for workspace details.

### Backend workspace

```bash
cd backend
```

Planned local development flow:

1. Install Python 3.12 or newer.
2. Create and activate a virtual environment.
3. Install dependencies once backend packaging is added.
4. Configure RTM, Gemma, database, and session settings through local `.env` files or shell environment variables.
5. Run the FastAPI development server.

See [`backend/README.md`](backend/README.md) for workspace details.

### Documentation workspace

```bash
cd docs
```

The docs workspace contains the GitHub roadmap and will collect architecture decisions, deployment notes, and operational runbooks. See [`docs/README.md`](docs/README.md).

## Secret handling

Do not commit secret-bearing files. Local environment files, generated credentials, private keys, build artifacts, caches, local databases, and dependency directories are ignored by the root `.gitignore`.

Examples of values that belong in backend-only environment configuration:

- RTM API key and shared secret
- RTM auth tokens
- Gemma API credentials
- database URLs and passwords
- session signing keys
- object storage credentials

## Roadmap automation

The roadmap source lives in [`docs/github-roadmap.json`](docs/github-roadmap.json). To preview GitHub label, milestone, and issue creation:

```bash
python scripts/create_github_roadmap.py --repo owner/repo --dry-run
```
