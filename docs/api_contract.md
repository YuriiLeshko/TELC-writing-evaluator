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
  "available_submissions": 5,
  "next_info_task_index": 1,
  "next_complaint_task_index": 1
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

Frontend-relevant fields for archive/detail navigation:

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
  "duration_seconds": 300,
  "submitted_at": "2026-04-30T12:05:00Z",
  "status": "success",
  "error_message": null
}
```

Notes:
- `raw_score` and `final_score` may be `null` when evaluation finished with `result.analysis_status` `"partial"` or `"failed"` (see evaluation result shape below).
- `duration_seconds` is expected on `SubmissionRead` and used as duration fallback in result display.
- Archive detail flow passes `submission` to `/result` route state.

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

Update own `username`, `email`, and/or `password`.

Request body (at least one field):

```json
{
  "username": "updated-user",
  "email": "updated@example.com",
  "password": "new-password"
}
```

Notes:
- If `password` is empty (`""`), password is not changed.
- Admin-only fields are ignored on this endpoint (`role`, `is_active`, counters, next-task indexes).

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

Starts a new session for current user using:

- `InfoTask.task_number == user.next_info_task_index`
- `ComplaintTask.task_number == user.next_complaint_task_index`

Also updates:

- `available_sessions -= 1`
- `next_info_task_index += 1`
- `next_complaint_task_index += 1`

Response `200`:

```json
{
  "session": { "id": 10, "started_at": "2026-04-30T12:00:00Z", "submitted_at": null, "duration_seconds": null, "selected_task_type": null, "status": "started", "info_task": {}, "complaint_task": {} },
  "display_title": "Modelltest 10"
}
```

Timing behavior:
- `started_at` is set when the session is created by `POST /task-sessions/start`.
- The timer starts at session creation time, not when the user confirms task choice.
- `submitted_at` and `duration_seconds` remain `null` until a successful submission.
- `duration_seconds` is computed as `int((submitted_at - started_at).total_seconds())`.

Errors:

- `403`: `"User is inactive."`
- `403`: `"No available task sessions left."`
- `404`: `"No more tasks available for this user."`

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
- stores the same timing triplet in both `TaskSession` and `Submission`:
  - `started_at`
  - `submitted_at`
  - `duration_seconds`

Response `200` (frontend-facing contract; values reflect `WritingEvaluationResult` after API shaping — see `backend/routers/submissions.py` `_sanitize_result_for_api`):

```json
{
  "submission_id": 100,
  "task_session_id": 10,
  "selected_task_type": "info",
  "selected_task_id": 1,
  "result": {
    "topic_mismatch": false,
    "situation_mismatch": false,
    "analysis_status": "success",
    "analysis_error": null,
    "criterion_I": {
      "grade": "B",
      "points": 3,
      "scaled_points": 9,
      "max_scaled_points": 15,
      "comment": "Aufgabenerfüllung auf B2-Niveau mit kleinen Lücken.",
      "analysis_status": "success",
      "analysis_error": null,
      "task_achievement_summary": {
        "fulfilled_count": 2,
        "partially_fulfilled_count": 1,
        "not_fulfilled_count": 1,
        "own_idea_count": 0,
        "overall_level": "B1+",
        "summary_comment": "2 erfüllt, 1 teilweise erfüllt, 1 nicht erfüllt."
      },
      "key_point_details": [
        {
          "number": 1,
          "type": "expected",
          "key_point": "Problem beschreiben",
          "status": "fulfilled",
          "sentence_count": 2,
          "situation_appropriate": true,
          "language_level": "B2",
          "comment": "Klar und passend formuliert."
        }
      ]
    },
    "criterion_II": {
      "grade": "B",
      "points": 3,
      "scaled_points": 9,
      "max_scaled_points": 15,
      "comment": "Kommunikation ist insgesamt gut nachvollziehbar.",
      "analysis_status": "success",
      "analysis_error": null,
      "communication_indicators": [
        {
          "aspect": "coherence",
          "label": "Zusammenhang",
          "rating": "acceptable",
          "comment": "Teilweise klare Verknüpfung der Aussagen."
        }
      ]
    },
    "criterion_III": {
      "grade": "C",
      "points": 1,
      "scaled_points": 3,
      "max_scaled_points": 15,
      "comment": "Formale Korrektheit schwankt, Verständlichkeit bleibt erhalten.",
      "analysis_status": "success",
      "analysis_error": null,
      "aspect_ratings": {
        "grammar": "adequate",
        "syntax": "strong",
        "word_order": "adequate",
        "verb_forms": "adequate",
        "agreement": "adequate",
        "spelling": "adequate",
        "punctuation": "adequate",
        "capitalization": "adequate",
        "comprehension": "weak"
      },
      "highlighted_errors": [
        {
          "text": "ein Kopfhörer",
          "correction": "einen Kopfhörer",
          "error_type": "Kasusfehler",
          "explanation": "Nach dem Verb steht hier der Akkusativ."
        }
      ]
    },
    "word_count": {
      "value": 162,
      "minimum_required": 150,
      "meets_requirement": true
    },
    "raw_score": 8,
    "final_score": 24,
    "max_score": 45,
    "improved_text": {
      "improved_text": "Sehr geehrte Damen und Herren, ..."
    }
  }
}
```

Required response fields:
- `submission_id`
- `task_session_id`
- `selected_task_type`
- `selected_task_id`
- `result`

Required `result` fields (successful full evaluation):
- `topic_mismatch` (`true` = Thema unpassend; dann werden die drei Kriterien inhaltlich mit D bewertet, die Endnote wird dennoch berechnet — siehe `criteria.md`)
- `situation_mismatch` (`true` = Situation unpassend)
- `analysis_status` (`success` | `partial` | `failed`)
- `analysis_error` (`string | null`; bei `partial` / `failed` oft gesetzt)
- `criterion_I`
- `criterion_II`
- `criterion_III`
- `word_count`
- `max_score`
- `improved_text`

Scores (nullable bei partial/failed):
- `raw_score` (`int | null`)
- `final_score` (`int | null`): `null` wenn mindestens ein Kriterium technisch **nicht** ausgewertet wurde (`analysis_status` `"partial"` oder `"failed"`).

Optional `result` fields:
- `duration_seconds` (optional in `result`; frontend currently falls back to `submission.duration_seconds`)

#### `result.criterion_I` (Aufgabenerfüllung)

Required (wenn Analyse für dieses Kriterium erfolgreich):
- `grade` (`A` \| `B` \| `C` \| `D`; bei technischem Fehler `null`)
- `points` (`0`–`5`; bei technischem Fehler `null`)
- `scaled_points` / `max_scaled_points` (oft `null`, wenn `analysis_status` dieses Kriteriums `failed`)
- `comment`
- `analysis_status` (`success` \| `failed`)
- `analysis_error` (`string | null`; bei `failed` mit erklärendem Text)
- `task_achievement_summary`
- `key_point_details`

`task_achievement_summary` fields:
- `fulfilled_count`
- `partially_fulfilled_count`
- `not_fulfilled_count`
- `own_idea_count`
- `overall_level`
- `summary_comment`

`key_point_details[]` fields:
- `number`
- `type`
- `key_point`
- `status`
- `sentence_count`
- `situation_appropriate`
- `language_level`
- `comment`

#### `result.criterion_II` (Kommunikative Gestaltung)

Required:
- `grade` / `points` (bei `analysis_status: failed` beide `null`; es wird **keine** automatische D-Note für technische Fehler vergeben)
- `scaled_points` / `max_scaled_points`
- `comment`
- `analysis_status` (`success` | `failed`)
- `analysis_error` (`string | null`)
- `communication_indicators`

`communication_indicators[]` fields:
- `aspect` (`email_elements`, `structure`, `coherence`, `cohesion`, `register`, `vocabulary`, `sentence_variety`)
- `label`
- `rating` (`excellent`, `good`, `acceptable`, `weak`, `missing`)
- `comment`

#### `result.criterion_III` (Formale Korrektheit)

Required:
- `grade` / `points` (wie Kriterium II bei technischem Fehler)
- `scaled_points` / `max_scaled_points`
- `comment`
- `analysis_status` (`success` \| `failed`)
- `analysis_error` (`string \| null`)
- `aspect_ratings` (Objekt oder `null`; bei erfolgreicher Analyse die Teilaspekte direkt aus der Sprachprüfung)
- `highlighted_errors`

`aspect_ratings` keys (jeweils `strong` \| `adequate` \| `weak` \| `problematic`):
- `grammar`, `syntax`, `word_order`, `verb_forms`, `agreement`, `spelling`, `punctuation`, `capitalization`, `comprehension`

Hinweis: Das veraltete Feld `accuracy_details` wird von der API nicht mehr ausgeliefert.

`highlighted_errors[]` fields:
- `text`
- `correction`
- `error_type`
- `explanation`

Constraints:
- `text` must be an exact short fragment from `candidate_text` (not whole paragraphs).
- Maximum `10` highlighted errors; if no clear errors exist, return `[]`.

#### `result.word_count`

Required:
- `value`
- `minimum_required`
- `meets_requirement`

#### `result.improved_text`

Required:
- `improved_text` (full improved German text only)

Timing source for `duration_seconds`:
- Primary source: `submission.duration_seconds`.
- Computed from task-session lifecycle:
  - session/submission `started_at` (when session starts),
  - session/submission `submitted_at` (when evaluate succeeds),
  - `duration_seconds = int(submitted_at - started_at)` in seconds.

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

Action semantics:
- **Deactivate** = soft status change (`is_active = false`).
- **Activate** = status change (`is_active = true`).
- **Delete** = hard deletion from database (only when entity is not already used).

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
- `next_info_task_index`
- `next_complaint_task_index`

- `200`: `UserRead`
- `404`: `"User not found."`
- `400`: `"Email already exists."`

#### DELETE `/admin/users/{user_id}`

- hard delete only if no related sessions/submissions
- if related sessions/submissions exist: request is rejected, user is not modified
- admin cannot delete themselves
- admin users cannot be deleted

Responses:

```json
{ "status": "deleted" }
```

or

- `409`: `"User cannot be deleted because related sessions or submissions exist. Deactivate the user instead."`
- `400`: `"Admin cannot delete themselves."`
- `403`: `"Admin users cannot be deleted."`

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
  "source_text": "string",
  "situation_text": "string",
  "instruction_text": "string",
  "expected_key_points": ["string"]
}
```

