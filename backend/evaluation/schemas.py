"""Pydantic schemas for TELC B2 writing evaluation.

Dependencies:
pip install pydantic

"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class WritingEvaluationInput(BaseModel):
    """Input payload for evaluating a TELC B2 writing response."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "task_text": (
                    "Sie haben im Hotel ein Problem erlebt. Schreiben Sie eine E-Mail "
                    "an die Hotelleitung und beschreiben Sie die Situation."
                ),
                "expected_key_points": [
                    "Problem beschreiben",
                    "Folgen schildern",
                    "Lösung verlangen",
                ],
                "candidate_text": (
                    "Betreff: Beschwerde zu meinem Aufenthalt\n\n"
                    "Sehr geehrte Damen und Herren,\n..."
                ),
            }
        },
    )

    task_text: str = Field(..., min_length=1)
    expected_key_points: list[str] = Field(..., min_length=1)
    candidate_text: str = Field(..., min_length=1)

    @field_validator("expected_key_points")
    @classmethod
    def validate_expected_key_points(cls, value: list[str]) -> list[str]:
        """Ensure key points are non-empty, unique strings."""
        cleaned = [item.strip() for item in value]
        if any(not item for item in cleaned):
            raise ValueError("expected_key_points must not contain empty strings")
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("expected_key_points must not contain duplicates")
        return cleaned


class RelevanceCheckResult(BaseModel):
    """Structured LLM output for topic and situation relevance checks."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "topic_mismatch": False,
                "situation_mismatch": False,
                "explanation": "The response matches the requested complaint email scenario.",
                "positive_feedback": ["The response addresses the product delivery complaint scenario."],
                "improvement_feedback": ["State the recipient role even more explicitly in the opening line."],
            }
        },
    )

    topic_mismatch: bool = Field(...)
    situation_mismatch: bool = Field(...)
    explanation: str = Field(..., min_length=1)
    positive_feedback: list[str] = Field(...)
    improvement_feedback: list[str] = Field(...)

    @field_validator("positive_feedback", "improvement_feedback")
    @classmethod
    def validate_feedback_lists(cls, value: list[str]) -> list[str]:
        """Ensure feedback entries are non-empty strings."""
        cleaned = [item.strip() for item in value]
        if any(not item for item in cleaned):
            raise ValueError("feedback fields must not contain empty strings")
        return cleaned


class KeyPointDetail(BaseModel):
    """Structured per-key-point TELC task-achievement analysis."""

    model_config = ConfigDict(extra="forbid")

    number: int | None = None
    type: Literal["expected", "own_idea"] = "expected"
    key_point: str
    status: Literal["fulfilled", "partially_fulfilled", "not_fulfilled"]
    sentence_count: int = 0
    situation_appropriate: bool | None = None
    language_level: Literal["B2", "B1+", "B1", "A2"] | None = None
    comment: str


class TaskAchievementSummary(BaseModel):
    """Frontend-facing Criterion I summary metrics."""

    model_config = ConfigDict(extra="forbid")

    fulfilled_count: int = 0
    partially_fulfilled_count: int = 0
    not_fulfilled_count: int = 0
    own_idea_count: int = 0
    overall_level: Literal["B2", "B1+", "B1", "A2"] | None = None
    summary_comment: str


class KeyPointCheckResult(BaseModel):
    """Structured LLM output for key-point extraction and validation."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "fulfilled_key_points": ["Problem beschreiben", "Lösung verlangen"],
                "own_ideas": ["Gutschein als Kompensation vorschlagen"],
                "invalid_points": ["Über Wetter sprechen"],
                "explanation": "Two required key points are present and one additional idea is valid.",
                "positive_feedback": ["The damage problem is clearly developed with concrete detail."],
                "improvement_feedback": ["Explain expectations with more specific conditions or deadlines."],
            }
        },
    )

    fulfilled_key_points: list[str] = Field(default_factory=list)
    own_ideas: list[str] = Field(default_factory=list)
    invalid_points: list[str] = Field(default_factory=list)
    explanation: str = Field(..., min_length=1)
    positive_feedback: list[str] = Field(default_factory=list)
    improvement_feedback: list[str] = Field(default_factory=list)
    key_point_details: list[KeyPointDetail] = Field(default_factory=list)

    @field_validator(
        "fulfilled_key_points",
        "own_ideas",
        "invalid_points",
        "positive_feedback",
        "improvement_feedback",
    )
    @classmethod
    def validate_string_lists(cls, value: list[str]) -> list[str]:
        """Ensure all list entries are non-empty strings."""
        cleaned = [item.strip() for item in value]
        if any(not item for item in cleaned):
            raise ValueError("list fields must not contain empty strings")
        return cleaned


