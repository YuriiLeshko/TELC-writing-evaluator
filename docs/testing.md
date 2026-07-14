# Testing

Backend tests use **pytest**. From the repository root, activate the venv and install dev dependencies:

```bash
pip install -r requirements-dev.txt
```

Tests inject safe dummy LLM env values in `backend/tests/conftest.py`, so a real OpenRouter key is not required to run the suite.

## Run all backend tests

```bash
PYTHONPATH=. pytest backend/tests
```

## Coverage

**Terminal summary** (overall % per file and missing lines):

```bash
PYTHONPATH=. pytest backend/tests --cov=backend --cov-report=term-missing
```

**HTML report** (open `htmlcov/index.html`):

```bash
PYTHONPATH=. pytest backend/tests \
  --cov=backend \
  --cov-report=term-missing \
  --cov-report=html
```

**Machine-readable** (e.g. CI) — writes `coverage.xml` in the repo root:

```bash
PYTHONPATH=. pytest backend/tests --cov=backend --cov-report=xml
```

Coverage artifacts (`htmlcov/`, `.coverage`, `coverage.xml`) are ignored via `.gitignore` where listed.

## What the suite covers

Rough map of `backend/tests/`:

| Area | Examples |
| ---- | -------- |
| API | users, task sessions, submissions, admin |
| Evaluation | pipeline, checkers, scoring, improvement, result builder |
| Prompts / schemas | prompt builders, schema validation |
| Data | seed idempotency, database models |
| LLM client | client behaviour with mocks / isolation |

Config: `pytest.ini` at the repo root.
