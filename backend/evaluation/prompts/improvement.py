"""Prompt definitions for improved TELC B2 text generation.

This module contains only prompt text and prompt-construction helpers for
generating an improved candidate text. It does not call the LLM and does not
contain scoring, FastAPI, database, or OCR logic.
"""

from __future__ import annotations

from backend.evaluation.schemas import WritingEvaluationInput

SYSTEM_PROMPT = """You are a TELC B2 German writing coach.
Improve the candidate text while preserving its original meaning.

Rules:
- Do not invent facts.
- Do not invent order numbers, dates, names, prices, product details, or events.
- Keep the text suitable for TELC B2, not C1/C2.
- Keep email format if the task requires email.
- Improve grammar, spelling, punctuation, structure, register, coherence, and B2 style.
- If the original text is below 150 words, expand only with safe, generic, realistic details
  that do not invent specific facts.

Output rules:
- Return only valid JSON.
- Do not output markdown.
- Do not output text outside JSON.
- All output text must be in German except JSON field names.
"""


def build_improvement_user_prompt(input_data: WritingEvaluationInput) -> str:
    """Build the improvement prompt from validated input data."""
    expected_key_points_block = "\n".join(f"- {item}" for item in input_data.expected_key_points)
    return f"""Verbessere den folgenden Text nach den Regeln.

Aufgabentext:
\"\"\"
{input_data.task_text}
\"\"\"

Erwartete Leitpunkte:
{expected_key_points_block}

Kandidatentext:
\"\"\"
{input_data.candidate_text}
\"\"\"

Anforderungen an den verbesserten Text:
- Nur Deutsch verwenden.
- Bedeutung und Absicht des Originals erhalten.
- Keine konkreten Fakten erfinden.
- Register und Format passend zur Aufgabe beibehalten.
- Grammatik, Rechtschreibung, Zeichensetzung und Kohärenz verbessern.
- Wenn möglich auf mindestens 150 Wörter ausbauen, aber nur mit sicheren, allgemeinen Details.

Erforderliches JSON-Format:
{{
  "improved_text": "string",
  "changes_summary": ["string"]
}}

Regeln für improved_text:
- Nur Deutsch.
- B2-Niveau.
- Passendes formelles/halbformelles Register je nach Aufgabe.
- Keine erfundenen spezifischen Fakten.

Regeln für changes_summary:
- Nur Deutsch.
- 2 bis 4 kurze Punkte.
- Nur allgemeine Änderungen nennen, z. B.:
  - "Grammatik und Satzbau verbessert"
  - "Formellen Stil verstärkt"
  - "Textstruktur klarer gemacht"
"""