class CommunicationIndicator(BaseModel):
    """Simplified per-aspect communicative indicator for Criterion II."""

    model_config = ConfigDict(extra="forbid")

    aspect: Literal[
        "email_elements",
        "structure",
        "coherence",
        "cohesion",
        "register",
        "vocabulary",
        "sentence_variety",
    ]
    label: str
    rating: Literal["excellent", "good", "acceptable", "weak", "missing"]
    comment: str


class CommunicationCheckResult(BaseModel):
    """Structured LLM output for communicative quality and email structure."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "has_subject": True,
                "has_greeting": True,
                "has_introduction": True,
                "has_body_structure": True,
                "has_conclusion": True,
                "has_closing": True,
                "register_quality": "appropriate",
                "coherence_quality": "good",
                "vocabulary_level": "B2",
                "sentence_variety": "some_variety",
                "explanation": "The email has the expected structure and appropriate register.",
                "communication_indicators": [
                    {
                        "aspect": "email_elements",
                        "label": "E-Mail-Elemente",
                        "rating": "good",
                        "comment": "Die wichtigsten E-Mail-Bausteine sind vorhanden.",
                    }
                ],
            }
        },
    )

    has_subject: bool = Field(...)
    has_greeting: bool = Field(...)
    has_introduction: bool = Field(...)
    has_body_structure: bool = Field(...)
    has_conclusion: bool = Field(...)
    has_closing: bool = Field(...)
    register_quality: Literal["appropriate", "mostly_appropriate", "inappropriate"] = Field(...)
    coherence_quality: Literal["strong", "good", "acceptable", "weak", "incoherent"] = Field(...)
    vocabulary_level: Literal["B2", "B1+", "B1", "A2"] = Field(...)
    sentence_variety: Literal["varied", "some_variety", "simple"] = Field(...)
    explanation: str = Field(..., min_length=1)
    communication_indicators: list[CommunicationIndicator] = Field(default_factory=list)


class GrammarErrorSpan(BaseModel):
    """A grammar, spelling, or punctuation error found in the original text."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., min_length=1)
    correction: str = Field(..., min_length=1)
    error_type: str = Field(..., min_length=1)
    aspect: Literal[
        "grammar",
        "syntax",
        "word_order",
        "spelling",
        "punctuation",
        "comprehension",
    ] | None = None
    explanation: str = Field(..., min_length=1)


class AccuracyDetail(BaseModel):
    """Structured grouped formal-accuracy analysis for Criterion III."""

    model_config = ConfigDict(extra="forbid")

    aspect: Literal[
        "grammar",
        "syntax",
        "word_order",
        "spelling",
        "punctuation",
        "comprehension",
    ]
    label: str
    status: Literal["strong", "adequate", "weak", "problematic"]
    error_count: int = 0
    evidence: list[str] = Field(default_factory=list)
    comment: str


