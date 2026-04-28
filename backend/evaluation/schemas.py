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
            }
        },
    )

    topic_mismatch: bool = Field(...)
    situation_mismatch: bool = Field(...)
    explanation: str = Field(..., min_length=1)


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
            }
        },
    )

    fulfilled_key_points: list[str] = Field(default_factory=list)
    own_ideas: list[str] = Field(default_factory=list)
    invalid_points: list[str] = Field(default_factory=list)
    explanation: str = Field(..., min_length=1)

    @field_validator("fulfilled_key_points", "own_ideas", "invalid_points")
    @classmethod
    def validate_string_lists(cls, value: list[str]) -> list[str]:
        """Ensure all list entries are non-empty strings."""
        cleaned = [item.strip() for item in value]
        if any(not item for item in cleaned):
            raise ValueError("list fields must not contain empty strings")
        return cleaned


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
            }
        },
    )

    grammar_control: Literal["strong", "good", "unstable", "basic"] = Field(...)
    systematic_errors: list[str] = Field(default_factory=list)
    spelling_quality: Literal["good", "acceptable", "poor"] = Field(...)
    punctuation_quality: Literal["good", "acceptable", "poor"] = Field(...)
    comprehension_affected: bool = Field(...)
    explanation: str = Field(..., min_length=1)

    @field_validator("systematic_errors")
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
                "raw_score": 9,
                "final_score": 27,
                "max_score": 45,
                "explanations": {
                    "relevance": "The text matches the task and the intended situation.",
                    "criterion_I": "Most key points are fulfilled.",
                    "criterion_II": "The email structure is complete and register is appropriate.",
                    "criterion_III": "Errors are present but do not significantly hinder comprehension.",
                },
            }
        },
    )

    topic_mismatch: bool = Field(...)
    situation_mismatch: bool = Field(...)
    criterion_I: CriterionScore = Field(...)
    criterion_II: CriterionScore = Field(...)
    criterion_III: CriterionScore = Field(...)
    raw_score: int = Field(..., ge=0)
    final_score: int = Field(..., ge=0)
    max_score: int = Field(..., ge=1)
    explanations: dict[str, str] = Field(...)

    @field_validator("explanations")
    @classmethod
    def validate_explanations(cls, value: dict[str, str]) -> dict[str, str]:
        """Ensure explanation keys and values are non-empty strings."""
        if not value:
            raise ValueError("explanations must not be empty")
        cleaned: dict[str, str] = {}
        for key, item in value.items():
            normalized_key = key.strip()
            normalized_value = item.strip()
            if not normalized_key or not normalized_value:
                raise ValueError("explanations must not contain empty keys or values")
            cleaned[normalized_key] = normalized_value
        return cleaned
