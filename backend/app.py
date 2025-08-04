from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
# --- Relative Imports for your project structure ---
from .chunker import chunk_code                                   # <-- CHANGE
from .embedder import embed_text                                  # <-- CHANGE
from .retriever import create_temp_collection, add_to_collection, query_collection # <-- CHANGE
from .llm import generate_answer_ollama                           # <-- CHANGE

# New imports for serving static files, handling CORS, and time logging
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import time
import uuid

app = FastAPI()

# --- Configuration ---
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

@app.post("/ask")
async def ask_code(question: str = Form(...), file: UploadFile = File(None)):
    total_start_time = time.time()
    print("\n--- New Query Received ---")

    if not file:
        return {
            "answer": "Please upload a C/C++ code file to ask a question about it.",
            "snippets": [],
            "files": []
        }

    # Read the content of the uploaded file
    try:
        file_content = (await file.read()).decode("utf-8")
    except Exception as e:
        print(f"Error reading or decoding uploaded file: {e}")
        return {"answer": f"Error processing file: {e}", "snippets": [], "files": []}

    # Create a temporary, isolated collection for this request
    collection_name = f"temp_collection_{uuid.uuid4().hex}"
    collection = create_temp_collection(collection_name)

    # Prepare data for chunking
    code_data = [{"file": file.filename, "content": file_content}]

    # Chunk the code into function-level snippets
    chunks = chunk_code(code_data)

    if not chunks:
        print(f"⚠️ No functions found to index in the uploaded file: {file.filename}.")
        return {
            "answer": "I could not find any functions in the uploaded file. Please make sure it's a valid C/C++ file with function definitions.",
            "snippets": [],
            "files": []
        }

    # Generate embeddings for each code chunk
    contents = [c["content"] for c in chunks]
    embeddings = embed_text(contents)

    # Store chunks and embeddings into the temporary Chroma collection
    add_to_collection(collection, chunks, embeddings)
    print(f"✅ File processed with {len(chunks)} chunks.")

    # Convert the user's question into an embedding
    embedding_start_time = time.time()
    question_embedding = embed_text([question])[0]
    embedding_end_time = time.time()
    print(f"⏱️ Question embedding took: {embedding_end_time - embedding_start_time:.2f}s")

    # Retrieve relevant chunks with similarity threshold
    retrieval_start_time = time.time()
    results = query_collection(collection, question_embedding, top_k=10, similarity_threshold=SIMILARITY_THRESHOLD)
    retrieval_end_time = time.time()
    print(f"⏱️ ChromaDB query took: {retrieval_end_time - retrieval_start_time:.2f}s")

    # Extract the retrieved documents/snippets
    retrieved_docs = results["documents"][0]
    if not retrieved_docs:
        print(f"🤷 No relevant code snippets found below similarity threshold of {SIMILARITY_THRESHOLD}.")
        return {
            "answer": "I could not find any relevant code snippets in the uploaded file to answer your question. Please try rephrasing your question.",
            "snippets": [],
            "files": []
        }

    print(f"✅ Found {len(retrieved_docs)} relevant snippets below the threshold.")

    # Generate an answer using the LLM
    context = "\n\n".join(retrieved_docs)
    llm_start_time = time.time()
    answer = generate_answer_ollama(context, question)
    llm_end_time = time.time()
    print(f"⏱️ LLM generation took: {llm_end_time - llm_start_time:.2f}s")

    total_end_time = time.time()
    print(f"⏱️ Total request time: {total_end_time - total_start_time:.2f}s")

    # Return the final answer, the snippets used, and file info to the frontend
    return {
        "answer": answer,
        "snippets": retrieved_docs,
        "files": results["metadatas"][0]
    }

# --- Static Files and Root Endpoint ---
# This path goes up one directory from 'backend' to find 'chat_web_app'
static_files_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chat_web_app"))
app.mount("/static", StaticFiles(directory=static_files_path), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(static_files_path, "index.html"))