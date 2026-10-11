import pytest

from app.evaluation.retrieval_assessment import assess_retrieval


def test_no_candidates():
    result = assess_retrieval([])

    assert result.status == "no_candidates"
    assert result.best_similarity is None
    assert result.candidate_count == 0


def test_candidates_without_threshold():
    result = assess_retrieval([0.12, 0.25])

    assert result.status == "not_evaluated"
    assert result.best_similarity == pytest.approx(0.88)
    assert result.candidate_count == 2


def test_candidates_below_threshold():
    result = assess_retrieval(distances=[0.35, 0.40],min_similarity=0.75)

    assert result.status == "below_threshold"
    assert result.best_similarity == pytest.approx(0.65)


def test_candidates_pass_threshold():
    result = assess_retrieval(distances=[0.12, 0.30],min_similarity=0.80)

    assert result.status == "passes_threshold"
    assert result.best_similarity == pytest.approx(0.88)


def test_invalid_threshold_is_rejected():
    with pytest.raises(ValueError):
        assess_retrieval(distances=[0.12],min_similarity=1.5)