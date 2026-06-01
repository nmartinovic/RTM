# GitHub Milestones and Issues Roadmap

This roadmap converts `PRD.md` into GitHub milestones and implementation issues for the MVP. The machine-readable source of truth is [`docs/github-roadmap.json`](github-roadmap.json), and `scripts/create_github_roadmap.py` can create or update the labels, milestones, and issues through the GitHub REST API.

## Milestones

1. **M1: Repository and Deployment Skeleton** — monorepo foundations, frontend app shell, backend app shell, GitHub Pages deployment, CORS, and login/session.
2. **M2: RTM Read-Only Integration** — Remember The Milk auth, list/task fetch, task normalization, and dashboard status/counts.
3. **M3: Database and Audit Foundation** — SQLAlchemy/migrations, persistence models, task snapshots, and audit API.
4. **M4: Task Maintenance Review** — Gemma maintenance prompt/schema, validation, and review-only proposal UI.
5. **M5: Safe Auto-Apply** — validated low-risk RTM writes, safety gates, idempotency, and audit logs.
6. **M6: Review Queue** — approve/reject/edit flows for maintenance proposals.
7. **M7: File Upload and Text Extraction** — upload validation/storage, MVP text extraction formats, and preview UI.
8. **M8: Gemma Action Extraction** — action extraction prompt/schema, proposal validation/storage, and grouped review UI.
9. **M9: Create Approved RTM Tasks** — action approval flows, duplicate detection, RTM task creation, metadata, and source notes.
10. **M10: Weekly Project Review** — project health summaries, missing next actions, stale tasks, duplicates, and weekly focus.
11. **M11: Polish and Settings** — settings, retention controls, prompt override, errors, and optional scheduling hooks.

## Issue Counts by Milestone

| Milestone | Issue count |
| --- | ---: |
| M1: Repository and Deployment Skeleton | 5 |
| M2: RTM Read-Only Integration | 4 |
| M3: Database and Audit Foundation | 4 |
| M4: Task Maintenance Review | 4 |
| M5: Safe Auto-Apply | 3 |
| M6: Review Queue | 3 |
| M7: File Upload and Text Extraction | 3 |
| M8: Gemma Action Extraction | 3 |
| M9: Create Approved RTM Tasks | 3 |
| M10: Weekly Project Review | 2 |
| M11: Polish and Settings | 4 |
| **Total** | **38** |

## Creating the GitHub Roadmap

Prerequisites:

- A GitHub personal access token or GitHub Actions token with permission to create labels, milestones, and issues.
- The repository owner/name, either through `GITHUB_REPOSITORY=owner/repo` or command-line flags.

Dry run:

```bash
python scripts/create_github_roadmap.py --repo owner/repo --dry-run
```

Create labels, milestones, and issues:

```bash
GITHUB_TOKEN=ghp_xxx python scripts/create_github_roadmap.py --repo owner/repo
```

The script is title-idempotent:

- Existing labels are updated.
- Existing open or closed milestones with the same title are reused/updated.
- Existing open or closed issues with the same title are reused and assigned to the matching milestone/labels.
- Missing issues are created.
