from sentence_transformers import SentenceTransformer

MODEL_NAME="intfloat/multilingual-e5-small"

def main():
    model=SentenceTransformer(MODEL_NAME)

    texts=[
        "passage: Çalışanlar haftada iki gün uzaktan çalışabilir.",
        "passage: Çalışanların yıllık izin hakkı yirmi gündür.",
        "query: Evden haftada kaç gün çalışabilirim?"
        ]

    embeddings=model.encode(texts,convert_to_numpy=True)

    print("Model device:", model.device)
    print("Output shape:", embeddings.shape)
    print("Data type:", embeddings.dtype)

    for index,embedding in enumerate(embeddings):
        print(f"\nText {index + 1}:")
        print(texts[index])
        print("First 8 values:", embedding[:8].round(4))

        assert embeddings.shape==(3,384)

if __name__ == "__main__":
    main()