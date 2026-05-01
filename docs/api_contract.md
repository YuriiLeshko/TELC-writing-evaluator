# TELC Writing Evaluator API Contract (MVP)

Base URL (local): `http://127.0.0.1:8000`

API title: `TELC Writing Evaluator API`

Content type: `application/json`

---

## Authentication Model (current MVP)

Current auth is **demo-based** (no JWT yet):

- User context is resolved by backend helper:
  - demo user: `user@example.com` (fallback username: `user`)
- Admin context is resolved by backend helper:
  - demo admin: `admin@example.com`

Because of this, frontend does not send tokens yet.

---

## Common Response Schemas

### UserRead

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "user",
  "role": "user",
  "is_active": true,
  "available_sessions": 5,
  "available_submissions": 5
}
```

### InfoTaskRead

```json
{
  "id": 1,
  "task_number": 1,
  "source_text": "string",
  "situation_text": "string",
  "instruction_text": "string",
  "expected_key_points": ["string"]
}
```

### ComplaintTaskRead

```json
{
  "id": 1,
  "task_number": 1,
  "source_text": "string",
  "situation_text": "string",
  "instruction_text": "string",
  "expected_key_points": ["string"]
}
```

### TaskSessionRead

```json
{
  "id": 10,
  "started_at": "2026-04-30T12:00:00Z",
  "submitted_at": null,
  "duration_seconds": null,
  "selected_task_type": null,
  "status": "started",
  "info_task": { "id": 1, "task_number": 1, "source_text": "string", "situation_text": "string", "instruction_text": "string", "expected_key_points": ["string"] },
  "complaint_task": { "id": 1, "task_number": 1, "source_text": "string", "situation_text": "string", "instruction_text": "string", "expected_key_points": ["string"] }
}
```

### SubmissionRead

```json
{
  "id": 100,
  "task_session_id": 10,
  "selected_task_type": "info",
  "selected_task_id": 1,
  "candidate_text": "string",
  "result": {},
  "raw_score": 9,
  "final_score": 27,
  "max_score": 45,
  "word_count": 162,
  "started_at": "2026-04-30T12:00:00Z",
  "submitted_at": "2026-04-30T12:05:00Z",
  "duration_seconds": 300,
  "status": "success",
  "error_message": null
}
```

---

## Default

### GET `/health`

Response `200`:

```json
{ "status": "ok" }
```

---

## Users

Prefix: `/users`

### GET `/users/me`

Returns current demo user.

- `200`: `UserRead`
- `401`: `"Demo user not found. Run backend/seed.py first."`
- `403`: `"User is inactive."`

### POST `/users/register`

Create a new regular user.

Request body:

```json
{
  "email": "new@example.com",
  "username": "newuser",
  "password": "plain-text-mvp"
}
```

Response:

- `201`: `UserRead`
- `400`: `"Email already exists."`

### PATCH `/users/me`

Update own email and/or password.

Request body (at least one field):

```json
{
  "email": "updated@example.com",
  "password": "new-password"
}
```

Response:

- `200`: `UserRead`
- `400`: `"Email already exists."`
- `401`/`403`: same as `/users/me`

### DELETE `/users/me`

Delete own account (hard delete).

Response `200`:

```json
{ "status": "deleted" }
```

---

## Task Sessions

Prefix: `/task-sessions`

### POST `/task-sessions/start`

Starts a new session for the current user:

- Picks one **random** active `InfoTask` the user has not yet received (not referenced by any existing `TaskSession` for that user).
- Picks one **random** active `ComplaintTask` under the same rule (independent draw).
- Updates `available_sessions -= 1`.

If every active info task (or every active complaint task) already appears in some session for this user, the request fails with `404`.

Response `200`:

```json
{
  "session": { "id": 10, "started_at": "2026-04-30T12:00:00Z", "submitted_at": null, "duration_seconds": null, "selected_task_type": null, "status": "started", "info_task": {}, "complaint_task": {} },
  "display_title": "Modelltest 10"
}
```

Errors:

- `403`: `"User is inactive."`
- `403`: `"No available task sessions left."`
- `404`: `"No unused tasks available for this user (all active tasks were already used)."`

### GET `/task-sessions/my`

Returns all current user sessions, newest first.

- `200`: `TaskSessionRead[]`

### GET `/task-sessions/active`

Returns current user sessions with `status == "started"`, newest first.

- `200`: `TaskSessionRead[]`

### GET `/task-sessions/{session_id}`

Returns one session owned by current user.

- `200`: `TaskSessionRead`
- `404`: `"Task session not found."`

### DELETE `/task-sessions/{session_id}`

Delete own session only when `status == "started"`.

Response `200`:

```json
{ "status": "deleted", "session_id": 10 }
```

Errors:

- `404`: `"Task session not found."`
- `400`: `"Submitted sessions cannot be deleted."`

---

## Submissions

Prefix: `/submissions`

### POST `/submissions/evaluate`

Evaluates submitted text and creates a `Submission`.

Request body:

```json
{
  "task_session_id": 10,
  "selected_task_type": "info",
  "candidate_text": "string"
}
```

On success:

- marks session as submitted
- sets `submitted_at`, `duration_seconds`, `selected_task_type`, `selected_task_id`
- decrements `available_submissions` by 1

Response `200`:

```json
{
  "submission_id": 100,
  "task_session_id": 10,
  "selected_task_type": "info",
  "selected_task_id": 1,
  "result": {}
}
```

Errors:

- `403`: `"User is inactive."`
- `403`: `"No available submissions left."`
- `404`: `"Task session not found."`
- `400`: `"Session already submitted."`
- `500`: `"Evaluation failed."`

### GET `/submissions/my`

Returns all current user submissions, newest first.

- `200`: `SubmissionRead[]`

### GET `/submissions/active`

Current implementation returns same list as `/submissions/my`.

- `200`: `SubmissionRead[]`

### GET `/submissions/{submission_id}`

Returns one submission owned by current user.

- `200`: `SubmissionRead`
- `404`: `"Submission not found."`

### DELETE `/submissions/{submission_id}`

Delete own submission.

Response `200`:

```json
{ "status": "deleted", "submission_id": 100 }
```

Error:

- `404`: `"Submission not found."`

---

## Admin

Prefix: `/admin`

All endpoints require demo admin helper.

Auth-related errors:

- `401`: `"Demo admin not found. Run backend/seed.py first."`
- `403`: `"Admin access required."`
- `403`: `"Admin user is inactive."`

### Users Management

#### GET `/admin/users`

- `200`: `UserRead[]`

#### GET `/admin/users/{user_id}`

- `200`: `UserRead`
- `404`: `"User not found."`

#### POST `/admin/users`

Request body:

```json
{
  "email": "x@example.com",
  "username": "x",
  "password": "plain-text-mvp",
  "role": "user",
  "available_sessions": 5,
  "available_submissions": 5,
  "is_active": true
}
```

- `200`: `UserRead`
- `400`: `"Email already exists."`

#### PATCH `/admin/users/{user_id}`

Partial update supported for:

- `email`
- `username`
- `role`
- `is_active`
- `available_sessions`
- `available_submissions`

- `200`: `UserRead`
- `404`: `"User not found."`
- `400`: `"Email already exists."`

#### DELETE `/admin/users/{user_id}`

- hard delete if no related sessions/submissions
- otherwise sets `is_active = false`

Responses:

```json
{ "status": "deleted" }
```

or

```json
{ "status": "deactivated" }
```

#### PATCH `/admin/users/{user_id}/counters`

Request:

```json
{
  "available_sessions": 10,
  "available_submissions": 12
}
```

- `200`: `UserRead`
- `404`: `"User not found."`

#### PATCH `/admin/users/{user_id}/activate`

- `200`: `UserRead`
- `404`: `"User not found."`

#### PATCH `/admin/users/{user_id}/deactivate`

- `200`: `UserRead`
- `404`: `"User not found."`

---

### Info Tasks Management

#### GET `/admin/info-tasks`

- `200`: `InfoTaskRead[]`

#### POST `/admin/info-tasks`

Request:

```json
{
  "task_number": 2,
  "source_text": "string",
  "situation_text": "string",
  "instruction_text": "string",
  "expected_key_points": ["string"],
  "is_active": true
}
```

- `200`: `InfoTaskRead`
- `400`: `"Info task number already exists."`

#### GET `/admin/info-tasks/{task_id}`

- `200`: `InfoTaskRead`
- `404`: `"Info task not found."`

#### PATCH `/admin/info-tasks/{task_id}`

Partial update:

- `task_number`
- `source_text`
- `situation_text`
- `instruction_text`
- `expected_key_points`
- `is_active`

- `200`: `InfoTaskRead`
- `404`: `"Info task not found."`
- `400`: `"Info task number already exists."`

#### DELETE `/admin/info-tasks/{task_id}`

Soft delete via `is_active = false`.

```json
{ "status": "deactivated", "task_id": 2 }
```

---

### Complaint Tasks Management

#### GET `/admin/complaint-tasks`

- `200`: `ComplaintTaskRead[]`

#### POST `/admin/complaint-tasks`

Request:

```json
{
  "task_number": 2,
  "source_text": "string",
  "situation_text": "string",
  "instruction_text": "string",
  "expected_key_points": ["string"],
  "is_active": true
}
```

- `200`: `ComplaintTaskRead`
- `400`: `"Complaint task number already exists."`

#### GET `/admin/complaint-tasks/{task_id}`

- `200`: `ComplaintTaskRead`
- `404`: `"Complaint task not found."`

#### PATCH `/admin/complaint-tasks/{task_id}`

Partial update:

- `task_number`
- `source_text`
- `situation_text`
- `instruction_text`
- `expected_key_points`
- `is_active`

- `200`: `ComplaintTaskRead`
- `404`: `"Complaint task not found."`
- `400`: `"Complaint task number already exists."`

#### DELETE `/admin/complaint-tasks/{task_id}`

Soft delete via `is_active = false`.

```json
{ "status": "deactivated", "task_id": 2 }
```

---

## Frontend Notes

- Use `/users/me` to render current counters:
  - `available_sessions`
  - `available_submissions`
- To start workflow:
  1. `POST /task-sessions/start`
  2. user chooses `info` or `complaint`
  3. `POST /submissions/evaluate`
- Current API is demo-auth driven; replace with JWT flow in next phase.
