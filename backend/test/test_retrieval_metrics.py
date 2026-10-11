import pytest

from app.evaluation.metrics import calculate_retrieval_metrics


def test_precision_and_recall_at_three():
    metrics = calculate_retrieval_metrics(retrieved_ids=[21, 24, 35],relevant_ids={21, 24, 27, 30},k=3)

    assert metrics.relevant_found == 2
    assert metrics.precision_at_k == pytest.approx(2 / 3)
    assert metrics.recall_at_k == pytest.approx(2 / 4)


def test_all_relevant_chunks_are_found():
    metrics = calculate_retrieval_metrics(retrieved_ids=[12, 15, 19],relevant_ids={15},k=3)

    assert metrics.precision_at_k == pytest.approx(1 / 3)
    assert metrics.recall_at_k == pytest.approx(1.0)


def test_empty_ground_truth_is_rejected():
    with pytest.raises(ValueError):
        calculate_retrieval_metrics(retrieved_ids=[12, 15],relevant_ids=set(),k=3)