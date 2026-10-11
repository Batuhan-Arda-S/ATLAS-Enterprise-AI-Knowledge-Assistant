
import argparse

from app.evaluation.retrieval_assessment import assess_retrieval
from app.database.session import get_session
from app.services.semantic_search import semantic_search_service


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("document_id", type=int)
    parser.add_argument("question", type=str)
    parser.add_argument("--min-similarity",type=float,default=None)

    args = parser.parse_args()

    session_generator = get_session()
    session = next(session_generator)

    try:
        results = semantic_search_service.search(session=session,
                                                 document_id=args.document_id,
                                                 question=args.question,
                                                 limit=3)

        assessment=assess_retrieval(distances=[distance for _, distance in results],
                                   min_similarity=args.min_similarity)

        print(f"Assessment status: {assessment.status}")
        print(f"Candidate count: {assessment.candidate_count}")

        if assessment.best_similarity is not None:
            print(f"Best cosine similarity: "f"{assessment.best_similarity:.4f}")

        if not results:
            print("No embedded chunks found for this document.")
            return

        for chunk, distance in results:
            similarity = 1.0 - distance

            print(f"Chunk index: {chunk.chunk_index}")
            print(f"Cosine similarity: {similarity:.4f}")
            print(f"Content: {chunk.content}")
            print("-" * 50)

    finally:
        session_generator.close()


if __name__ == "__main__":
    main()
