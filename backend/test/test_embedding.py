
import numpy as np
import pytest

from app.services.embedding import EmbeddingService


class FakeEmbeddingModel:

    def __init__(self):
        self.received_inputs = []

    def encode(self, inputs, convert_to_numpy=True):
        self.received_inputs.append(inputs)

        if isinstance(inputs, str):
            return np.zeros(384, dtype=np.float32)

        return np.zeros((len(inputs), 384),dtype=np.float32)


def test_embed_passages_uses_correct_prefix():
    fake_model = FakeEmbeddingModel()
    service = EmbeddingService(model=fake_model)

    vectors = service.embed_passages([
        "Uzaktan çalışma",
        "Yıllık izin"
    ])

    assert fake_model.received_inputs == [
        [
            "passage: Uzaktan çalışma",
            "passage: Yıllık izin"
        ]]

    assert vectors.shape == (2, 384)


def test_embed_query_uses_correct_prefix():
    fake_model = FakeEmbeddingModel()
    service = EmbeddingService(model=fake_model)

    vector = service.embed_query("Evden çalışabilir miyim?")

    assert fake_model.received_inputs == ["query: Evden çalışabilir miyim?"]

    assert vector.shape == (384,)


def test_empty_embedding_inputs_are_rejected():
    fake_model = FakeEmbeddingModel()
    service = EmbeddingService(model=fake_model)

    with pytest.raises(ValueError):
        service.embed_passages([])

    with pytest.raises(ValueError):
        service.embed_passages(["   "])

    with pytest.raises(ValueError):
        service.embed_query("   ")

    assert fake_model.received_inputs == []
