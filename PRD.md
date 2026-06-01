# PRD: GitHub Pages AI Task Organizer for Remember The Milk

## 1. Product Summary

Build a web-accessible AI task organizer with a dashboard hosted on GitHub Pages. The product connects to Remember The Milk (RTM), uses Gemma 4 31B to organize existing tasks and extract new tasks from uploaded files, and sends validated tasks back to RTM with relevant metadata.

The product has two major workflows:

1. **Task Maintenance**
   - Pull existing tasks from Remember The Milk.
   - Clean, tag, organize, prioritize, flag, and review them.
   - Apply only safe low-risk changes automatically.

2. **Action Intake**
   - Upload files such as transcripts, emails, PDFs, meeting notes, markdown files, and text files.
   - Extract candidate actions using Gemma.
   - Show extracted actions to the user for approval or editing.
   - Create approved tasks in Remember The Milk with tags, dates, priorities, estimates, and source notes.

The GitHub Pages app is the user-facing dashboard. Because GitHub Pages is static hosting and cannot run server-side code, the product also requires a separate backend API for secrets, authentication, RTM API calls, Gemma calls, and durable storage.

---

## 2. Key Architecture Constraint

GitHub Pages can host the dashboard, but it cannot securely execute backend logic or store API secrets. Therefore, the MVP must use a split architecture:

- **Frontend:** Static React/Vite app hosted on GitHub Pages.
- **Backend:** Small API service hosted separately, recommended as GCP Cloud Run, Railway, Render, Fly.io, or a similar service.
- **Database:** Backend-managed database, initially SQLite if using persistent disk or Postgres if hosted on a managed platform.
- **LLM:** Gemma 4 31B accessed through the backend.
- **Remember The Milk API:** Accessed through the backend to avoid exposing shared secrets or auth tokens in the browser.

The GitHub Pages frontend should never contain RTM shared secrets, Gemma API keys, or long-lived RTM auth tokens.

---

## 3. Problem Statement

Task systems degrade over time:

- inboxes fill with vague tasks
- due dates become fake urgency
- priorities become inflated
- old tasks become stale
- project-related tasks are scattered
- tags become inconsistent
- tasks do not clearly express the next action
- important action items remain buried in transcripts, emails, PDFs, and notes

The user wants RTM to remain the source of truth, while Gemma helps maintain task quality and extract new tasks from unstructured source material.

The major risk is uncontrolled LLM behavior. The product must therefore use structured outputs, safety rules, audit logs, and user validation before creating or modifying important tasks.

---

## 4. Goals

### Primary Goals

1. Provide a GitHub Pages dashboard for task review and file-based action extraction.
2. Connect securely to Remember The Milk through a backend API.
3. Fetch existing RTM tasks and normalize them into structured JSON.
4. Use Gemma 4 31B to review existing tasks and propose improvements.
5. Apply only low-risk task maintenance changes automatically.
6. Upload files through the dashboard.
7. Extract text from uploaded files.
8. Use Gemma to identify candidate tasks and action items.
9. Show extracted actions to the user for validation.
10. Create approved tasks in RTM with relevant list, tags, dates, priority, estimate, URL, and notes.
11. Store audit logs for all model suggestions, user decisions, and RTM writes.
12. Provide daily and weekly task summaries.

### Secondary Goals

1. Detect duplicate tasks.
2. Detect stale tasks.
3. Detect projects missing next actions.
4. Support project-level weekly planning.
5. Support batch approval for high-confidence extracted actions.
6. Allow the user to re-run extraction with custom instructions.
7. Keep uploaded files private and avoid unnecessary retention.
8. Make the app deployable from a GitHub repository.

---

## 5. Non-Goals

The MVP will not:

1. Replace Remember The Milk as the source of truth.
2. Build a full standalone task manager.
3. Depend on RTM subtasks.
4. Automatically delete tasks.
5. Automatically complete tasks unless explicitly requested.
6. Automatically create tasks from uploaded files without user approval.
7. Expose RTM or Gemma secrets in GitHub Pages.
8. Build native mobile apps.
9. Build collaborative multi-user workflows.
10. Guarantee perfect OCR for scanned PDFs.
11. Build a full document-management system.
12. Build direct inbox polling in V1.
13. Support every proprietary file format in V1.
14. Handle legal, medical, tax, visa, financial, or payment-related actions without review.

---

## 6. Target User

Primary user:

- Individual user managing personal, work, health, job-search, and side-project tasks.
- Uses Remember The Milk as the task source of truth.
- Wants an LLM to maintain task hygiene.
- Wants a web dashboard available from GitHub Pages.
- Wants to upload transcripts, emails, PDFs, and notes to extract action items.
- Wants automation, but not uncontrolled autonomous edits.

---

## 7. Product Principles

1. **RTM remains the source of truth.**
2. **GitHub Pages is the dashboard, not the backend.**
3. **Secrets stay on the backend.**
4. **Gemma proposes; the app validates and applies selectively.**
5. **Uploaded-file extraction requires user approval before RTM creation.**
6. **Safe maintenance changes can be automatic only when confidence is high.**
7. **Risky or destructive changes require review.**
8. **Tasks should describe concrete next actions.**
9. **Dates should represent real time constraints, not fake urgency.**
10. **Priorities should be scarce.**
11. **Tags should be predictable and machine-friendly.**
12. **Every active project should have a next action.**
13. **Every extracted action should include source evidence.**
14. **Every write should be auditable.**

