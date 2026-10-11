from dataclasses import dataclass

@dataclass(frozen=True)
class RetrievalMetrics:
    precision_at_k:float
    recall_at_k:float
    relevant_found:int


def calculate_retrieval_metrics(retrieved_ids:list[int],relevant_ids:set[int],k:int)->RetrievalMetrics:

    if k<=0:
        raise ValueError("K must be positive")

    if not relevant_ids:
        raise ValueError("At least one relevant chunk is required")

    if len(retrieved_ids)!=len(set(retrieved_ids)):
        raise ValueError("Retrieved chunk IDs must be unique")

    top_k_ids=set(retrieved_ids[:k])

    relevant_found=len(top_k_ids.intersection(relevant_ids))

    precision=relevant_found/k
    recall=relevant_found/len(relevant_ids)

    return RetrievalMetrics(precision_at_k=precision,recall_at_k=recall,relevant_found=relevant_found)