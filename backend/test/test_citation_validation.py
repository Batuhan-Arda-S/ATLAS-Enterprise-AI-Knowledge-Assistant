import pytest

from app.services.citation_validation import (InvalidCitationError,validate_citations)


def test_valid_citations_preserve_order():
    answer = "First [[chunk:2]], then [[chunk:1]] and [[chunk:2]]."

    result = validate_citations(answer=answer,allowed_ids={1, 2, 3})

    assert result == (2, 1)


def test_unknown_citation_is_rejected():
    with pytest.raises(InvalidCitationError):
        validate_citations(answer="The policy allows two days. [[chunk:999]]",allowed_ids={1, 2, 3})


def test_missing_citations_return_empty_tuple():
    assert validate_citations(answer="No supporting evidence is available.",
                              allowed_ids={1, 2, 3}) == ()