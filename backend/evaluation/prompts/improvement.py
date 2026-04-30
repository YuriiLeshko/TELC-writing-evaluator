"""Prompt definitions for improved TELC B2 text generation.

This module contains only prompt text and prompt-construction helpers for
generating an improved candidate text. It does not call the LLM and does not
contain scoring, FastAPI, database, or OCR logic.
"""

from __future__ import annotations

from backend.evaluation.schemas import (
    AccuracyCheckResult,
    CommunicationCheckResult,
    KeyPointCheckResult,
    WritingEvaluationInput,
)

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


def _format_list(title: str, items: list[str]) -> str:
    """Format a short bullet list section for prompt context."""
    if not items:
        return f"{title}:\n- (keine)"
    return f"{title}:\n" + "\n".join(f"- {item}" for item in items[:5])


def build_improvement_user_prompt(
    input_data: WritingEvaluationInput,
    key_points_result: KeyPointCheckResult | None = None,
    communication_result: CommunicationCheckResult | None = None,
    accuracy_result: AccuracyCheckResult | None = None,
) -> str:
    """Build the improvement prompt from validated input data."""
    expected_key_points_block = "\n".join(f"- {item}" for item in input_data.expected_key_points)
    evidence_sections: list[str] = []

    if key_points_result is not None:
        evidence_sections.extend(
            [
                "Leitpunkt-Feedback aus der Auswertung:",
                _format_list("Stärken", key_points_result.positive_feedback),
                _format_list("Verbesserungen", key_points_result.improvement_feedback),
            ]
        )

    if communication_result is not None:
        evidence_sections.extend(
            [
                "Kommunikations-Feedback aus der Auswertung:",
                _format_list("Stärken", communication_result.positive_feedback),
                _format_list("Verbesserungen", communication_result.improvement_feedback),
            ]
        )

    if accuracy_result is not None:
        evidence_sections.extend(
            [
                "Sprachrichtigkeits-Feedback aus der Auswertung:",
                _format_list("Stärken", accuracy_result.positive_feedback),
                _format_list("Verbesserungen", accuracy_result.improvement_feedback),
                _format_list("Wiederkehrende Fehler", accuracy_result.systematic_errors),
                _format_list("Beispiel-Fehler", accuracy_result.example_errors),
                _format_list("Technische Hinweise", accuracy_result.technical_notes),
            ]
        )
        if accuracy_result.highlighted_errors:
            span_lines = [
                (
                    f"- Fehler: \"{item.text}\" | Korrektur: \"{item.correction}\" "
                    f"| Typ: {item.error_type}"
                )
                for item in accuracy_result.highlighted_errors[:10]
            ]
            evidence_sections.append(
                "Gezielte Fehlerstellen aus dem Original (genau diese Stellen korrigieren):\n"
                + "\n".join(span_lines)
            )

    evidence_block = "\n\n".join(evidence_sections) if evidence_sections else "Keine zusätzlichen Auswertungsdaten vorhanden."
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

Zusätzliche Auswertungshinweise (verwende sie als Priorität für Korrekturen):
{evidence_block}

Anforderungen an den verbesserten Text:
- Nur Deutsch verwenden.
- Bedeutung und Absicht des Originals erhalten.
- Keine konkreten Fakten erfinden.
- Register und Format passend zur Aufgabe beibehalten.
- Grammatik, Rechtschreibung, Zeichensetzung und Kohärenz verbessern.
- Wenn möglich auf mindestens 150 Wörter ausbauen, aber nur mit sicheren, allgemeinen Details.
- Berücksichtige die oben genannten Fehler und Empfehlungen gezielt.
- Wenn konkrete Fehlerstellen angegeben sind, korrigiere diese konsistent im verbesserten Text.

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