Notes:
- `task_number` is auto-assigned by backend (`max(task_number) + 1` per task type).
- Frontend should not send `task_number` when creating a task.
- New tasks are created as inactive by default (`is_active = false`).
- Frontend should not send `is_active` during create.

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

Hard delete (record removal) only for unused tasks.

```json
{ "status": "deleted", "task_id": 2 }
```

- `409`: `"Task cannot be deleted because it is already used. Deactivate it instead."`

#### PATCH `/admin/info-tasks/{task_id}/deactivate`

Soft deactivate task (`is_active = false`).

- `200`: `InfoTaskRead`
- `404`: `"Info task not found."`

#### PATCH `/admin/info-tasks/{task_id}/activate`

Reactivate task (`is_active = true`).

- `200`: `InfoTaskRead`
- `404`: `"Info task not found."`

---

### Complaint Tasks Management

#### GET `/admin/complaint-tasks`

- `200`: `ComplaintTaskRead[]`

#### POST `/admin/complaint-tasks`

Request:

```json
{
  "source_text": "string",
  "situation_text": "string",
  "instruction_text": "string",
  "expected_key_points": ["string"]
}
```

Notes:
- `task_number` is auto-assigned by backend (`max(task_number) + 1` per task type).
- Frontend should not send `task_number` when creating a task.
- New tasks are created as inactive by default (`is_active = false`).
- Frontend should not send `is_active` during create.

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

Hard delete (record removal) only for unused tasks.

```json
{ "status": "deleted", "task_id": 2 }
```

- `409`: `"Task cannot be deleted because it is already used. Deactivate it instead."`

#### PATCH `/admin/complaint-tasks/{task_id}/deactivate`

Soft deactivate task (`is_active = false`).

- `200`: `ComplaintTaskRead`
- `404`: `"Complaint task not found."`

#### PATCH `/admin/complaint-tasks/{task_id}/activate`

Reactivate task (`is_active = true`).

- `200`: `ComplaintTaskRead`
- `404`: `"Complaint task not found."`

---

## Frontend Notes

- To start workflow:
  1. `POST /task-sessions/start`
  2. user chooses `info` or `complaint`
  3. `POST /submissions/evaluate`
- Current API is demo-auth driven; replace with JWT flow in next phase.
- Archive compatibility:
  - "Details anzeigen" in archive navigates to `/result`.
  - Route state passes `result`, `candidate_text`, `submission`, and (when available) `session`, `selectedTaskType`, `selectedTask`.
