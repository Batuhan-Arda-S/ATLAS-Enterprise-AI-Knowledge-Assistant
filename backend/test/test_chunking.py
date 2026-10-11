import pytest

from app.services.chunking import chunking_service

def test_text_is_split_into_chunks():
    chunks=chunking_service.split_text("ABCDEFGHIJKLM",chunk_size=5)

    assert chunks==["ABCDE","FGHIJ","KLM"]

def test_short_text_remains_one_chunk():
    chunks=chunking_service.split_text("Hello",chunk_size=20)
    assert chunks==["Hello"]

def test_empty_text_returns_no_chunks():
    chunks=chunking_service.split_text("",chunk_size=5)
    assert chunks==[]

def test_exact_chunk_size_does_not_create_empty_chunk():
    chunks=chunking_service.split_text("ABCDEFGHIJ",chunk_size=5)
    assert chunks==["ABCDE","FGHIJ"]

def test_zero_chunk_size_is_rejected():
    with pytest.raises(ValueError):
        chunking_service.split_text("Hello",chunk_size=0)

def test_chunks_overlap_correctly():
    chunks=chunking_service.split_text("ABCDEFGHIJKLM",chunk_size=5,overlap=2)

    assert chunks==["ABCDE","DEFGH","GHIJK","JKLM"]


def test_short_text_with_overlap():
    chunks=chunking_service.split_text("Hello",chunk_size=20,overlap=5)
    assert chunks==["Hello"]

def test_negative_overlap_is_rejected():
    with pytest.raises(ValueError):
        chunking_service.split_text("Hello",chunk_size=5,overlap=-1)

def test_overlap_equal_to_chunk_size_is_rejected():
    with pytest.raises(ValueError):
        chunking_service.split_text("Hello",chunk_size=5,overlap=5)

def test_overlap_greater_than_chunk_size_is_rejected():
    with pytest.raises(ValueError):
        chunking_service.split_text("Hello",chunk_size=5,overlap=6)

def test_smart_split_prefers_word_boundary():
    chunks=chunking_service.split_text_smart("ABC DEF GHI",chunk_size=8)

    assert chunks==["ABC DEF","GHI"]

def test_smart_split_prefers_paragraph_boundary():
    text="Leave policy.\n\nRemote work policy."

    chunks=chunking_service.split_text_smart(text,chunk_size=20)

    assert chunks==["Leave policy.","Remote work policy."]

def test_smart_split_prefers_sentence_boundary():
    text="Annual leave rules. Remote work rules."

    chunks=chunking_service.split_text_smart(text,chunk_size=24)

    assert chunks==["Annual leave rules.","Remote work rules."]

def test_smart_split_handles_long_sword():
    chunks=chunking_service.split_text_smart("ABCDEFGHIJK",chunk_size=4)

    assert chunks==["ABCD","EFGH","IJK"]

def test_smart_split_handles_whitespace_only():
    chunks=chunking_service.split_text_smart("   \n\n   ",chunk_size=10)

    assert chunks==[]

def test_smart_split_rejects_zero_chunk_size():
    with pytest.raises(ValueError):
        chunking_service.split_text_smart("Hello",chunk_size=0)