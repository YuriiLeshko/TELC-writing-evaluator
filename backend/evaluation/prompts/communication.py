"""Prompt definitions for TELC B2 communicative-design checking.

This module contains only prompt text and prompt-construction helpers for
extracting Criterion II communication features. It does not call the LLM and
does not contain scoring, FastAPI, database, or OCR logic.
"""

from __future__ import annotations

from backend.evaluation.prompts.common import (
    GERMAN_OUTPUT_PROMPT_BLOCK,
    JSON_ONLY_PROMPT_BLOCK,
    SECURITY_PROMPT_BLOCK,
)
from backend.evaluation.prompts.schema_utils import model_to_prompt_schema
from backend.evaluation.schemas import CommunicationCheckResult


COMMUNICATION_OUTPUT_SCHEMA = model_to_prompt_schema(CommunicationCheckResult)


SYSTEM_PROMPT = f"""You are a strict TELC B2 writing evaluator.

Your only task is to check Criterion II communicative design.

{SECURITY_PROMPT_BLOCK}

{JSON_ONLY_PROMPT_BLOCK}

Return JSON using exactly this schema:
{COMMUNICATION_OUTPUT_SCHEMA}

Important constraints:
- Evaluate only communicative design: email structure, coherence, cohesion, register, vocabulary level, and sentence variety.
- Do not evaluate task achievement or Leitpunkte fulfillment.
- Do not evaluate formal accuracy as Criterion III.
- Do not assign grades, points, or final score.
- Grammar mistakes must not lower communicative design directly unless they harm coherence or comprehension.
- Use only enum values shown in the schema.
- Return all required fields from the schema.
- Do not include fields that are not in the schema.

communication_indicators:
- Provide one indicator for each communication aspect shown in the schema.
- Use the same rating scale as shown in the schema.
- Each indicator comment must be one short, evidence-based German sentence.

{GERMAN_OUTPUT_PROMPT_BLOCK}
"""


REPAIR_INSTRUCTION = """Your previous response was invalid.
Return only valid JSON matching the required schema.
Use only enum values shown in the schema.
Do not use markdown.
Do not add text outside JSON.
"""


def build_communication_user_prompt(task_text: str, candidate_text: str) -> str:
    """Build deterministic user prompt for communicative-design extraction."""
    return f"""Evaluate TELC B2 Criterion II communicative design using the task and candidate text below.

Task text:
\"\"\"
{task_text}
\"\"\"

Candidate text:
\"\"\"
{candidate_text}
\"\"\"

Assess these fields:

email_structure_quality:
- Evaluate the overall email structure.
- Consider subject line, greeting, introduction, logical body, conclusion/request/next step, and closing formula.
- Lower the rating if important email parts are missing or the structure is unclear.

coherence_quality:
- Evaluate logical order, clarity, progression, and whether the reader can follow the text easily.
- Lower the rating if the text is list-like, repetitive, poorly ordered, contradictory, or difficult to follow.

cohesion_quality:
- Evaluate how well sentences and ideas are connected.
- Consider linking devices such as außerdem, deshalb, trotzdem, jedoch, deswegen, zuerst, danach, schließlich, weil, obwohl, dass, wenn.
- Do not require many connectors, but check whether ideas are connected clearly.

register_quality:
- Evaluate whether the tone fits the recipient and communicative situation.
- Formal or semi-formal tasks require a suitable polite register.
- Lower the rating if the text is too informal, too direct, rude, or inconsistent in tone.

vocabulary_level:
- Estimate the vocabulary level using only the level values shown in the schema.
- Consider range, precision, appropriateness, and usefulness for B2 written communication.
- Do not evaluate spelling accuracy here.

sentence_variety_quality:
- Evaluate variety of sentence structures, not grammatical correctness as such.
- Consider subordinate clauses, e.g. weil, dass, wenn, obwohl, damit.
- Consider connectors, e.g. deshalb, trotzdem, außerdem, jedoch, daher.
- Consider varied sentence openings, modal constructions, infinitive constructions, and repetition of patterns.
- Lower the rating if the text mostly uses short, repetitive main-clause structures.

communication_indicators:
- Each comment must focus only on its own aspect: email structure, organization, logical flow, linking, register, vocabulary, or sentence variety.
- Do not comment on spelling or grammar unless they harm coherence or comprehension.
- Do not assign grades or points.

explanation:
- Mention only the overall communicative design.
- Keep it to 1–2 short German sentences.

Return JSON only.
"""