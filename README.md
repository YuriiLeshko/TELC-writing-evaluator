# TELC Writing Evaluator

**Easily scalable MVP** for TELC B2–style German writing practice: seed a task bank, run a criterion-aligned evaluation pipeline via OpenRouter, show scores + feedback in a React SPA. Swap models, grow tasks/users, or harden auth without rewriting the core loop.

> Training aid — not official TELC marking. Live: [app](https://telc-writing-evaluator-9tee.onrender.com) · [API](https://telc-writing-evaluator.onrender.com/docs)

---

## What is TELC?

**TELC** (*The European Language Certificates*) is a widely used system of standardized language exams aligned with the CEFR. In German, **TELC Deutsch B2** includes a **written expression** part (*Schriftlicher Ausdruck*): the candidate writes one formal-style text — typically an **email asking for information** or a **complaint** — from a short prompt with fixed content points (*Leitpunkte*).

Examiners do **not** give a single “gut/schlecht” mark. They score three criteria separately (bands **A / B / C / D** → 5 / 3 / 1 / 0 points), then combine them:

**Final score = (I + II + III) × 3** · max **45**

Full rubric we implement: [`task_examples&criteria/criteria.md`](task_examples&criteria/criteria.md).

### The three criteria

| # | Name | What it measures |
| - | ---- | ---------------- |
| **I** | **Task Achievement** (*Aufgabenbewältigung*) | Did the writer cover the required key points, develop them adequately, at roughly B2 level? Wrong topic → usually all D; wrong situation → I = D, II/III still scored. |
| **II** | **Communicative Design** (*Kommunikative Gestaltung*) | Structure of the email, coherence/cohesion, register (formal vs informal), sentence variety — is it readable as a real message to the intended recipient? |
| **III** | **Formal Accuracy** (*Formale Richtigkeit*) | Grammar, syntax, spelling, punctuation, etc. — how correct is the German, and does error load hurt comprehension? |

Pre-check before I–III: **relevance** (topic + communicative situation). If the text misses the topic entirely, grading short-circuits to D/D/D.

---

## Value

| Need | What this MVP delivers |
| ---- | ---------------------- |
| Repeatable exam practice | Paired info + complaint tasks, timer, archive |
| Criterion-shaped feedback | Same I / II / III logic as above, not a vague “AI grade” |
| Cheap iteration | JSON task seed, demo auth, SQLite — grow when needed |
| Reliable LLM use | Structured evidence in, rule-based scores out |

Auth is demo-fixed today (`user@example.com` / `admin@example.com`); evaluation and API are separated so JWT or another DB can slot in later.

---

## Evaluation workflow

```
submitted text
    │
    ▼
① Relevance (topic / situation)     ← topic miss → D/D/D, stop
    │
    ▼
② Key points        → Criterion I   ┐
③ Communication     → Criterion II  ├─ LLM extractors (②–④ concurrent after ①)
④ Accuracy          → Criterion III ┘
    │
    ▼
⑤ Deterministic scoring             ← A/B/C/D → points; Final = (I+II+III)×3
    │
    ▼
⑥ Improved text (optional LLM) + structured result JSON
```

---

## LLM + anti-hallucination (Pydantic)

Models are **not** asked for a final grade. They only fill **typed evidence** validated by Pydantic; Python assigns A/B/C/D and the final score.

```
LLM JSON  →  Pydantic.model_validate(...)  →  deterministic scoring.py
```

| Control | How |
| ------- | --- |
| **Schema as contract** | Each checker maps to a model (`RelevanceCheckResult`, `KeyPointCheckResult`, …) with `extra="forbid"`, `Literal[...]` enums, field validators |
| **Prompts from schemas** | `model_to_prompt_schema()` prints the same Pydantic shape into the prompt — one source of truth |
| **Hard reject** | `model_validate` on every response; invalid/extra fields fail (retries / schema-repair hint where needed) |
| **Scores offline** | Grades and final formula live in `scoring.py`, not in model prose |
| **Low temperature** | Extractors typically `temperature=0.0` |

---

## What’s in the product

- **Training** — start session, pick info or complaint (~20 each, seeded), write, submit  
- **Result** — score (max 45), criterion cards, highlights, suggested rewrite  
- **Archive / Profile / Admin** — history, counters, task CRUD (demo admin)  
- **Assessment guide** — in-app rubric explanation  

---

## Layout

```
backend/evaluation/   # pipeline, checks, scoring, prompts, Pydantic schemas
backend/routers/      # sessions, submissions, users, admin
backend/seed_tasks/   # JSON task bank
frontend/src/         # React SPA (pages + result UI)
docs/                 # local setup, testing, deploy, API contract
```

Stack: FastAPI · SQLAlchemy/SQLite · React/Vite · OpenRouter.

---

## Docs & quick start

[Local](docs/local-development.md) · [Testing](docs/testing.md) · [Deploy](docs/deployment.md) · [API](docs/api_contract.md) · [Triage](TRIAGE.md)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
# .env: OPENROUTER_API_KEY, MODEL_NAME, FALLBACK_MODEL_NAME
PYTHONPATH=. uvicorn backend.main:app --reload

cd frontend && npm install && npm run dev
```
