# backend/retriever.py
import chromadb

client = chromadb.PersistentClient(path="./chroma")  # 🔥 this is all you need

collection = client.get_or_create_collection("code_chunks")

def add_to_chroma(chunks, embeddings):
    for i, chunk in enumerate(chunks):
        collection.add(
            documents=[chunk["content"]],
            metadatas=[{"file": chunk["file"]}],
            ids=[f"chunk_{i}"],
            embeddings=[embeddings[i]]
        )

def query_chroma(query_embedding, top_k=10):
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    return results
