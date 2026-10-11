
import argparse
import json
from pathlib import Path

from app.database.session import get_session
from app.evaluation.metrics import calculate_retrieval_metrics
from app.services.semantic_search import semantic_search_service


DEFAULT_DATASET = (Path(__file__).resolve().parents[1]/ "evaluation_data"/ "retrieval_cases.json")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--dataset",type=Path,default=DEFAULT_DATASET)

    parser.add_argument("--k",type=int,default=3)

    args = parser.parse_args()

    if not 1 <= args.k <= 10:
        parser.error("K must be between 1 and 10")

    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))

    cases = dataset["cases"]

    if not cases:
        print("No evaluation cases found in dataset.")
        return

    total_precision = 0.0
    total_recall = 0.0

    session_generator = get_session()
    session = next(session_generator)

    try:
        for case in cases:
            relevant_ids = set(case["relevant_chunk_ids"])

            results = semantic_search_service.search(session=session,
                                                     document_id=case["document_id"],
                                                     question=case["question"],
                                                     limit=args.k)

            retrieved_ids = [chunk.id for chunk, distance in results]

            metrics = calculate_retrieval_metrics(retrieved_ids=retrieved_ids,relevant_ids=relevant_ids,k=args.k)

            total_precision += metrics.precision_at_k
            total_recall += metrics.recall_at_k

            print(f"\nQuestion: {case['question']}")
            print(f"Expected chunk IDs: {sorted(relevant_ids)}")
            print(f"Retrieved chunk IDs: {retrieved_ids}")

            for rank, (chunk, distance) in enumerate(results,start=1):
                similarity = 1.0 - distance
                is_relevant = chunk.id in relevant_ids

                print(
                    f"Rank {rank}: "
                    f"chunk={chunk.id}, "
                    f"similarity={similarity:.4f}, "
                    f"relevant={is_relevant}"
                )

            print(
                f"Precision@{args.k}: "
                f"{metrics.precision_at_k:.3f}"
            )

            print(
                f"Recall@{args.k}: "
                f"{metrics.recall_at_k:.3f}"
            )

        case_count = len(cases)

        print("\nEvaluation Summary")
        print(f"Evaluated questions: {case_count}")

        print(
            f"Mean Precision@{args.k}: "
            f"{total_precision / case_count:.3f}"
        )

        print(
            f"Mean Recall@{args.k}: "
            f"{total_recall / case_count:.3f}"
        )

    finally:
        session_generator.close()


if __name__ == "__main__":
    main()
