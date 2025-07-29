import chromadb

client = chromadb.PersistentClient(path="./chroma")  # 🔥 this is all you need

collection = client.get_or_create_collection("code_chunks")

def add_to_chroma(chunks, embeddings):
    """
    Adds chunks and their embeddings to ChromaDB in a single batch for efficiency.
    """
    # Generate IDs for each chunk for batch insertion
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    collection.add(
        documents=[chunk["content"] for chunk in chunks],
        metadatas=[{"file": chunk["file"]} for chunk in chunks],
        ids=ids,
        embeddings=embeddings
    )

def query_chroma(query_embedding, top_k=10, similarity_threshold=1.0):
    """
    Queries ChromaDB and filters the results by a distance threshold.
    """
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    # Return an empty structure if no initial results are found
    if not results or not results["ids"][0]:
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    filtered_documents = []
    filtered_metadatas = []
    filtered_distances = []

    # Results from Chroma are lists of lists; we work with the first list for our single query
    query_distances = results["distances"][0]
    query_documents = results["documents"][0]
    query_metadatas = results["metadatas"][0]

    for i, distance in enumerate(query_distances):
        # L2 distance: lower is more similar. We only keep results below the threshold.
        if distance <= similarity_threshold:
            filtered_documents.append(query_documents[i])
            filtered_metadatas.append(query_metadatas[i])
            filtered_distances.append(distance)
        else:
            # Since results are ordered by distance, we can stop once the threshold is exceeded.
            break

    return {
        "documents": [filtered_documents],
        "metadatas": [filtered_metadatas],
        "distances": [filtered_distances]
    }