class AccuracyCheckResult(BaseModel):
    """Structured LLM output for language accuracy and error impact."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "grammar_control": "good",
                "systematic_errors": ["Verb placement in subordinate clauses"],
                "spelling_quality": "acceptable",
                "punctuation_quality": "acceptable",
                "comprehension_affected": False,
                "explanation": "There are recurring grammar issues, but meaning remains clear.",
                "positive_feedback": ["Sentence boundaries are generally clear."],
                "improvement_feedback": ["Case marking is inconsistent in subordinate clauses."],
                "example_errors": ["Incorrect verb position after connector 'weil' in one sentence."],
                "technical_notes": ["Verb placement is mostly stable but occasionally inconsistent."],
                "highlighted_errors": [
                    {
                        "text": "ein Kopfhörer",
                        "correction": "einen Kopfhörer",
                        "error_type": "Kasusfehler",
                        "explanation": "Nach dem Verb steht hier der Akkusativ.",
                    }
                ],
            }
        },
    )

    grammar_control: Literal["strong", "good", "unstable", "basic"] = Field(...)
    systematic_errors: list[str] = Field(default_factory=list)
    spelling_quality: Literal["good", "acceptable", "poor"] = Field(...)
    punctuation_quality: Literal["good", "acceptable", "poor"] = Field(...)
    comprehension_affected: bool = Field(...)
    explanation: str = Field(..., min_length=1)
    positive_feedback: list[str] = Field(default_factory=list)
    improvement_feedback: list[str] = Field(default_factory=list)
    example_errors: list[str] = Field(default_factory=list)
    technical_notes: list[str] = Field(default_factory=list)
    accuracy_details: list[AccuracyDetail] = Field(default_factory=list)
    highlighted_errors: list[GrammarErrorSpan] = Field(default_factory=list)

    @field_validator(
        "systematic_errors",
        "positive_feedback",
        "improvement_feedback",
        "example_errors",
        "technical_notes",
    )
    @classmethod
    def validate_systematic_errors(cls, value: list[str]) -> list[str]:
        """Ensure systematic error labels are non-empty strings."""
        cleaned = [item.strip() for item in value]
        if any(not item for item in cleaned):
            raise ValueError("systematic_errors must not contain empty strings")
        return cleaned


class CriterionScore(BaseModel):
    """Validated score for one TELC writing criterion."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "grade": "B",
                "points": 3,
            }
        },
    )

    grade: Literal["A", "B", "C", "D"] = Field(...)
    points: int = Field(..., ge=0, le=5)
    comment: str | None = Field(default=None)
    scaled_points: int | None = Field(default=None)
    max_scaled_points: int | None = Field(default=None)
    task_achievement_summary: TaskAchievementSummary | None = Field(default=None)
    key_point_details: list[KeyPointDetail] | None = Field(default=None)
    analysis_status: Literal["success", "failed"] | None = Field(default=None)
    analysis_error: str | None = Field(default=None)
    communication_indicators: list[CommunicationIndicator] | None = Field(default=None)
    accuracy_details: list[AccuracyDetail] | None = Field(default=None)
    highlighted_errors: list[GrammarErrorSpan] | None = Field(default=None)

    @model_validator(mode="after")
    def validate_grade_points_mapping(self) -> CriterionScore:
        """Ensure points exactly match the grade mapping."""
        expected_points = {"A": 5, "B": 3, "C": 1, "D": 0}[self.grade]
        if self.points != expected_points:
            raise ValueError(
                f"points must equal {expected_points} when grade is {self.grade}"
            )
        return self


class FinalScore(BaseModel):
    """Aggregated raw and final score values."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "raw_score": 11,
                "final_score": 33,
                "max_score": 45,
            }
        },
    )

    raw_score: int = Field(..., ge=0)
    final_score: int = Field(..., ge=0)
    max_score: int = Field(default=45, ge=1)


class WordCountCheck(BaseModel):
    """Deterministic word count precheck metadata."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "value": 132,
                "minimum_required": 150,
                "meets_requirement": False,
            }
        },
    )

    value: int = Field(..., ge=0)
    minimum_required: int = Field(default=150, ge=1)
    meets_requirement: bool = Field(...)


class ImprovedTextResult(BaseModel):
    """Improved version of the candidate text and short summary of changes."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "improved_text": "Betreff: Beschädigte Lieferung ...",
                "changes_summary": [
                    "Grammatik und Satzbau verbessert",
                    "Formellen Stil verstärkt",
                ],
            }
        },
    )

    improved_text: str = Field(..., min_length=1)
    changes_summary: list[str] = Field(default_factory=list)

    @field_validator("changes_summary")
    @classmethod
    def validate_changes_summary(cls, value: list[str]) -> list[str]:
        """Ensure summary entries are non-empty strings."""
        cleaned = [item.strip() for item in value]
        if any(not item for item in cleaned):
            raise ValueError("changes_summary must not contain empty strings")
        return cleaned


class WritingEvaluationResult(BaseModel):
    """Final JSON-serializable result returned by the writing evaluation pipeline."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "topic_mismatch": False,
                "situation_mismatch": False,
                "criterion_I": {"grade": "B", "points": 3},
                "criterion_II": {"grade": "A", "points": 5},
                "criterion_III": {"grade": "C", "points": 1},
                "word_count": {
                    "value": 132,
                    "minimum_required": 150,
                    "meets_requirement": False,
                },
                "improved_text": {
                    "improved_text": "Betreff: Beschädigte Lieferung ...",
                    "changes_summary": [
                        "Grammatik und Satzbau verbessert",
                        "Formellen Stil verstärkt",
                    ],
                },
                "raw_score": 9,
                "final_score": 27,
                "max_score": 45,
            }
        },
    )

    topic_mismatch: bool = Field(...)
    situation_mismatch: bool = Field(...)
    criterion_I: CriterionScore = Field(...)
    criterion_II: CriterionScore = Field(...)
    criterion_III: CriterionScore = Field(...)
    word_count: WordCountCheck | None = Field(default=None)
    improved_text: ImprovedTextResult = Field(...)
    raw_score: int = Field(..., ge=0)
    final_score: int = Field(..., ge=0)
    max_score: int = Field(..., ge=1)
