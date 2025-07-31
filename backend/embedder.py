# backend/embedder.py
from sentence_transformers import SentenceTransformer

# Load a pre-trained sentence embedding model named "all-MiniLM-L6-v2
model = SentenceTransformer("all-MiniLM-L6-v2") 

def embed_text(texts):
    return model.encode(texts, convert_to_numpy=True).tolist()
