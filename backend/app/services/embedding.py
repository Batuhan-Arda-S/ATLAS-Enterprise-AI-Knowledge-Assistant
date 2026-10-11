from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "intfloat/multilingual-e5-small"

class EmbeddingService:

    def __init__(self,model:SentenceTransformer|None=None):

        if model is None:
            model=SentenceTransformer(MODEL_NAME)

        self.model = model

    def embed_passages(self,texts:list[str])->np.ndarray:

        if not texts:
            raise ValueError("At least one passage is required")

        if any(not text.strip() for text in texts):
            raise ValueError("Passages cannot be blank")

        inputs=[
            f"passage: {text}"
            for text in texts
        ]

        return self.model.encode(inputs,convert_to_numpy=True)


    def embed_query(self,text:str)->np.ndarray:

        if not text.strip():
            raise ValueError("Query cannot be blank")

        return self.model.encode(f"query: {text}",convert_to_numpy=True)

@lru_cache(maxsize=1)
def get_embedding_service()->EmbeddingService:
    return EmbeddingService()