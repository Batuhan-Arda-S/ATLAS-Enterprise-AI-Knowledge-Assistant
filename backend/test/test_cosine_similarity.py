import numpy as np
import pytest

from scripts.cosine_demo import cosine_similarity

def test_similar_vectors():
    a = np.array([1, 0, 0])
    b = np.array([0.9, 0.1, 0])

    result = cosine_similarity(a, b)

    assert result == pytest.approx(0.9938837)


def test_vector_length_does_not_change_direction():
    a = np.array([1, 0])
    b = np.array([5, 0])

    result = cosine_similarity(a, b)

    assert result == pytest.approx(1.0)


def test_zero_vector_is_rejected():
    a = np.array([0, 0])
    b = np.array([1, 0])

    with pytest.raises(ValueError):
        cosine_similarity(a, b)