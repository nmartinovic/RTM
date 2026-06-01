# Frontend workspace

This workspace is reserved for the static GitHub Pages dashboard.

## Intended stack

- React
- Vite
- TypeScript
- Static hosting through GitHub Pages

## Responsibilities

- Display RTM connection status and dashboard summaries.
- Provide task maintenance and action-intake review queues.
- Upload source files or extracted text to the backend API.
- Let the user approve, reject, edit, or merge AI proposals.
- Show audit logs and run summaries.

## Local development

The app shell has not been scaffolded yet. Once it is added, the expected flow will be:

```bash
npm install
npm run dev
```

Use non-secret Vite environment variables for browser-safe configuration, for example:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

Never put RTM shared secrets, Gemma keys, long-lived RTM tokens, database URLs, or session-signing secrets in this workspace.
