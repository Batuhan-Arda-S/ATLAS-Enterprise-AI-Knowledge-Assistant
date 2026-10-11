import numpy as np
from app.services.embedding import get_embedding_service

def cosine_similarity(a:np.ndarray,b:np.ndarray)->float:

    if a.shape!=b.shape:
        raise ValueError("Vector dimensions must match")

    norm_a=np.linalg.norm(a)
    norm_b=np.linalg.norm(b)

    if norm_a==0 or norm_b==0:
        raise ValueError("Cannot compare zero vectors")

    dot_product=np.dot(a,b)

    return float(dot_product/(norm_a*norm_b))


def main():
    service = get_embedding_service()

    passages = [
        "Çalışanlar haftada iki gün uzaktan çalışabilir.",
        "Çalışanların yıllık izin hakkı yirmi gündür.",
        "Şirket araçlarının bakımı yılda bir yapılır."
    ]

    query = "Evden haftada kaç gün çalışabilirim?"

    passage_vectors = service.embed_passages(passages)
    query_vector = service.embed_query(query)

    for text, vector in zip(passages, passage_vectors):
        score = cosine_similarity(query_vector, vector)

        print(f"Similarity: {score:.4f}")
        print(f"Text: {text}")
        print()


if __name__ == "__main__":
    main()