"""Prompt definitions for TELC B2 key-points task-achievement check.

This module defines prompt text and prompt-construction helpers for extracting
fulfilled key points, relevant own ideas, and invalid points. It does not call
an LLM and does not contain scoring, FastAPI, database, or OCR logic.
"""

from __future__ import annotations

SYSTEM_PROMPT = """You are a strict TELC B2 writing evaluator.
Your only task is to check task achievement through key points.

Output requirements:
- Return only valid JSON.
- Do not use markdown.
- Do not output any text outside JSON.
- Use exactly this schema:
{
  "fulfilled_key_points": ["string"],
  "own_ideas": ["string"],
  "invalid_points": ["string"],
  "explanation": "string"
}

Scope restrictions:
- Do NOT evaluate grammar.
- Do NOT evaluate spelling or punctuation.
- Do NOT evaluate communicative design.
- Do NOT assign criterion grades or points.
- Do NOT calculate final score.
"""


def build_key_points_user_prompt(
    task_text: str,
    expected_key_points: list[str],
    candidate_text: str,
) -> str:
    """Build deterministic user prompt for key-point achievement extraction."""
    expected_key_points_block = "\n".join(f"- {item}" for item in expected_key_points)

    return f"""Evaluate TELC B2 task achievement using ONLY the rules below.

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

Decision rules:

fulfilled_key_points:
Include an expected key point only if it is:
- directly relevant to the task
- appropriate to the communicative situation
- developed beyond one sentence
- sufficiently detailed
- at B2 content level

Do NOT count a key point as fulfilled if it is:
- only mentioned briefly
- only implied
- too general
- unclear
- irrelevant
- inappropriate to the situation
- not developed enough

own_ideas:
Include only relevant additional ideas that are:
- not part of expected_key_points
- appropriate to the task
- clearly developed
- useful for the communicative goal
- at B2 content level

Do NOT count as own idea:
- repetition of expected key points
- generic filler
- greeting or closing
- emotional reaction without development
- irrelevant information

invalid_points:
Include:
- expected key points that were missing
- expected key points that were mentioned but not adequately developed
- candidate ideas that were irrelevant, unclear, too general, or inappropriate

Important constraints:
- Use the same or very close wording from expected_key_points when listing fulfilled_key_points.
- Do not invent expected key points.
- Do not assign grades.
- Do not calculate points.
- Ignore grammar mistakes unless they make content impossible to understand.
- Be strict but fair.

Required output JSON structure:
{{
  "fulfilled_key_points": ["string"],
  "own_ideas": ["string"],
  "invalid_points": ["string"],
  "explanation": "string"
}}

The explanation must be short and mention only task achievement / key-point fulfillment.
Return JSON only.
"""
