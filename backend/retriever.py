# backend/retriever.py
import chromadb

# Use a transient, in-memory client. This will not save data to disk.
client = chromadb.Client()

def create_temp_collection(name):
    """Creates a new temporary collection."""
    return client.get_or_create_collection(name)

def add_to_collection(collection, chunks, embeddings):
    """Adds chunks and their embeddings to a specified collection."""
    if not chunks:
        return

    ids = [f"chunk_{i}" for i in range(len(chunks))]
    collection.add(
        documents=[chunk["content"] for chunk in chunks],
        metadatas=[{"file": chunk["file"]} for chunk in chunks],
        ids=ids,
        embeddings=embeddings
    )

def query_collection(collection, query_embedding, top_k=10, similarity_threshold=1.0):
    """Queries a specified collection."""
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    if not results or not results["ids"][0]:
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    filtered_documents = []
    filtered_metadatas = []
    filtered_distances = []

    query_distances = results["distances"][0]
    query_documents = results["documents"][0]
    query_metadatas = results["metadatas"][0]

    for i, distance in enumerate(query_distances):
        if distance <= similarity_threshold:
            filtered_documents.append(query_documents[i])
            filtered_metadatas.append(query_metadatas[i])
            filtered_distances.append(distance)
        else:
            break

    return {
        "documents": [filtered_documents],
        "metadatas": [filtered_metadatas],
        "distances": [filtered_distances]
    }