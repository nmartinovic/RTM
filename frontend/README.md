# Frontend workspace

This workspace contains the static dashboard shell for GitHub Pages. The package manifest declares the intended React/Vite/TypeScript stack, while the current shell keeps the build path dependency-light until the registry dependencies can be installed in CI or a developer workstation.

## Stack

- TypeScript
- Static GitHub Pages-compatible assets
- Browser-safe configuration through Vite-style `VITE_*` environment variables
- Intended React/Vite dependencies declared in `package.json`

## Routes

The shell includes hash-based placeholder routes for:

- Dashboard (`#/dashboard`)
- Uploads (`#/uploads`)
- Review queues (`#/review-queues`)
- Audit (`#/audit`)
- Settings (`#/settings`)

## Local development

```bash
npm install
npm run dev
```

Build the static assets with:

```bash
npm run build
```

The build emits deployable static files to `dist/`.

## GitHub Pages deployment

The repository includes a GitHub Actions workflow at `.github/workflows/deploy-pages.yml` that builds this workspace and publishes `dist/` to GitHub Pages whenever changes are pushed to `main`. The workflow can also be started manually from the Actions tab.

For the deployed dashboard, configure the backend API origin with a repository variable named `VITE_API_BASE_URL`. Use a public HTTPS origin only; do not store RTM shared secrets, Gemma keys, long-lived RTM tokens, database URLs, or session-signing secrets in GitHub Pages variables because frontend variables are embedded in static browser assets.

## Configuration

Set the browser-safe backend API origin with a Vite-style environment variable:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

The app defaults to `http://localhost:8000` when `VITE_API_BASE_URL` is not provided.

Never put RTM shared secrets, Gemma keys, long-lived RTM tokens, database URLs, or session-signing secrets in this workspace. Those values belong in backend-only configuration or a hosting-provider secret manager.
