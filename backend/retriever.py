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

# --- CHANGE ---
# This function now only queries and returns the raw, unfiltered results.
def query_collection(collection, query_embedding, top_k=10):
    """
    Queries a specified collection for the top_k most similar chunks.
    """
    # Ensure the query embedding is not empty before querying
    if not query_embedding:
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    return results