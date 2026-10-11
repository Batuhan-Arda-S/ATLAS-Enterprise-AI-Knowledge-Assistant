from dataclasses import dataclass
from math import isfinite
from typing import Literal, Sequence


RetrievalStatus = Literal["no_candidates","not_evaluated","below_threshold","passes_threshold"]


@dataclass(frozen=True)
class RetrievalAssessment:
    status: RetrievalStatus
    best_similarity: float | None
    candidate_count: int


def assess_retrieval(distances: Sequence[float],min_similarity: float | None = None)->RetrievalAssessment:

    if min_similarity is not None:
        if not isfinite(min_similarity) or not -1 <= min_similarity <= 1:
            raise ValueError("Similarity threshold must be between -1 and 1")

    if any(not isfinite(distance) for distance in distances):
        raise ValueError("Distances must be finite")

    if not distances:
        return RetrievalAssessment(status="no_candidates",best_similarity=None,candidate_count=0)

    best_similarity = max(1.0 - distance for distance in distances)

    if min_similarity is None:
        status = "not_evaluated"

    elif best_similarity < min_similarity:
        status = "below_threshold"

    else:
        status = "passes_threshold"

    return RetrievalAssessment(status=status,best_similarity=best_similarity,candidate_count=len(distances))