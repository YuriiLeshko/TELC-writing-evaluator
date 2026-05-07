"""Prompt definitions for improved TELC B2 text generation.

This module contains only prompt text and prompt-construction helpers for
generating an improved candidate text. It does not call the LLM and does not
contain scoring, FastAPI, database, or OCR logic.
"""

from __future__ import annotations

from backend.evaluation.prompts.common import (
    GERMAN_OUTPUT_PROMPT_BLOCK,
    JSON_ONLY_PROMPT_BLOCK,
    SECURITY_PROMPT_BLOCK,
)
from backend.evaluation.prompts.schema_utils import model_to_prompt_schema
from backend.evaluation.schemas import (
    AccuracyCheckResult,
    CommunicationCheckResult,
    ImprovedTextResult,
    KeyPointCheckResult,
    WritingEvaluationInput,
)


IMPROVEMENT_OUTPUT_SCHEMA = model_to_prompt_schema(ImprovedTextResult)


SYSTEM_PROMPT = f"""You are a TELC B2 German writing coach.

Your only task is to produce an improved German full text as the sole JSON field `improved_text`.

{SECURITY_PROMPT_BLOCK}

{JSON_ONLY_PROMPT_BLOCK}

Output schema (return JSON that matches this exactly, no extra keys):
{IMPROVEMENT_OUTPUT_SCHEMA}

What the model must not output (in any form):
- No analysis, commentary, meta-text, or reflections.
- No explanations of what you changed or why.
- No scores, grades, or points.
- No list of changes or bullet summary of edits (the improved text alone is the deliverable).

Quality and content rules:
- Preserve the original meaning and communicative intention.
- Do not invent specific facts; do not invent order numbers, dates, names, prices, product details, addresses, or events.
- Keep TELC B2 level—not C1/C2.
- Keep the text type and format required by the task.
- Improve grammar, spelling, punctuation, structure, register, and coherence.
- If the original text is below 150 words, expand only with safe, generic, realistic details.
- Do not change evaluation outcomes, grades, points, or scoring in the output (do not mention them).

{GERMAN_OUTPUT_PROMPT_BLOCK}
"""


def _format_list(title: str, items: list[str]) -> str:
    """Format a short bullet list section for prompt context."""
    if not items:
        return f"{title}:\n- (keine)"
    return f"{title}:\n" + "\n".join(f"- {item}" for item in items[:5])


def _format_communication_context(
    communication_result: CommunicationCheckResult,
) -> str:
    """Format communication evidence from the current simplified schema."""
    indicator_lines = [
        f"- {item.label}: {item.rating} — {item.comment}"
        for item in communication_result.communication_indicators[:7]
    ]

    indicators_block = (
        "\n".join(indicator_lines)
        if indicator_lines
        else "- (keine detaillierten Kommunikationsindikatoren)"
    )

    return "\n".join(
        [
            "Kommunikationsanalyse aus der Auswertung:",
            f"- E-Mail-Struktur: {communication_result.email_structure_quality}",
            f"- Zusammenhang: {communication_result.coherence_quality}",
            f"- Verknüpfungen: {communication_result.cohesion_quality}",
            f"- Register: {communication_result.register_quality}",
            f"- Wortschatzniveau: {communication_result.vocabulary_level}",
            f"- Satzvielfalt: {communication_result.sentence_variety_quality}",
            f"- Kommentar: {communication_result.explanation}",
            "Kommunikationsindikatoren:",
            indicators_block,
        ]
    )


def build_improvement_user_prompt(
    input_data: WritingEvaluationInput,
    key_points_result: KeyPointCheckResult | None = None,
    communication_result: CommunicationCheckResult | None = None,
    accuracy_result: AccuracyCheckResult | None = None,
) -> str:
    """Build the improvement prompt from validated input data."""
    expected_key_points_block = "\n".join(
        f"- {item}" for item in input_data.expected_key_points
    )

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
        evidence_sections.append(
            _format_communication_context(communication_result)
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
                "Gezielte Fehlerstellen aus dem Original "
                "(genau diese Stellen korrigieren):\n"
                + "\n".join(span_lines)
            )

    evidence_block = (
        "\n\n".join(evidence_sections)
        if evidence_sections
        else "Keine zusätzlichen Auswertungsdaten vorhanden."
    )

    return f"""Erzeuge nur den vollständigen verbesserten deutschen Text als Wert von "improved_text" (Schema siehe Systemanweisung)—keine Analyse, keine Erklärungen, keine Punktzahlen, keine Änderungsliste.

Verwende Aufgabe und Hinweise nur innerlich; die Ausgabe darf ausschließlich den verbesserten Lauftext enthalten.

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

Zusätzliche Auswertungshinweise:
{evidence_block}

Anforderungen an den verbesserten Text:
- Bedeutung und Absicht des Originals erhalten.
- Keine konkreten Fakten erfinden.
- Register und Format passend zur Aufgabe beibehalten.
- Grammatik, Rechtschreibung, Zeichensetzung, Textstruktur, Register und Kohärenz verbessern.
- TELC-B2-Niveau halten, nicht auf C1/C2 anheben.
- Wenn unter 150 Wörter: nur mit sicheren, allgemeinen Details erweitern.
- Genannte Fehler und Empfehlungen im verbesserten Text berücksichtigen; bei konkreten Fehlerstellen diese dort korrigieren.

Return JSON only.
"""