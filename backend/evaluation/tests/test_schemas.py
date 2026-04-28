"""Unit tests for evaluation schemas."""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from backend.evaluation.schemas import (
    CriterionScore,
    WritingEvaluationInput,
    WritingEvaluationResult,
)


class CriterionScoreTests(unittest.TestCase):
    """Tests for grade-to-points validation."""

    def test_accepts_valid_grade_points_mapping(self) -> None:
        """Valid grade/points pairs should pass validation."""
        score = CriterionScore(grade="A", points=5)
        self.assertEqual(score.grade, "A")
        self.assertEqual(score.points, 5)

    def test_rejects_invalid_grade_points_mapping(self) -> None:
        """Invalid grade/points pairs should fail validation."""
        with self.assertRaises(ValidationError):
            CriterionScore(grade="B", points=5)


class WritingEvaluationInputTests(unittest.TestCase):
    """Tests for strict input validation."""

    def test_rejects_duplicate_key_points(self) -> None:
        """Duplicate expected key points should be rejected."""
        with self.assertRaises(ValidationError):
            WritingEvaluationInput(
                task_text="Task",
                expected_key_points=["Punkt 1", "Punkt 1"],
                candidate_text="Antwort",
            )

    def test_rejects_extra_field(self) -> None:
        """Unexpected fields should be forbidden."""
        with self.assertRaises(ValidationError):
            WritingEvaluationInput(
                task_text="Task",
                expected_key_points=["Punkt 1"],
                candidate_text="Antwort",
                extra_field="forbidden",
            )


class WritingEvaluationResultTests(unittest.TestCase):
    """Tests for final result schema validation."""

    def test_accepts_valid_result(self) -> None:
        """A well-formed final result should validate."""
        result = WritingEvaluationResult(
            topic_mismatch=False,
            situation_mismatch=False,
            criterion_I=CriterionScore(grade="A", points=5),
            criterion_II=CriterionScore(grade="B", points=3),
            criterion_III=CriterionScore(grade="C", points=1),
            raw_score=9,
            final_score=27,
            max_score=45,
            explanations={
                "relevance": "Matches task.",
                "criterion_I": "Key points mostly covered.",
                "criterion_II": "Structure is solid.",
                "criterion_III": "Some errors present.",
            },
        )
        self.assertEqual(result.max_score, 45)

    def test_rejects_empty_explanations(self) -> None:
        """Explanations dictionary must not be empty."""
        with self.assertRaises(ValidationError):
            WritingEvaluationResult(
                topic_mismatch=False,
                situation_mismatch=False,
                criterion_I=CriterionScore(grade="A", points=5),
                criterion_II=CriterionScore(grade="A", points=5),
                criterion_III=CriterionScore(grade="A", points=5),
                raw_score=15,
                final_score=45,
                max_score=45,
                explanations={},
            )


if __name__ == "__main__":
    unittest.main()
