"""Prompt definitions for TELC B2 formal-accuracy checking.

This module contains only prompt text and prompt-construction helpers for
extracting Criterion III formal accuracy features. It does not call the LLM and
does not contain scoring, FastAPI, database, or OCR logic.
"""

from __future__ import annotations

SYSTEM_PROMPT = """You are a strict TELC B2 German writing evaluator.
Your only task is to check formal accuracy.

Output requirements:
- Return only valid JSON.
- Do not use markdown.
- Do not output any text outside JSON.
- Use exactly this schema:
{
  "grammar_control": "strong | good | unstable | basic",
  "systematic_errors": ["string"],
  "spelling_quality": "good | acceptable | poor",
  "punctuation_quality": "good | acceptable | poor",
  "comprehension_affected": boolean,
  "explanation": "string"
}

Scope restrictions:
- Do NOT evaluate topic relevance.
- Do NOT evaluate task achievement.
- Do NOT evaluate communicative design.
- Do NOT assign grades or points.
- Do NOT calculate final score.
"""


def build_accuracy_user_prompt(candidate_text: str) -> str:
    """Build deterministic user prompt for formal-accuracy extraction."""
    return f"""Evaluate TELC B2 formal accuracy using ONLY the rules below.

Candidate text:
\"\"\"
{candidate_text}
\"\"\"

Evaluate these fields:

grammar_control:
Allowed values:
- "strong"
- "good"
- "unstable"
- "basic"
Use:
- "strong" if the text shows strong grammatical control, no systematic errors, and only minor mistakes.
- "good" if grammar is generally good, with few systematic errors, and comprehension is not hindered.
- "unstable" if grammar is adequate but inconsistent, with several systematic errors, but the text remains mostly understandable.
- "basic" if there are frequent basic errors, incorrect sentence structures, tense confusion, agreement errors, or parts are difficult to understand.

systematic_errors:
List recurring/systematic error types found in the text.
Possible examples:
- word order errors
- article errors
- case errors
- verb conjugation errors
- tense errors
- preposition errors
- adjective ending errors
- noun gender errors
- agreement errors
- spelling errors
- punctuation errors
- capitalization errors
- sentence structure errors
Only include errors that are actually present.
Do not invent errors.

spelling_quality:
Allowed values:
- "good"
- "acceptable"
- "poor"
Use:
- "good" if spelling is mostly correct.
- "acceptable" if there are some spelling mistakes, but they do not seriously affect understanding.
- "poor" if spelling errors are frequent or phonetic and reduce clarity.

punctuation_quality:
Allowed values:
- "good"
- "acceptable"
- "poor"
Use:
- "good" if punctuation is mostly correct.
- "acceptable" if there are some punctuation mistakes but the text remains clear.
- "poor" if punctuation mistakes are frequent and reduce readability.

comprehension_affected:
boolean
Set true only if language errors make parts of the text difficult to understand.
Set false if errors are present but the meaning is still clear.

Important constraints:
- Do not correct the text.
- Do not rewrite the text.
- Do not evaluate content or task fulfillment.
- Do not evaluate email structure.
- Do not assign grades.
- Do not calculate points.
- Be strict for TELC B2, but do not punish content issues here.
- Grammar mistakes should be evaluated here, not in Criterion II.

Required output JSON structure:
{{
  "grammar_control": "strong | good | unstable | basic",
  "systematic_errors": ["string"],
  "spelling_quality": "good | acceptable | poor",
  "punctuation_quality": "good | acceptable | poor",
  "comprehension_affected": boolean,
  "explanation": "string"
}}

The explanation must be short and mention only formal accuracy.
Return JSON only.
"""