---

## 8. Recommended Deployment Architecture

### Frontend

- React + Vite
- Hosted on GitHub Pages
- Static assets only
- Calls backend API over HTTPS
- Uses browser session storage or backend-issued session token
- Handles drag-and-drop upload UI
- Displays review queues and audit logs

### Backend

Recommended MVP backend:

- Python FastAPI
- Hosted on GCP Cloud Run, Railway, Render, or Fly.io
- Handles RTM authentication and signed RTM API requests
- Handles Gemma API calls
- Stores audit logs and proposals
- Performs file text extraction when needed
- Exposes a secure API to the GitHub Pages frontend

### Database

Recommended MVP:

- Postgres if deployed on a managed host
- SQLite only if the host provides durable persistent storage

Recommended tables:

- users
- rtm_connections
- task_snapshots
- ai_task_proposals
- source_documents
- extracted_chunks
- action_proposals
- audit_logs
- app_settings

### Storage

Two possible modes:

#### Preferred MVP: Backend File Storage

- Frontend uploads files to backend.
- Backend stores files temporarily or permanently based on settings.
- Backend extracts text.
- Backend can delete original files after extraction if configured.

#### Privacy-Focused Alternative: Browser-First Extraction

- Frontend extracts text in browser where possible.
- Only extracted text is sent to backend.
- Original file never leaves the browser.
- More complex for PDFs, emails, and edge cases.

Recommended MVP: start with backend file upload and provide a setting to delete original files after extraction.

---

## 9. System Components

### 9.1 GitHub Pages Frontend

Responsibilities:

- Display dashboard.
- Let user connect RTM.
- Show connection status.
- Run daily/weekly reviews.
- Upload files.
- Show extracted action proposals.
- Show task maintenance proposals.
- Let user approve/reject/edit/merge proposals.
- Show run summaries and audit logs.

### 9.2 Backend API

Responsibilities:

- Authenticate frontend requests.
- Manage RTM OAuth/token flow.
- Store RTM credentials securely.
- Fetch RTM lists and tasks.
- Apply RTM task updates.
- Call Gemma.
- Validate Gemma JSON responses.
- Run safety checks.
- Store source documents, proposals, and audit logs.
- Return summaries to frontend.

### 9.3 RTM Connector

Responsibilities:

- Sign RTM API requests.
- Fetch lists.
- Fetch tasks.
- Add tasks.
- Move tasks.
- Add/remove tags.
- Set priority.
- Set due date.
- Set start date.
- Set estimate.
- Add notes.
- Handle timelines.
- Store RTM identifiers:
  - `list_id`
  - `taskseries_id`
  - `task_id`

### 9.4 Gemma Client

Responsibilities:

- Send prompts to Gemma 4 31B.
- Enforce JSON output expectations when supported.
- Retry malformed responses once.
- Return structured response to validator.
- Include model and prompt version in logs.

### 9.5 Proposal Validator

Responsibilities:

- Validate JSON schema.
- Validate task references.
- Validate action risk.
- Enforce confidence threshold.
- Enforce protected tags.
- Block destructive actions.
- Separate safe auto-apply actions from review-required actions.

### 9.6 Action Intake Service

Responsibilities:

- Accept uploaded files.
- Extract text.
- Chunk long documents.
- Send extracted content to Gemma.
- Store candidate action proposals.
- Detect duplicates.
- Prepare user validation UI data.
- Create approved RTM tasks.

### 9.7 Audit Store

Responsibilities:

- Store every model proposal.
- Store every auto-applied change.
- Store every user-approved change.
- Store every rejected proposal.
- Store every blocked or failed operation.
- Preserve old and new values.

---

## 10. User Roles

### Single-User MVP

The MVP assumes one user.

Capabilities:

- connect RTM
- upload files
- run reviews
- approve/reject proposals
- create RTM tasks
- view audit history
- configure settings

### Future Multi-User Support

Not required for MVP.

---

## 11. Authentication and Security

### Frontend Access

Because the frontend is hosted on GitHub Pages, it is public unless protected externally. The backend must enforce authentication.

MVP options:

1. Simple password-protected backend session.
2. OAuth login with GitHub or Google.
3. Single-user magic link.
4. Backend-issued API session token.

Recommended MVP:

- Single-user password login on backend.
- Frontend stores short-lived session token.
- Backend rejects all unauthenticated requests.

### Secret Storage

Backend environment variables:

```text
RTM_API_KEY=
RTM_SHARED_SECRET=
GEMMA_API_BASE_URL=
GEMMA_API_KEY=
GEMMA_MODEL=gemma-4-31b
APP_TIMEZONE=Europe/Paris
DATABASE_URL=
FRONTEND_ORIGIN=https://<github-username>.github.io
SESSION_SECRET=
```

Never store these in:

- GitHub Pages frontend code
- committed config files
- browser local storage
- public repository files

GitHub Actions secrets may be used only for deployment workflows, not for making secrets available to browser runtime.

---

## 12. Core Feature 1: RTM Task Maintenance

### 12.1 Summary

The app fetches existing RTM tasks and asks Gemma to classify, clean, tag, prioritize, and flag them. The app applies only safe changes automatically. Risky changes go to the review queue.

### 12.2 Task Classification States

Gemma should classify every reviewed task into one of these states:

1. `clear_next_action`
2. `vague`
3. `project_anchor`
4. `waiting_or_blocked`
5. `stale_or_probably_done`
6. `someday_or_backlog`

