
from app.services.embedding import get_embedding_service


def main():
    service_a = get_embedding_service()
    service_b = get_embedding_service()

    print("Same service instance?", service_a is service_b)

    passages = [
        "Çalışanlar haftada iki gün uzaktan çalışabilir.",
        "Çalışanların yıllık izin hakkı yirmi gündür."
    ]

    query = "Evden haftada kaç gün çalışabilirim?"

    passage_vectors = service_a.embed_passages(passages)
    query_vector = service_a.embed_query(query)

    print("Passage embeddings:", passage_vectors.shape)
    print("Query embedding:", query_vector.shape)

    print("First 5 passage embedding values:")
    print(passage_vectors[0][:5].round(4))

    print("First 5 query embedding values:")
    print(query_vector[:5].round(4))


if __name__ == "__main__":
    main()
