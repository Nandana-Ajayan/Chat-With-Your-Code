from fastapi import FastAPI
from pydantic import BaseModel
from backend.chunker import load_c_code_files, chunk_code
from backend.embedder import embed_text
from backend.retriever import add_to_chroma, query_chroma
from backend.llm import generate_answer_ollama

# New imports for serving static files, handling CORS, and time logging
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import time

app = FastAPI()

# --- Configuration ---
# The default distance function in Chroma is L2 (Euclidean) distance.
# For normalized embeddings, L2 distance ranges from 0 (identical) to 2 (most dissimilar).
# A threshold of 1.0 is a good starting point, capturing reasonably similar documents.
SIMILARITY_THRESHOLD = 1.2

# --- Enable CORS to allow frontend to communicate with backend
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str   # Accepts a string question from the frontend

@app.on_event("startup")
def index_code():
    print("🔄 Indexing C/C++ codebase...")
    start_time = time.time()

    # Load all C/C++ files from 'data/lprint' directory
    code_data = load_c_code_files("data/lprint")

    # Chunk the code into function-level snippets
    chunks = chunk_code(code_data)
    
    if not chunks:
        print("⚠️ No functions found to index. Ensure 'data/lprint' contains C/C++ files with function definitions.")
        return
    
    # Generate embeddings for each code chunk
    contents = [c["content"] for c in chunks]
    embeddings = embed_text(contents)

    # Store chunks and embeddings into Chroma vector DB
    add_to_chroma(chunks, embeddings)
    end_time = time.time()
    print(f"✅ Codebase indexed with {len(chunks)} chunks in {end_time - start_time:.2f} seconds.")

@app.post("/ask")
def ask_code(query: QueryRequest):
    total_start_time = time.time()
    print("\n--- New Query Received ---")
    question = query.question

    #  Convert the user's question into an embedding
    embedding_start_time = time.time()
    question_embedding = embed_text([question])[0]
    embedding_end_time = time.time()
    print(f"⏱️ Question embedding took: {embedding_end_time - embedding_start_time:.2f}s")

    # Retrieve relevant chunks with similarity threshold
    retrieval_start_time = time.time()
    results = query_chroma(question_embedding, top_k=10, similarity_threshold=SIMILARITY_THRESHOLD)
    retrieval_end_time = time.time()
    print(f"⏱️ ChromaDB query took: {retrieval_end_time - retrieval_start_time:.2f}s")

    #Extract the retrieved documents/snippets
    retrieved_docs = results["documents"][0]
    if not retrieved_docs:
        print(f"🤷 No relevant code snippets found below similarity threshold of {SIMILARITY_THRESHOLD}.")
        return {
            "answer": "I could not find any relevant code snippets to answer your question. Please try rephrasing your question or consider adjusting the similarity threshold in the code.",
            "snippets": [],
            "files": []
        }
    
    print(f"✅ Found {len(retrieved_docs)} relevant snippets below the threshold.")

    #Generate an answer using the LLM
    context = "\n\n".join(retrieved_docs)
    llm_start_time = time.time()
    answer = generate_answer_ollama(context, question)
    llm_end_time = time.time()
    print(f"⏱️ LLM generation took: {llm_end_time - llm_start_time:.2f}s")

    total_end_time = time.time()
    print(f"⏱️ Total request time: {total_end_time - total_start_time:.2f}s")

    #Return the final answer, the snippets used, and file info to frontend
    return {
        "answer": answer,
        "snippets": retrieved_docs,
        "files": results["metadatas"][0]
    }

# --- Static Files and Root Endpoint ---
static_files_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chat_web_app"))
app.mount("/static", StaticFiles(directory=static_files_path), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(static_files_path, "index.html"))