### 12.3 Safe Automatic Changes

The app may automatically apply these if confidence is high and validation passes:

- add missing tags
- remove duplicate tags
- move obvious Inbox tasks to a stable list
- rename task for clarity when meaning is preserved
- add `ai_reviewed`
- add `ai_changed`
- add `ai_needs_clarification`
- add `waiting`, `blocked`, `someday`, or `review`
- set estimate if obvious
- add project tag when highly likely

### 12.4 Changes Requiring User Approval

The app must not automatically:

- delete a task
- complete a task
- change a recurring task
- merge duplicate tasks
- change a task tagged `do_not_touch`
- change a Priority 1 task
- change a task due today
- change a legal, medical, tax, visa, financial, contractual, or payment-related task
- remove a due date that appears real
- add a hard due date when one was not explicitly provided
- create many new tags
- make large rewrites that change user intent

---

## 13. Core Feature 2: Action Intake From Uploaded Files

### 13.1 Summary

The dashboard allows the user to upload files. The system extracts text, uses Gemma to find candidate actions, shows those actions with source evidence, and creates approved tasks in RTM.

No extracted action should be sent to RTM without user approval in V1.

### 13.2 Supported File Types

#### MVP Supported Types

- `.txt`
- `.md`
- `.csv`
- `.json`
- `.html`
- `.htm`
- `.eml`
- `.pdf`
- `.vtt`
- `.srt`

#### Later

- `.docx`
- `.msg`
- `.xlsx`
- `.pptx`
- audio files requiring transcription
- image-only PDFs requiring OCR

### 13.3 Upload Flow

1. User opens GitHub Pages dashboard.
2. User logs into backend session.
3. User uploads one or more files.
4. Frontend sends files to backend over HTTPS.
5. Backend validates file type and size.
6. Backend stores file.
7. Backend extracts text.
8. Backend chunks long documents.
9. Backend sends extracted text to Gemma.
10. Gemma returns candidate actions.
11. Backend validates proposals.
12. Frontend displays proposals grouped by source document.
13. User approves, rejects, edits, or merges proposals.
14. Backend creates approved tasks in RTM.
15. Backend stores RTM identifiers and audit records.

### 13.4 Extraction Rules

Gemma should extract only real candidate actions.

Extract as tasks when the source contains:

- a clear next action
- a follow-up
- an explicit commitment
- a deadline
- an assigned responsibility for the user
- a decision that requires implementation
- a question that needs answering
- a project that needs multiple steps
- a waiting-for item

Do not extract tasks from:

- random facts
- general discussion
- completed actions
- vague aspirations
- historical context
- background explanation
- jokes or casual comments
- uncertain commitments
- anything assigned to someone else unless the user needs to follow up

### 13.5 Source Evidence Requirement

Every proposed task must include:

- source file name
- source excerpt
- reason the item is actionable
- page, line, or timestamp where available
- confidence score
- risk level

No source evidence means the proposal is blocked.

### 13.6 Review Actions

For each extracted action, user can:

- approve
- reject
- edit
- merge with another proposal
- mark as already done
- create in RTM
- send back for re-analysis with custom instruction

### 13.7 RTM Creation Rules

Preferred creation approach:

1. Create task with `rtm.tasks.add`.
2. Add tags with `rtm.tasks.addTags`.
3. Set priority with `rtm.tasks.setPriority`.
4. Set due date only if approved.
5. Set start date if supported and approved.
6. Set estimate if supported.
7. Add note with source evidence using RTM notes API.
8. Verify created task.
9. Store RTM identifiers locally.

Avoid relying entirely on Smart Add parsing for V1 because explicit metadata calls are safer and easier to audit.

---

## 14. Task Taxonomy

### 14.1 Lists

Use broad, stable lists:

- Inbox
- Work
- Personal/Admin
- Health
- Side Projects
- Job Search
- Someday/Maybe
- Waiting

### 14.2 Project Tags

Project tags start with `p_`.

Examples:

- `p_commcenter_docs`
- `p_job_search_2027`
- `p_side_hustle`
- `p_fitness`
- `p_horse_bets`
- `p_memos`

### 14.3 Context Tags

Examples:

- `computer`
- `phone`
- `errand`
- `home`
- `office`
- `deepwork`
- `quick`

### 14.4 Status Tags

Examples:

- `waiting`
- `blocked`
- `followup`
- `review`
- `someday`
- `next`

### 14.5 AI Tags

Examples:

- `ai_reviewed`
- `ai_changed`
- `ai_flagged`
- `ai_needs_clarification`
- `ai_low_confidence`
- `ai_possible_duplicate`
- `ai_stale`
- `ai_missing_next_action`

### 14.6 Protection Tag

The tag `do_not_touch` prevents all automatic model edits.

The app may still read protected tasks and include them in summaries, but it must not modify them.

---

## 15. Date Rules

The app should resolve dates using the user’s timezone.

Default timezone:

```text
Europe/Paris
```

Rules:

1. “Today” means today in the configured timezone.
2. “Tomorrow” means the next calendar day in the configured timezone.
3. “Friday” means the next upcoming Friday unless context clearly says otherwise.
4. “Next week” usually means a start date, not a due date.
5. “Someday” means no due date and tag `someday`.
6. “ASAP” does not automatically mean Priority 1.
7. Do not create hard due dates unless explicitly stated.
8. Existing real due dates should be protected.
9. Relative dates from uploaded files require a known source document date.
10. If document date is unknown, mark relative-date proposals as `needs_review`.

