from __future__ import annotations

from backend.evaluation.schemas import (
    AccuracyCheckResult,
    CommunicationCheckResult,
    KeyPointCheckResult,
    RelevanceCheckResult,
)
from backend.evaluation.scoring import (
    apply_word_count_override,
    calculate_final_score,
    make_score,
    score_all_criteria,
    score_criterion_i,
    score_criterion_ii,
    score_criterion_iii,
)


def make_relevance(
    *,
    topic_mismatch: bool = False,
    situation_mismatch: bool = False,
) -> RelevanceCheckResult:
    """Create a relevance result for tests."""
    return RelevanceCheckResult(
        topic_mismatch=topic_mismatch,
        situation_mismatch=situation_mismatch,
        explanation="test",
    )


def make_key_points(
    *,
    fulfilled_key_points: list[str] | None = None,
    own_ideas: list[str] | None = None,
    invalid_points: list[str] | None = None,
) -> KeyPointCheckResult:
    """Create a key-point result for tests."""
    return KeyPointCheckResult(
        fulfilled_key_points=fulfilled_key_points or [],
        own_ideas=own_ideas or [],
        invalid_points=invalid_points or [],
        explanation="test",
    )


def make_communication(
    *,
    email_structure_quality: str = "good",
    coherence_quality: str = "good",
    cohesion_quality: str = "good",
    register_quality: str = "good",
    vocabulary_level: str = "B2",
    sentence_variety_quality: str = "good",
) -> CommunicationCheckResult:
    """Create a communication result for tests."""
    return CommunicationCheckResult(
        email_structure_quality=email_structure_quality,
        cohesion_quality=cohesion_quality,
        register_quality=register_quality,
        coherence_quality=coherence_quality,
        vocabulary_level=vocabulary_level,
        sentence_variety_quality=sentence_variety_quality,
        explanation="test",
    )


def make_accuracy(
    *,
    grammar_control: str = "good",
    systematic_errors: list[str] | None = None,
    spelling_quality: str = "good",
    punctuation_quality: str = "good",
    comprehension_affected: bool = False,
) -> AccuracyCheckResult:
    """Create an accuracy result for tests."""
    return AccuracyCheckResult(
        grammar_control=grammar_control,
        systematic_errors=systematic_errors or [],
        spelling_quality=spelling_quality,
        punctuation_quality=punctuation_quality,
        comprehension_affected=comprehension_affected,
        explanation="test",
        aspect_ratings={
            "grammar": "adequate",
            "syntax": "adequate",
            "word_order": "adequate",
            "verb_forms": "adequate",
            "agreement": "adequate",
            "spelling": "adequate",
            "punctuation": "adequate",
            "capitalization": "adequate",
            "comprehension": "adequate",
        },
    )


def test_make_score_returns_correct_points() -> None:
    assert make_score("A").points == 5
    assert make_score("B").points == 3
    assert make_score("C").points == 1
    assert make_score("D").points == 0


def test_topic_mismatch_forces_all_criteria_to_d() -> None:
    relevance = make_relevance(topic_mismatch=True)
    key_points = make_key_points(
        fulfilled_key_points=["p1", "p2", "p3"],
        own_ideas=["idea"],
    )
    communication = make_communication(
        coherence_quality="excellent",
        register_quality="excellent",
        cohesion_quality="excellent",
        vocabulary_level="B2",
        sentence_variety_quality="excellent",
    )
    accuracy = make_accuracy(grammar_control="strong")

    criterion_i, criterion_ii, criterion_iii, final_score = score_all_criteria(
        relevance=relevance,
        key_points=key_points,
        communication=communication,
        accuracy=accuracy,
    )

    assert criterion_i.grade == "D"
    assert criterion_i.points == 0
    assert criterion_ii.grade == "D"
    assert criterion_ii.points == 0
    assert criterion_iii.grade == "D"
    assert criterion_iii.points == 0
    assert final_score.raw_score == 0
    assert final_score.final_score == 0


def test_situation_mismatch_forces_only_criterion_i_to_d() -> None:
    relevance = make_relevance(situation_mismatch=True)
    key_points = make_key_points(fulfilled_key_points=["p1", "p2", "p3"])
    communication = make_communication(
        coherence_quality="excellent",
        register_quality="excellent",
        cohesion_quality="excellent",
        vocabulary_level="B2",
        sentence_variety_quality="excellent",
    )
    accuracy = make_accuracy(grammar_control="strong")

    criterion_i, criterion_ii, criterion_iii, _ = score_all_criteria(
        relevance=relevance,
        key_points=key_points,
        communication=communication,
        accuracy=accuracy,
    )

    assert criterion_i.grade == "D"
    assert criterion_ii.grade == "A"
    assert criterion_iii.grade == "A"


def test_criterion_i_three_fulfilled_key_points_is_a() -> None:
    score = score_criterion_i(
        make_relevance(),
        make_key_points(fulfilled_key_points=["p1", "p2", "p3"]),
    )
    assert score.grade == "A"


def test_criterion_i_two_key_points_and_one_own_idea_is_a() -> None:
    score = score_criterion_i(
        make_relevance(),
        make_key_points(fulfilled_key_points=["p1", "p2"], own_ideas=["idea"]),
    )
    assert score.grade == "A"


def test_criterion_i_two_key_points_is_b() -> None:
    score = score_criterion_i(
        make_relevance(),
        make_key_points(fulfilled_key_points=["p1", "p2"]),
    )
    assert score.grade == "B"


def test_criterion_i_one_key_point_and_one_own_idea_is_b() -> None:
    score = score_criterion_i(
        make_relevance(),
        make_key_points(fulfilled_key_points=["p1"], own_ideas=["idea"]),
    )
    assert score.grade == "B"


