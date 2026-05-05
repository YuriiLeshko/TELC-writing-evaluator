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
  "explanation": "string",
  "positive_feedback": ["string"],
  "improvement_feedback": ["string"],
  "key_point_details": [
    {
      "key_point": "string",
      "covered": true,
      "status": "fulfilled | partially_fulfilled | not_fulfilled",
      "coverage_quality": "strong | adequate | weak | missing",
      "sentence_count": 0,
      "development": "detailed | sufficient | too_short | unclear | missing",
      "relevance": "direct | partial | irrelevant",
      "situation_appropriate": true,
      "language_level": "B2 | B1+ | B1 | A2 | null",
      "comment": "Kurzer Kommentar auf Deutsch"
    }
  ]
}

Scope restrictions:
- Do NOT evaluate grammar.
- Do NOT evaluate spelling or punctuation.
- Do NOT evaluate communicative design.
- Do NOT assign criterion grades or points.
- Do NOT calculate final score.
- Feedback must be balanced and evidence-based:
  - always include positive_feedback and improvement_feedback
  - if weaknesses are limited, still provide one realistic improvement suggestion
  - do not invent missing points or errors
  - return at most 2 items in positive_feedback
  - return at most 2 items in improvement_feedback
  - each feedback item must be <= 120 characters
You must write all explanations, feedback, and comments strictly in German (Deutsch).
Do not use English words or sentences.
Do not mix German and English.
Your output must be entirely in German except for JSON field names.
If any part of the explanation is in English, the response is invalid.
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

key_point_details:
- Return exactly one object per expected key point.
- Use original expected key point wording exactly or very close.
- Do not invent expected key points.
- sentence_count = estimated number of candidate sentences that address this key point.
- covered=true only if the point is adequately fulfilled.
- status:
  - fulfilled: clearly developed, relevant, situation-appropriate, beyond one sentence, sufficiently detailed, B2/B1+ acceptable content
  - partially_fulfilled: mentioned but too short, vague, weakly developed, or only partly relevant
  - not_fulfilled: missing, irrelevant, unclear, or inappropriate
- coverage_quality:
  - strong = clear, detailed, direct
  - adequate = sufficient but not very detailed
  - weak = too general or underdeveloped
  - missing = not present
- development:
  - detailed = clearly developed beyond one sentence
  - sufficient = enough for TELC task but could be richer
  - too_short = only brief mention
  - unclear = hard to understand
  - missing = absent
- relevance:
  - direct = directly answers the key point
  - partial = only partly answers
  - irrelevant = does not answer
- situation_appropriate=false if content does not fit the communicative situation.
- language_level must estimate the language used for that point.
- comment must be concise German and evidence-based.

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
  "explanation": "Kurze Erklärung auf Deutsch (1–2 Sätze)",
  "positive_feedback": ["string"],
  "improvement_feedback": ["string"],
  "key_point_details": [
    {{
      "key_point": "string",
      "covered": true,
      "status": "fulfilled | partially_fulfilled | not_fulfilled",
      "coverage_quality": "strong | adequate | weak | missing",
      "sentence_count": 0,
      "development": "detailed | sufficient | too_short | unclear | missing",
      "relevance": "direct | partial | irrelevant",
      "situation_appropriate": true,
      "language_level": "B2 | B1+ | B1 | A2 | null",
      "comment": "Kurzer Kommentar auf Deutsch"
    }}
  ]
}}

The explanation must be short and mention only task achievement / key-point fulfillment.
Feedback focus:
- positive_feedback: clearly fulfilled and developed task points
- improvement_feedback: missing, underdeveloped, unclear, or overly general points
Feedback limits:
- positive_feedback: max 2 items, each <= 120 chars
- improvement_feedback: max 2 items, each <= 120 chars
Language requirements:
- All explanations must be written in German.
- Use clear and simple German sentences suitable for B2 learners.
- Maximum 1–2 sentences per explanation.
- Do not include English words.
- Each feedback item must be in German.
- Maximum 1 sentence per feedback item.
Return JSON only.
"""