---

## 16. Priority Rules

Priority meanings:

- Priority 1: must be done today or serious consequence
- Priority 2: important this week
- Priority 3: useful, but not urgent
- No priority: normal backlog

Rules:

1. No more than 3 Priority 1 tasks should be recommended for a normal day.
2. Priority 1 tasks should not be automatically changed.
3. The model should flag priority inflation.
4. The model should not assign Priority 1 just because something is important.
5. If many tasks are Priority 1, extras should go to review.

---

## 17. Estimate Rules

Allowed estimate buckets:

- 5 min
- 15 min
- 30 min
- 1 hour
- 2 hours
- half day

Rules:

1. Add `quick` if estimate is 15 minutes or less.
2. Add `deepwork` if estimate is 1 hour or more and requires focus.
3. If a task is larger than half a day, flag for splitting.
4. Do not overfit estimates.

---

## 18. Risk Rules

### 18.1 Safe to Suggest

These can be shown as normal proposals:

- clear follow-ups
- clearly assigned user actions
- explicit deadlines
- meeting action items
- obvious admin tasks
- project next actions

### 18.2 Must Require Review

These must never be auto-created or auto-applied:

- legal tasks
- tax tasks
- visa/immigration tasks
- medical tasks
- financial tasks
- payment tasks
- tasks involving contracts
- tasks with ambiguous owners
- tasks with relative dates and unknown document date
- tasks inferred from weak language
- tasks that may belong to someone else
- possible duplicates

### 18.3 Blocked

These should be blocked unless the user manually edits them:

- no source evidence
- hallucinated details
- no clear action
- confidence below threshold
- unsupported file extraction
- unreadable source text
- unsafe write request
- protected task

### 18.4 High-Risk Keywords

Tasks containing these words should default to review mode:

- legal
- tax
- visa
- doctor
- medical
- contract
- lawyer
- payment
- rent
- insurance
- bank
- unemployment
- prefecture
- immigration
- passport

---

## 19. LLM Output Contracts

### 19.1 Task Maintenance Output

Gemma must return JSON only.

```json
{
  "run_summary": {
    "reviewed_count": 42,
    "safe_changes_count": 18,
    "needs_user_review_count": 6,
    "no_change_count": 18
  },
  "actions": [
    {
      "rtm_identifiers": {
        "list_id": "789",
        "taskseries_id": "456",
        "task_id": "123"
      },
      "classification": "clear_next_action",
      "confidence": 0.91,
      "risk": "safe",
      "changes": {
        "set_name": "Draft CommCenter local testing instructions",
        "move_to_list": "Work",
        "add_tags": ["p_commcenter_docs", "deepwork", "next", "ai_changed"],
        "remove_tags": ["ai_needs_clarification"],
        "set_priority": "2",
        "set_estimate": "1 hour"
      },
      "reason": "Original task was actionable but vague. It clearly belongs to CommCenter documentation."
    }
  ]
}
```

### 19.2 Action Extraction Output

Gemma must return JSON only.

```json
{
  "document_summary": {
    "source_type": "meeting_transcript",
    "short_summary": "Discussion about CommCenter handover, documentation, and next review steps.",
    "detected_projects": ["p_commcenter_docs"],
    "warnings": []
  },
  "candidate_actions": [
    {
      "candidate_task_name": "Email Pedro with CommCenter documentation review request",
      "extraction_type": "followup",
      "assignee": "user",
      "suggested_list": "Work",
      "suggested_tags": ["p_commcenter_docs", "pedro", "followup", "next"],
      "suggested_due": null,
      "suggested_start": null,
      "suggested_priority": "2",
      "suggested_estimate": "15 min",
      "suggested_note": "Ask Pedro to review the CommCenter documentation before handover.",
      "source_evidence": "Pedro can review the documentation before we hand it over.",
      "source_location": {
        "page": null,
        "line_start": 84,
        "line_end": 87,
        "timestamp_start": null,
        "timestamp_end": null
      },
      "confidence": 0.87,
      "risk": "needs_review",
      "reason": "The document implies the user should ask Pedro for review, but this should be confirmed before creating a task."
    }
  ],
  "non_actionable_items": [
    {
      "text": "The document includes background context about the mailbox poller.",
      "reason": "Useful context, but no concrete next action."
    }
  ],
  "questions_for_user": [
    {
      "question": "Should the CommCenter documentation project be tagged as p_commcenter_docs or p_commcenter_handover?",
      "related_candidate_action_indexes": [0]
    }
  ]
}
```

---

## 20. App-Level Validation

The app must validate all Gemma output before applying or creating anything.

Validation rules:

1. JSON must parse successfully.
2. Every maintenance action must reference a real RTM task.
3. Every extracted action must include source evidence.
4. Confidence must meet the configured threshold.
5. `risk` must be valid.
6. Proposed tags must match allowed tag patterns.
7. The task must not have changed since it was fetched.
8. The target task must not contain `do_not_touch`.
9. The app must not apply unsupported fields.
10. Destructive changes must always be blocked.
11. Any blocked action must be placed in the review queue if useful.

Default confidence thresholds:

- `>= 0.85`: eligible for safe automatic edit in maintenance workflow
- `0.60–0.84`: review queue
- `< 0.60`: flag only; no writes

