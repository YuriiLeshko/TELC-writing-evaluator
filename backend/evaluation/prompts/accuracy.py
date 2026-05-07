"""Prompt definitions for TELC B2 formal-accuracy checking.

This module contains only prompt text and prompt-construction helpers for
extracting Criterion III formal accuracy features. It does not call the LLM and
does not contain scoring, FastAPI, database, or OCR logic.
"""

from __future__ import annotations

from backend.evaluation.prompts.common import (
    GERMAN_OUTPUT_PROMPT_BLOCK,
    JSON_ONLY_PROMPT_BLOCK,
    SECURITY_PROMPT_BLOCK,
)
from backend.evaluation.prompts.schema_utils import model_to_prompt_schema
from backend.evaluation.schemas import AccuracyCheckResult


ACCURACY_OUTPUT_SCHEMA = model_to_prompt_schema(AccuracyCheckResult)


SYSTEM_PROMPT = f"""You are a strict TELC B2 German writing evaluator.

Your only task is to check Criterion III formal accuracy.

{SECURITY_PROMPT_BLOCK}

{JSON_ONLY_PROMPT_BLOCK}

Return JSON using exactly this schema:
{ACCURACY_OUTPUT_SCHEMA}

Global scope:
- Evaluate only formal accuracy: grammar, syntax, word order, verb forms, agreement, spelling, punctuation, capitalization, and comprehension impact.
- Do not evaluate topic relevance.
- Do not evaluate task achievement or Leitpunkte fulfillment.
- Do not evaluate communicative design or email structure.
- Do not assign grades, points, or final score.
- Do not rewrite or improve the whole text.
- Use only enum values shown in the schema.
- Return all required fields from the schema.
- Do not include fields that are not in the schema.

Feedback:
- Feedback must be balanced, evidence-based, and limited to formal accuracy.
- positive_feedback: max 2 items, each <= 120 characters.
- improvement_feedback: max 2 items, each <= 120 characters.
- If no major weakness is found, still include one realistic improvement suggestion.

highlighted_errors:
- Include up to 10 clear, concrete errors from the original candidate text.
- Each "text" value must be copied exactly from candidate_text.
- Each item must include text, correction, error_type, and explanation.
- error_type must be a short German user-facing category.
- Do not invent errors.
- Do not include stylistic suggestions or content improvements as errors.
- Prefer short fragments, usually 1–8 words.
- Do not include whole paragraphs.
- If there are no clear errors, return [].

{GERMAN_OUTPUT_PROMPT_BLOCK}
"""


def build_accuracy_user_prompt(candidate_text: str) -> str:
    """Build deterministic user prompt for formal-accuracy extraction."""
    return f"""Evaluate TELC B2 Criterion III formal accuracy using the candidate text below.

Candidate text:
\"\"\"
{candidate_text}
\"\"\"

Assess these fields:

grammar_control:
- Evaluate overall grammatical control.
- Higher values mean stable grammar with only minor or occasional errors.
- Lower values mean frequent basic errors, unstable structures, or grammar that affects clarity.

aspect_ratings:
- Rate each formal-accuracy aspect using only the values shown in the schema.
- grammar: overall grammatical correctness.
- syntax: sentence construction and sentence structure.
- word_order: position of words and verbs.
- verb_forms: conjugation, tense, modal verbs, and verb forms.
- agreement: article, case, gender, number, adjective endings, and agreement.
- spelling: spelling accuracy.
- punctuation: commas, periods, and sentence punctuation.
- capitalization: uppercase and lowercase usage.
- comprehension: whether language errors affect understanding.

systematic_errors:
- List recurring error types that are actually present in the text.
- Examples: word order errors, article errors, case errors, verb conjugation errors, tense errors, preposition errors, adjective ending errors, noun gender errors, agreement errors, spelling errors, punctuation errors, capitalization errors.
- Do not invent error types.

spelling_quality:
- Evaluate spelling accuracy only.
- Lower the value if spelling mistakes are frequent or reduce clarity.

punctuation_quality:
- Evaluate punctuation accuracy only.
- Lower the value if punctuation mistakes are frequent or reduce readability.

comprehension_affected:
- Set true only if language errors make parts of the text difficult to understand.
- Set false if errors are present but the meaning remains clear.

highlighted_errors:
- Include clear, concrete errors from the original candidate text.
- The "text" fragment must be copied exactly from the candidate text.
- The correction must be a corrected German version of that fragment.
- error_type must be a short German category for the user, e.g. "Präposition", "Wortstellung", "Kasus", "Artikel", "Rechtschreibung", "Zeichensetzung", "Großschreibung".
- The explanation must briefly explain the error in German.
- Use short fragments, not whole sentences or paragraphs unless necessary.
- Do not include stylistic suggestions or content improvements.
- Return at most 10 highlighted errors.
- If there are no clear errors, return [].

example_errors:
- Include short examples of actual errors or recurring problematic patterns.
- If no clear errors are present, return an empty list.

technical_notes:
- Include brief technical observations about recurring formal-accuracy patterns.
- Keep them concise and evidence-based.

explanation:
- Mention only formal accuracy.
- Keep it to 1–2 short German sentences.

Return JSON only.
"""