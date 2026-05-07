"""Prompt definitions for TELC B2 key-points task-achievement check.

This module defines prompt text and prompt-construction helpers for extracting
fulfilled key points, relevant own ideas, and invalid points. It does not call
an LLM and does not contain scoring, FastAPI, database, or OCR logic.
"""

from __future__ import annotations

from backend.evaluation.prompts.common import (
    GERMAN_OUTPUT_PROMPT_BLOCK,
    JSON_ONLY_PROMPT_BLOCK,
    SECURITY_PROMPT_BLOCK,
)
from backend.evaluation.prompts.schema_utils import model_to_prompt_schema
from backend.evaluation.schemas import KeyPointCheckResult


KEY_POINTS_OUTPUT_SCHEMA = model_to_prompt_schema(KeyPointCheckResult)


SYSTEM_PROMPT = f"""You are a strict TELC B2 writing evaluator.

Your only task is to check Criterion I task achievement through expected key points and relevant own ideas.

{SECURITY_PROMPT_BLOCK}

{JSON_ONLY_PROMPT_BLOCK}

Return JSON using exactly this schema:
{KEY_POINTS_OUTPUT_SCHEMA}

Scope:
- Evaluate only task achievement, content relevance, situation appropriateness, and key-point development.
- Do not evaluate grammar, spelling, punctuation, communicative design, grades, points, or final score.
- Ignore grammar mistakes unless they make the content impossible to understand.
- Feedback must be evidence-based and limited to task achievement.
- positive_feedback: max 2 items, each <= 120 characters.
- improvement_feedback: max 2 items, each <= 120 characters.
- If weaknesses are limited, still include one realistic improvement suggestion.

{GERMAN_OUTPUT_PROMPT_BLOCK}
"""


def build_key_points_user_prompt(
    task_text: str,
    expected_key_points: list[str],
    candidate_text: str,
) -> str:
    """Build deterministic user prompt for key-point achievement extraction."""
    expected_key_points_block = "\n".join(
        f"{index}. {item}" for index, item in enumerate(expected_key_points, start=1)
    )

    return f"""Evaluate TELC B2 Criterion I task achievement using only the rules below.

Task text:
\"\"\"
{task_text}
\"\"\"

Expected key points:
{expected_key_points_block}

Candidate text:
\"\"\"
{candidate_text}
\"\"\"

Your task:
- Analyze whether each expected key point is addressed in the candidate text.
- Estimate how many candidate sentences actually develop each expected key point.
- Identify relevant additional own ideas.
- Identify missing, unclear, underdeveloped, irrelevant, or inappropriate content points.
- Do not assign grades or points.

Decision rules:

1) Expected key point status

For each expected key point, choose exactly one status:

- fulfilled:
  The key point is clearly addressed, relevant, situation-appropriate, and sufficiently developed in content.

- partially_fulfilled:
  The key point is relevant but too short, vague, incomplete, weakly developed, only partly relevant, or not detailed enough.

- not_fulfilled:
  The key point is missing, irrelevant, unclear, impossible to understand, or inappropriate to the communicative situation.

Important:
- You must estimate sentence_count carefully.
- sentence_count means: the number of candidate sentences that actually develop this specific key point.
- Count only sentences that add meaningful content to the key point.
- Do not count greetings, closings, generic filler, repeated phrases, or unrelated sentences.
- If one sentence covers several key points, count it only where it meaningfully develops the point.
- The final deterministic sentence-count rule is applied after your output by the checker.

2) fulfilled_key_points

Include expected key points that are clearly fulfilled by content.
Use the original expected key point wording.

3) own_ideas

Include only additional candidate ideas that are:
- not repetitions of expected key points;
- relevant to the task;
- appropriate to the communicative situation;
- useful for the communicative goal;
- clearly developed.

Do not include:
- greetings or closings;
- generic filler;
- undeveloped emotional reactions;
- repetitions of expected key points;
- irrelevant information.

4) invalid_points

Include content points that are:
- missing;
- underdeveloped;
- unclear;
- too general;
- irrelevant;
- inappropriate to the communicative situation.

5) key_point_details

Return exactly one key_point_details object for each expected key point.
Do not include own ideas in key_point_details.
Use the expected key point order and numbering.

For every expected key point:
- number: use 1..N according to the expected key point list.
- type: always "expected".
- key_point: use the original expected key point wording.
- status: "fulfilled", "partially_fulfilled", or "not_fulfilled".
- sentence_count: estimate how many candidate sentences actually develop this key point.
- situation_appropriate: true, false, or null.
- language_level: "B2", "B1+", "B1", "A2", or null.
- comment: short, evidence-based German comment.

Consistency rules:
- fulfilled_key_points should match key_point_details where status is "fulfilled".
- Do not invent expected key points.
- Do not include own ideas in key_point_details.
- Do not assign grades.
- Do not calculate points.
- Ignore grammar mistakes unless they make the content impossible to understand.
- Be strict but fair.

Explanation:
- Mention only task achievement and key-point fulfillment.
- Keep it short.

Feedback focus:
- positive_feedback: clearly addressed and developed task points.
- improvement_feedback: missing, underdeveloped, unclear, or overly general points.

Return JSON only.
"""