For file intake:

- all task creation requires user approval in V1 regardless of confidence.

---

## 21. Data Model

### 21.1 User

```json
{
  "id": "uuid",
  "email": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 21.2 RTM Connection

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "rtm_user_id": "string",
  "auth_token_encrypted": "string",
  "permissions": "delete | write | read",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 21.3 Task Snapshot

```json
{
  "snapshot_id": "uuid",
  "fetched_at": "2026-05-29T10:00:00Z",
  "list_id": "string",
  "list_name": "Work",
  "taskseries_id": "string",
  "task_id": "string",
  "name": "Draft documentation",
  "notes": ["string"],
  "tags": ["p_commcenter_docs"],
  "due": "2026-06-01T00:00:00Z",
  "start": null,
  "priority": "2",
  "estimate": "1 hour",
  "url": null,
  "recurrence": null,
  "completed": null,
  "deleted": null,
  "state_hash": "sha256"
}
```

### 21.4 AI Task Proposal

```json
{
  "proposal_id": "uuid",
  "created_at": "2026-05-29T10:01:00Z",
  "model": "gemma-4-31b",
  "prompt_version": "task_maintenance_v1",
  "task_snapshot_id": "uuid",
  "classification": "clear_next_action",
  "confidence": 0.91,
  "risk": "safe",
  "changes": {},
  "reason": "string",
  "status": "pending | applied | rejected | blocked | failed"
}
```

### 21.5 Source Document

```json
{
  "source_document_id": "uuid",
  "uploaded_at": "2026-05-29T10:00:00Z",
  "filename": "meeting_transcript.txt",
  "file_type": "txt",
  "file_size_bytes": 123456,
  "content_hash": "sha256",
  "storage_path": "local-or-object-storage-path",
  "extracted_text_path": "local-or-object-storage-path",
  "extraction_status": "pending | extracted | failed",
  "extraction_error": null,
  "source_title": "Meeting Transcript",
  "source_date": "2026-05-28",
  "source_author": null,
  "detected_language": "en",
  "delete_original_after_extraction": true,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 21.6 Extracted Chunk

```json
{
  "chunk_id": "uuid",
  "source_document_id": "uuid",
  "chunk_index": 0,
  "text": "string",
  "page_start": null,
  "page_end": null,
  "line_start": 1,
  "line_end": 100,
  "timestamp_start": null,
  "timestamp_end": null,
  "token_estimate": 3000,
  "created_at": "datetime"
}
```

### 21.7 Action Proposal

```json
{
  "action_proposal_id": "uuid",
  "source_document_id": "uuid",
  "chunk_id": "uuid",
  "created_at": "2026-05-29T10:02:00Z",
  "model": "gemma-4-31b",
  "prompt_version": "action_extraction_v1",
  "candidate_task_name": "Email Pedro with CommCenter documentation review request",
  "candidate_list": "Work",
  "candidate_tags": ["p_commcenter_docs", "pedro", "followup", "next"],
  "candidate_due": null,
  "candidate_start": null,
  "candidate_priority": "2",
  "candidate_estimate": "15 min",
  "candidate_url": null,
  "candidate_note": "Source evidence and reason.",
  "source_evidence": "Pedro can review the documentation before we hand it over.",
  "source_location": {
    "page": null,
    "line_start": 84,
    "line_end": 87,
    "timestamp_start": null,
    "timestamp_end": null
  },
  "assignee": "user",
  "mentioned_people": ["Pedro"],
  "extraction_type": "task | followup | waiting | project_anchor | reminder | question",
  "confidence": 0.87,
  "risk": "safe | needs_review | blocked",
  "status": "pending | approved | rejected | edited | created_in_rtm | failed",
  "duplicate_status": "none | possible_duplicate | duplicate",
  "rtm_list_id": null,
  "rtm_taskseries_id": null,
  "rtm_task_id": null
}
```

### 21.8 Audit Log

```json
{
  "audit_id": "uuid",
  "timestamp": "2026-05-29T10:02:00Z",
  "event_type": "model_proposal | user_approval | user_rejection | rtm_write | blocked_action | failed_action",
  "entity_type": "task_snapshot | ai_task_proposal | source_document | action_proposal",
  "entity_id": "uuid",
  "old_value": {},
  "new_value": {},
  "source": "auto | user_approved | system",
  "model": "gemma-4-31b",
  "prompt_version": "string",
  "confidence": 0.91,
  "reason": "string",
  "api_result": "success | failure | blocked"
}
```

---

## 22. API Endpoints

### 22.1 Auth

```http
POST /api/login
POST /api/logout
GET /api/session
```

### 22.2 RTM Connection

```http
GET /api/rtm/auth-url
POST /api/rtm/callback
GET /api/rtm/status
POST /api/rtm/disconnect
```

### 22.3 Task Maintenance

```http
POST /api/tasks/sync
GET /api/tasks/snapshots
POST /api/reviews/daily
POST /api/reviews/weekly
GET /api/proposals/task-maintenance
POST /api/proposals/task-maintenance/{id}/approve
POST /api/proposals/task-maintenance/{id}/reject
POST /api/proposals/task-maintenance/{id}/edit
```

### 22.4 Action Intake

```http
POST /api/uploads
GET /api/uploads
GET /api/uploads/{id}
DELETE /api/uploads/{id}
POST /api/uploads/{id}/extract
GET /api/uploads/{id}/actions
POST /api/action-proposals/{id}/approve
POST /api/action-proposals/{id}/reject
POST /api/action-proposals/{id}/edit
POST /api/action-proposals/{id}/merge
POST /api/action-proposals/create-approved
```

### 22.5 Audit

```http
GET /api/audit
GET /api/audit/{id}
```

### 22.6 Settings

```http
GET /api/settings
PUT /api/settings
```

---

## 23. GitHub Pages Frontend Pages

### 23.1 Dashboard

Shows:

- RTM connection status
- backend connection status
- last daily run
- last weekly run
- pending task-maintenance review count
- pending extracted-action review count
- recent uploads
- recent RTM creations
- buttons:
  - Connect RTM
  - Run Daily Review
  - Run Weekly Review
  - Upload Files
  - View Review Queue
  - View Audit Log

### 23.2 Upload Files

Shows:

- drag-and-drop upload
- supported file types
- file size limit
- privacy setting:
  - retain original file
  - delete original after extraction
- upload progress
- extraction status

### 23.3 Source Document

Shows:

- document metadata
- extracted text preview
- extraction status
- candidate actions
- re-run extraction button
- delete source file button

### 23.4 Extracted Actions Review

Shows proposals grouped by source file.

For each proposal:

- proposed task name
- suggested list
- suggested tags
- suggested due date
- suggested start date
- suggested priority
- suggested estimate
- source evidence
- confidence
- risk level
- duplicate warning
- Gemma reason
- actions:
  - approve
  - reject
  - edit
  - merge
  - mark as already done
  - create in RTM

### 23.5 Task Maintenance Review

Shows proposed changes to existing RTM tasks.

For each proposal:

- current task
- proposed change
- model reason
- confidence
- risk
- approve/reject/edit buttons

### 23.6 Created Tasks

Shows:

- recently created RTM tasks
- source document
- RTM creation status
- tags/dates/priority applied
- audit details

### 23.7 Audit Log

Shows:

- timestamp
- event type
- task/proposal/source document
- old value
- new value
- source
- model
- result

### 23.8 Settings

Shows:

- backend API URL
- timezone
- confidence threshold
- auto-apply enabled/disabled
- default file retention
- default RTM list mappings
- allowed tags
- high-risk keywords

---

## 24. Daily Review Flow

1. User clicks “Run Daily Review” or scheduled job starts.
2. Backend fetches:
   - Inbox tasks
   - overdue tasks
   - tasks due today
   - Priority 1 and Priority 2 tasks
   - tasks tagged `ai_needs_clarification`
   - tasks tagged `waiting` or `followup`
3. Backend sends tasks to Gemma.
4. Gemma returns proposed actions.
5. Backend validates proposals.
6. Backend applies safe changes if enabled.
7. Backend stores review-required proposals.
8. Frontend displays daily summary.

Daily summary format:

```text
Reviewed 42 tasks.
Applied 18 safe cleanup changes.
Flagged 6 for review.
No change on 18.

Today’s likely focus:
1. Draft CommCenter local testing instructions
2. Email Germain with weekly report
3. Book gym trial session

Needs review:
- “Side hustle” is too vague.
- “Taxes” may need a real due date or clarification.
- Possible duplicate: “Review job postings” and “Look at US jobs.”

Waiting/follow-up:
- Follow up with Pedro on documentation review.
- Waiting for recruiter response.
```

---

## 25. Weekly Review Flow

1. User clicks “Run Weekly Review.”
2. Backend fetches:
   - all active project tags
   - project anchor tasks
   - tasks tagged `next`
   - tasks tagged `waiting`, `blocked`, `review`, `someday`
   - recently completed tasks if available
3. Gemma evaluates project health.
4. Backend flags projects missing next actions.
5. Backend identifies stale tasks and possible duplicates.
6. Backend produces recommended focus for next week.
7. Frontend displays weekly summary.

Weekly summary format:

```text
Active projects:

- CommCenter documentation
  Status: active
  Next action: Draft local testing instructions
  Risk: no usage guide task yet

- Job search 2027
  Status: active
  Next action: List 10 target companies
  Risk: no networking task this week

Projects missing next actions:
- Side hustle MVP
- Memos recap page

Stale or questionable tasks:
- “Look into old app idea”
- “Call someone about taxes”

Recommended focus next week:
1. Finish CommCenter handover draft
2. Create first side-hustle landing page
3. Lock in weekly lifting schedule
```

---

## 26. RTM Task Note Format for Extracted Actions

Every RTM task created from a file should include a note like this:

```text
Created by AI Action Intake

Source file: meeting_transcript.txt
Source type: transcript
Uploaded: 2026-05-29 10:00 Europe/Paris
Extracted action type: followup
Confidence: 0.87

Why this is a task:
The source implies the user should ask Pedro to review the CommCenter documentation before handover.

Evidence:
“Pedro can review the documentation before we hand it over.”

Source location:
Lines 84-87

Original suggested tags:
p_commcenter_docs, pedro, followup, next
```

---

## 27. Duplicate Detection

Before creating tasks in RTM, the app should check for possible duplicates.

Compare candidate task against:

- pending proposals from the same upload
- approved proposals from the same upload
- existing incomplete RTM tasks
- recently completed RTM tasks, if available

Duplicate signals:

- similar task name
- same project tag
- same person tag
- same due date
- overlapping source evidence
- same URL or source document

If a possible duplicate is found:

- do not auto-create
- mark `ai_possible_duplicate`
- show both tasks/proposals to the user
- allow merge or create anyway

---

## 28. Idempotency Requirements

The app must avoid noisy repeated changes.

Rules:

1. Do not add duplicate tags.
2. Do not append duplicate notes.
3. Do not rename if the new name is materially the same.
4. Do not repeatedly move the same task between lists.
5. Do not re-review unchanged tasks too often.
6. Store a hash of the task state at review time.
7. Skip tasks already tagged `ai_reviewed` if unchanged, unless overdue or explicitly selected.
8. Record model version and prompt version in the audit log.
9. Do not create duplicate tasks from the same source document unless user explicitly approves.

---

## 29. Error Handling

### RTM API Error

If RTM API call fails:

- log the error
- mark proposal as failed
- do not retry indefinitely
- show error in run summary

### LLM JSON Error

If Gemma returns invalid JSON:

- retry once with a stricter repair prompt
- if still invalid, fail the run
- do not apply changes from malformed output

### File Extraction Error

If extraction fails:

- mark source document as failed
- store error message
- show failure in UI
- do not send empty text to Gemma

### Validation Error

If proposal violates rules:

- mark proposal as blocked
- add reason
- show in review queue if useful

### State Mismatch

If RTM task changed after fetch:

- do not apply proposal
- mark proposal as stale
- refetch on next run

### Backend Offline

If frontend cannot reach backend:

- show backend offline state
- disable RTM and Gemma actions
- allow user to view cached frontend only if available

---

## 30. Security Requirements

1. Do not hardcode RTM API credentials.
2. Do not expose RTM shared secret to GitHub Pages.
3. Do not expose Gemma API key to GitHub Pages.
4. Store backend secrets in environment variables.
5. Do not log access tokens.
6. Require authentication before backend API access.
7. Restrict backend CORS to the GitHub Pages origin.
8. Use HTTPS only.
9. Store uploaded files securely.
10. Provide setting to delete original files after extraction.
11. Do not send unnecessary personal data to Gemma.
12. Store audit logs in backend database.
13. Provide a way to clear uploaded files and audit history.
14. Do not expose backend publicly without authentication.

---

## 31. Configuration

Backend environment variables:

```text
RTM_API_KEY=
RTM_SHARED_SECRET=
GEMMA_API_BASE_URL=
GEMMA_API_KEY=
GEMMA_MODEL=gemma-4-31b
APP_TIMEZONE=Europe/Paris
AUTO_APPLY_CONFIDENCE_THRESHOLD=0.85
DATABASE_URL=
SESSION_SECRET=
FRONTEND_ORIGIN=https://<username>.github.io
ENABLE_AUTO_APPLY=true
ENABLE_DAILY_SCHEDULE=false
ENABLE_WEEKLY_SCHEDULE=false
MAX_UPLOAD_MB=25
DELETE_ORIGINAL_FILES_AFTER_EXTRACTION=true
```

Frontend build variables:

```text
VITE_API_BASE_URL=https://<backend-domain>
VITE_APP_NAME=RTM AI Organizer
```

Do not place secrets in frontend build variables.

---

## 32. Recommended Tech Stack

### Frontend

- React
- Vite
- TypeScript
- Tailwind CSS
- GitHub Pages deployment
- GitHub Actions for frontend build/deploy

### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- HTTPX
- APScheduler or Cloud Scheduler for later scheduled jobs

### Database

- Postgres for hosted deployment
- SQLite only for local development

### File Parsing

MVP libraries:

- text/markdown: standard file read
- html/htm: BeautifulSoup
- eml: Python email parser
- pdf: PyMuPDF or pdfplumber
- srt/vtt: transcript parser or simple regex parser
- csv/json: standard Python libraries

### LLM

- Gemma 4 31B through selected inference provider
- JSON-only output enforced by prompt and schema validation

---

## 33. Implementation Milestones

### Milestone 1: Repository and Deployment Skeleton

- Create monorepo:
  - `frontend/`
  - `backend/`
  - `docs/`
- Set up React/Vite frontend.
- Deploy frontend to GitHub Pages.
- Set up FastAPI backend.
- Deploy backend to selected host.
- Configure CORS from GitHub Pages to backend.
- Add login/session flow.

### Milestone 2: RTM Read-Only Integration

- Implement RTM authentication.
- Fetch RTM lists.
- Fetch RTM tasks.
- Normalize RTM task JSON.
- Display connection status and task counts.

### Milestone 3: Database and Audit Foundation

- Add database.
- Add task snapshots.
- Add proposals.
- Add audit logs.
- Add settings table.

### Milestone 4: Task Maintenance Review

- Build daily review prompt.
- Send RTM tasks to Gemma.
- Validate JSON response.
- Display proposed changes.
- No writes yet.

### Milestone 5: Safe Auto-Apply

- Implement tag updates.
- Implement task renames.
- Implement list moves.
- Implement priority updates.
- Add safety validator.
- Add audit logging.

### Milestone 6: Review Queue

- Build review queue UI.
- Add approve/reject/edit flows.
- Apply approved proposals.
- Log user decisions.

### Milestone 7: File Upload and Text Extraction

- Add upload page.
- Store uploaded files.
- Extract text from MVP formats.
- Display extracted text preview.
- Store source document records.

### Milestone 8: Gemma Action Extraction

- Build action extraction prompt.
- Send extracted chunks to Gemma.
- Validate JSON output.
- Store candidate actions.
- Show proposals grouped by source document.

### Milestone 9: Create Approved RTM Tasks

- Add approve/edit/reject for extracted actions.
- Create approved tasks in RTM.
- Add tags, dates, priority, estimate, and notes.
- Store RTM identifiers.
- Log all creation results.

### Milestone 10: Weekly Project Review

- Fetch project-related tasks.
- Identify project tags.
- Generate project health summary.
- Flag projects missing next actions.

### Milestone 11: Polish and Settings

- Add settings page.
- Add file retention controls.
- Add manual prompt override for extraction.
- Add better error reporting.
- Add optional scheduled reviews.

---

## 34. Acceptance Criteria

### GitHub Pages Frontend

- Frontend is deployed and accessible through GitHub Pages.
- Frontend can connect to backend API.
- Frontend does not contain secret keys.
- Frontend shows backend offline state if API unavailable.

### Backend

- Backend requires authentication.
- Backend stores secrets securely.
- Backend restricts CORS to the GitHub Pages origin.
- Backend can call RTM API.
- Backend can call Gemma API.
- Backend can store audit logs.

### RTM Integration

- App can authenticate with RTM.
- App can fetch lists.
- App can fetch tasks.
- App can create tasks.
- App can update task fields.
- App handles RTM errors gracefully.

### Task Maintenance

- App can run a daily review.
- App can run a weekly review.
- Gemma returns structured proposals.
- App validates proposals.
- Safe changes can be applied automatically.
- Risky changes go to review.
- App does not delete, complete, or destructively change tasks without approval.
- App does not modify `do_not_touch` tasks.

### File Upload

- User can upload supported files.
- Unsupported files are rejected clearly.
- Duplicate files are detected by hash.
- Text extraction status is visible.
- Extracted text can be previewed.

### Action Extraction

- Gemma returns structured candidate actions.
- Every candidate action has source evidence.
- Every candidate action has confidence and risk.
- Ambiguous items are marked for review.
- Non-actionable content is not converted into tasks.
- No task is created from a file without user approval.

### Validation Dashboard

- User can approve, reject, edit, and merge proposals.
- User can inspect source evidence before approval.
- User can batch approve high-confidence low-risk proposals.
- User can prevent task creation for weak proposals.

### RTM Task Creation

- Approved actions can be created in RTM.
- Created tasks include name, list, tags, priority, dates, estimate, and notes when available.
- Source evidence is added to the RTM task note.
- RTM identifiers are stored locally.
- RTM creation failures are shown clearly.

### Auditability

- Every model proposal is logged.
- Every applied change is logged.
- Every rejected proposal is logged.
- Every blocked proposal is logged.
- User can inspect what changed and why.

---

## 35. Recommended MVP Defaults

```text
Frontend: GitHub Pages
Backend: FastAPI on GCP Cloud Run or Railway
Database: Postgres
LLM: Gemma 4 31B
Auto-apply maintenance changes: enabled only for safe changes
File intake task creation: always requires user approval
Audit log: backend database
Scheduling: manual first, optional later
Timezone: Europe/Paris
Confidence threshold: 0.85
Protected tag: do_not_touch
Original file retention: delete after extraction by default
```

Start with manual runs. Do not schedule automatic writes until the user has reviewed several runs and trusts the behavior.

---

## 36. Open Questions

1. Which backend host should be used: GCP Cloud Run, Railway, Render, Fly.io, or another service?
2. Which Gemma provider/runtime should be used?
3. Should original uploaded files be deleted immediately after extraction?
4. Should the app support browser-only extraction for privacy-sensitive documents?
5. Should GitHub authentication be used for app login?
6. Should daily reviews auto-apply safe changes from day one, or start in review-only mode?
7. Should completed RTM tasks be fetched for duplicate detection?
8. Should Smart Lists be created manually in RTM or managed by the app?
9. Should there be a natural-language “quick add” box in the dashboard?
10. Should the backend support direct email ingestion in a later version?

---

## 37. Definition of Done for MVP

The MVP is complete when:

1. The dashboard is available through GitHub Pages.
2. The backend is deployed and authenticated.
3. The frontend can communicate with the backend.
4. The user can connect Remember The Milk.
5. The app can fetch current RTM tasks.
6. The app can run a daily task review.
7. Gemma can return structured maintenance proposals.
8. The app can validate proposals.
9. The app can safely apply low-risk RTM edits.
10. Risky edits go to a review queue.
11. The user can upload supported files.
12. The app can extract text from uploaded files.
13. Gemma can extract candidate actions from files.
14. The user can approve, reject, or edit extracted actions.
15. Approved extracted actions can be created as RTM tasks.
16. Created RTM tasks include source notes.
17. Every proposal, approval, rejection, and RTM write is audit logged.
18. The app does not expose secrets in GitHub Pages.
19. The app does not create or modify high-risk tasks without approval.
20. The app generates useful daily and weekly summaries.

---

## 38. Source Notes

This PRD relies on the following implementation constraints:

- GitHub Pages is static hosting for HTML, CSS, and JavaScript, so backend functionality must run elsewhere.
- Remember The Milk API calls require signed requests for most methods, and write methods such as task creation require authentication and a timeline.
- RTM write operations should be handled by the backend because they require credentials and signed requests.
- GitHub Actions secrets are useful for deployment workflows, but they do not make runtime secrets safe to expose in browser JavaScript.
