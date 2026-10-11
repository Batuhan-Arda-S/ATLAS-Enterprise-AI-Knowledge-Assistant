import re


CITATION_PATTERN = re.compile(r"\[\[chunk:(\d+)\]\]")


class InvalidCitationError(ValueError):
    pass

def validate_citations(answer: str,allowed_ids: set[int]) -> tuple[int, ...]:

    cited_ids = tuple(dict.fromkeys(int(value)for value in CITATION_PATTERN.findall(answer)))

    if any(chunk_id not in allowed_ids for chunk_id in cited_ids):
        raise InvalidCitationError("LLM referenced a source outside the retrieved context")

    return cited_ids