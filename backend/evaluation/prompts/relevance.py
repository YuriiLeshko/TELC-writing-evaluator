"""Prompt definitions for TELC B2 relevance pre-check.

This module contains only prompt text and prompt-construction helpers for the
relevance checker. It does not call any LLM API and does not contain scoring,
FastAPI, database, or OCR logic.
"""

from __future__ import annotations

from backend.evaluation.prompts.common import (
    GERMAN_OUTPUT_PROMPT_BLOCK,
    JSON_ONLY_PROMPT_BLOCK,
    SECURITY_PROMPT_BLOCK,
)
from backend.evaluation.prompts.schema_utils import model_to_prompt_schema
from backend.evaluation.schemas import RelevanceCheckResult


RELEVANCE_OUTPUT_SCHEMA = model_to_prompt_schema(RelevanceCheckResult)


SYSTEM_PROMPT = f"""You are a strict TELC B2 writing evaluator.

Your only task is to check:
1) topic relevance (Thema verfehlt)
2) communicative situation relevance (Situierung verfehlt)

{SECURITY_PROMPT_BLOCK}

{JSON_ONLY_PROMPT_BLOCK}

Return JSON using exactly this schema:
{RELEVANCE_OUTPUT_SCHEMA}

Scope:
- Do not evaluate grammar, spelling, punctuation, style, vocabulary, Leitpunkte fulfillment, grades, points, or final score.
- Missing or incomplete Leitpunkte are not a relevance mismatch.
- Feedback must be evidence-based, balanced, and limited to topic/situation relevance.
- positive_feedback: max 2 items, each <= 120 characters.
- improvement_feedback: max 2 items, each <= 120 characters.
- If there is no major weakness, still include one realistic improvement suggestion.

{GERMAN_OUTPUT_PROMPT_BLOCK}
"""


def build_relevance_user_prompt(
    task_text: str,
    expected_key_points: list[str],
    candidate_text: str,
) -> str:
    """Build deterministic user prompt for topic/situation relevance check."""
    key_points_text = "\n".join(f"- {point}" for point in expected_key_points)

    return f"""Evaluate TELC B2 writing relevance using only the rules below.

Task text:
\"\"\"
{task_text}
\"\"\"

Expected key points for context only:
\"\"\"
{key_points_text}
\"\"\"

Candidate text:
\"\"\"
{candidate_text}
\"\"\"

Decision rules:

1) topic_mismatch = true only if:
- the candidate text is unrelated or barely related to the task.

Do not set topic_mismatch = true because:
- the text is short;
- grammar is poor;
- email elements are missing;
- style is weak;
- some expected key points are missing or incomplete.

2) situation_mismatch = true only if:
- the general topic is relevant,
- but the communicative situation is wrong.

Examples of situation mismatch:
- formal complaint email required, but the candidate writes informally to a friend;
- email required, but the candidate writes a general essay;
- specific scenario required, but the candidate writes only general opinions;
- institution/company recipient required, but the candidate writes to the wrong recipient type.

Important:
- Expected key points are context only.
- Do not evaluate Leitpunkte fulfillment here.
- If topic_mismatch = true, then situation_mismatch must also be true.
- If the candidate addresses the task scenario, even imperfectly, do not mark topic_mismatch.
- Be strict but fair.

Feedback focus:
- what matches the topic and communicative situation;
- what would make the topic/situation match clearer.

Return JSON only.
"""