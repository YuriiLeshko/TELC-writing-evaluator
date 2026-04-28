"""Prompt definitions for TELC B2 communicative-design checking.

This module contains only prompt text and prompt-construction helpers for
extracting Criterion II communication features. It does not call the LLM and
does not contain scoring, FastAPI, database, or OCR logic.
"""

from __future__ import annotations

SYSTEM_PROMPT = """You are a strict TELC B2 writing evaluator.
Your only task is to check communicative design.

Output requirements:
- Return only valid JSON.
- Do not use markdown.
- Do not output any text outside JSON.
- Use exactly this schema:
{
  "has_subject": boolean,
  "has_greeting": boolean,
  "has_introduction": boolean,
  "has_body_structure": boolean,
  "has_conclusion": boolean,
  "has_closing": boolean,
  "register_quality": "appropriate | mostly_appropriate | inappropriate",
  "coherence_quality": "strong | good | acceptable | weak | incoherent",
  "vocabulary_level": "B2 | B1+ | B1 | A2",
  "sentence_variety": "varied | some_variety | simple",
  "explanation": "string"
}

Scope restrictions:
- Do NOT evaluate task achievement.
- Do NOT evaluate formal accuracy.
- Do NOT assign grades or points.
- Do NOT calculate final score.
"""


def build_communication_user_prompt(task_text: str, candidate_text: str) -> str:
    """Build deterministic user prompt for communicative-design extraction."""
    return f"""Evaluate TELC B2 communicative design using ONLY the rules below.

Task text:
\"\"\"
{task_text}
\"\"\"

Candidate text:
\"\"\"
{candidate_text}
\"\"\"

Evaluate these boolean fields:

has_subject:
true only if there is a recognizable subject line / Betreff.

has_greeting:
true only if there is a recognizable greeting / Anrede.

has_introduction:
true if the email has an opening sentence that introduces the reason for writing.

has_body_structure:
true if the main content is organized logically, not just random fragments.

has_conclusion:
true if there is a closing sentence before the final formula, e.g. request for response, summary, expectation, next step.

has_closing:
true only if there is a recognizable closing formula, e.g. "Mit freundlichen Grüßen".

Evaluate these categorical fields:

register_quality:
Allowed values:
- "appropriate"
- "mostly_appropriate"
- "inappropriate"
Use:
- "appropriate" if the register fits the task consistently, e.g. formal/semi-formal email to customer service.
- "mostly_appropriate" if the register is mostly suitable but has minor inconsistencies.
- "inappropriate" if the register clearly does not fit the situation.

coherence_quality:
Allowed values:
- "strong"
- "good"
- "acceptable"
- "weak"
- "incoherent"
Use:
- "strong" if the text has a clear logical flow, convincing progression, and well-connected ideas.
- "good" if the text is clear and logically organized with minor weaknesses.
- "acceptable" if the text is understandable and mostly ordered but simple.
- "weak" if the text is list-like, repetitive, poorly connected, or weakly structured.
- "incoherent" if the text is illogical or difficult to follow.

vocabulary_level:
Allowed values:
- "B2"
- "B1+"
- "B1"
- "A2"
Use:
- "B2" if vocabulary is varied, precise, and suitable for B2 written communication.
- "B1+" if vocabulary is adequate but not fully B2.
- "B1" if vocabulary is simple, repetitive, or limited.
- "A2" if vocabulary is very limited and basic.

sentence_variety:
Allowed values:
- "varied"
- "some_variety"
- "simple"
Use:
- "varied" if the text uses varied sentence structures and linking devices.
- "some_variety" if there is some complexity but also repetition.
- "simple" if the text mostly uses short/simple/repetitive structures.

Important constraints:
- Grammar mistakes must not lower communicative design directly unless they harm coherence.
- Do not evaluate whether all Leitpunkte are fulfilled.
- Do not evaluate formal accuracy as Criterion III.
- Do not assign grades.
- Do not calculate points.
- Be strict but fair.

Required output JSON structure:
{{
  "has_subject": boolean,
  "has_greeting": boolean,
  "has_introduction": boolean,
  "has_body_structure": boolean,
  "has_conclusion": boolean,
  "has_closing": boolean,
  "register_quality": "appropriate | mostly_appropriate | inappropriate",
  "coherence_quality": "strong | good | acceptable | weak | incoherent",
  "vocabulary_level": "B2 | B1+ | B1 | A2",
  "sentence_variety": "varied | some_variety | simple",
  "explanation": "string"
}}

The explanation must be short and mention only communicative design.
Return JSON only.
"""
