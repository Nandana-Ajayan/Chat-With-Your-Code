# backend/embedder.py
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")  # Fast, local

def embed_text(texts):
    return model.encode(texts, convert_to_numpy=True).tolist()