def test_criterion_i_one_key_point_is_c() -> None:
    score = score_criterion_i(
        make_relevance(),
        make_key_points(fulfilled_key_points=["p1"]),
    )
    assert score.grade == "C"


def test_criterion_i_zero_key_points_is_d() -> None:
    score = score_criterion_i(make_relevance(), make_key_points())
    assert score.grade == "D"


def test_criterion_ii_strong_communication_with_all_email_elements_is_a() -> None:
    score = score_criterion_ii(
        make_relevance(),
        make_communication(
            email_structure_quality="excellent",
            register_quality="excellent",
            coherence_quality="excellent",
            cohesion_quality="excellent",
            vocabulary_level="B2",
            sentence_variety_quality="excellent",
        ),
    )
    assert score.grade == "A"


def test_criterion_ii_acceptable_structure_can_still_be_b() -> None:
    score = score_criterion_ii(
        make_relevance(),
        make_communication(
            email_structure_quality="acceptable",
            register_quality="good",
            coherence_quality="good",
            vocabulary_level="B2",
            sentence_variety_quality="good",
        ),
    )
    assert score.grade == "B"


def test_criterion_ii_inappropriate_register_is_d() -> None:
    score = score_criterion_ii(
        make_relevance(),
        make_communication(register_quality="weak"),
    )
    assert score.grade == "D"


def test_criterion_ii_incoherent_text_is_d() -> None:
    score = score_criterion_ii(
        make_relevance(),
        make_communication(coherence_quality="missing"),
    )
    assert score.grade == "D"


def test_criterion_ii_weak_coherence_is_c() -> None:
    score = score_criterion_ii(
        make_relevance(),
        make_communication(coherence_quality="weak"),
    )
    assert score.grade == "C"


def test_criterion_ii_b1_vocabulary_is_c() -> None:
    score = score_criterion_ii(
        make_relevance(),
        make_communication(vocabulary_level="B1"),
    )
    assert score.grade == "C"


def test_criterion_ii_simple_sentence_variety_is_c() -> None:
    score = score_criterion_ii(
        make_relevance(),
        make_communication(sentence_variety_quality="weak"),
    )
    assert score.grade == "C"


def test_criterion_ii_neutral_fallback_profile_is_c_not_d() -> None:
    score = score_criterion_ii(
        make_relevance(),
        make_communication(
            register_quality="acceptable",
            coherence_quality="acceptable",
            vocabulary_level="B1",
            sentence_variety_quality="weak",
        ),
    )
    assert score.grade == "C"


def test_criterion_iii_strong_grammar_with_max_one_systematic_error_is_a() -> None:
    score = score_criterion_iii(
        make_relevance(),
        make_accuracy(
            grammar_control="strong",
            systematic_errors=["minor issue"],
            spelling_quality="good",
            punctuation_quality="good",
        ),
    )
    assert score.grade == "A"


def test_criterion_iii_good_grammar_with_max_three_systematic_errors_is_b() -> None:
    score = score_criterion_iii(
        make_relevance(),
        make_accuracy(
            grammar_control="good",
            systematic_errors=["e1", "e2", "e3"],
            spelling_quality="acceptable",
            punctuation_quality="good",
        ),
    )
    assert score.grade == "B"


def test_criterion_iii_unstable_grammar_is_c() -> None:
    score = score_criterion_iii(
        make_relevance(),
        make_accuracy(grammar_control="unstable"),
    )
    assert score.grade == "C"


def test_criterion_iii_basic_grammar_is_c() -> None:
    score = score_criterion_iii(
        make_relevance(),
        make_accuracy(grammar_control="basic"),
    )
    assert score.grade == "C"


def test_criterion_iii_comprehension_affected_is_d() -> None:
    score = score_criterion_iii(
        make_relevance(),
        make_accuracy(comprehension_affected=True),
    )
    assert score.grade == "D"


def test_calculate_final_score() -> None:
    criterion_i = make_score("B")
    criterion_ii = make_score("B")
    criterion_iii = make_score("C")

    final_score = calculate_final_score(
        criterion_i=criterion_i,
        criterion_ii=criterion_ii,
        criterion_iii=criterion_iii,
    )

    assert final_score.raw_score == 7
    assert final_score.final_score == 21
    assert final_score.max_score == 45


def test_score_all_criteria_returns_expected_tuple() -> None:
    result = score_all_criteria(
        relevance=make_relevance(),
        key_points=make_key_points(fulfilled_key_points=["p1", "p2"]),
        communication=make_communication(
            email_structure_quality="acceptable",
            coherence_quality="good",
            vocabulary_level="B1+",
            sentence_variety_quality="good",
        ),
        accuracy=make_accuracy(grammar_control="good", systematic_errors=["e1"]),
    )

    criterion_i, criterion_ii, criterion_iii, final_score = result

    assert criterion_i.grade == "B"
    assert criterion_ii.grade == "B"
    assert criterion_iii.grade == "B"
    assert final_score.raw_score == 9
    assert final_score.final_score == 27


def test_word_count_override_below_150_sets_all_d() -> None:
    c1, c2, c3 = apply_word_count_override(
        word_count=149,
        minimum_required=150,
        criterion_i=make_score("A"),
        criterion_ii=make_score("B"),
        criterion_iii=make_score("C"),
    )
    assert (c1.grade, c2.grade, c3.grade) == ("D", "D", "D")


def test_word_count_override_at_least_150_unchanged() -> None:
    original = (make_score("A"), make_score("B"), make_score("C"))
    c1, c2, c3 = apply_word_count_override(
        word_count=150,
        minimum_required=150,
        criterion_i=original[0],
        criterion_ii=original[1],
        criterion_iii=original[2],
    )
    assert (c1.grade, c2.grade, c3.grade) == ("A", "B", "C")
