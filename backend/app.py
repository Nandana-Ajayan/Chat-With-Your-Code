# backend/app.py
from fastapi import FastAPI
from pydantic import BaseModel
from backend.chunker import load_c_code_files, chunk_code
from backend.embedder import embed_text
from backend.retriever import add_to_chroma, query_chroma
from backend.llm import generate_answer_ollama

# New imports for serving static files and handling CORS
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

app = FastAPI()

# --- CORS Middleware ---
# This allows your frontend to communicate with your backend.
# The "*" allows all origins, which is fine for local development.
# For production, you would want to restrict this to your frontend's domain.
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

@app.on_event("startup")
def index_code():
    print("🔄 Indexing C/C++ codebase...")
    # Assuming 'data/lprint' is relative to the project root
    code_data = load_c_code_files("data/lprint")
    chunks = chunk_code(code_data)
    contents = [c["content"] for c in chunks]
    embeddings = embed_text(contents)
    add_to_chroma(chunks, embeddings)
    print("✅ Codebase indexed.")

@app.post("/ask")
def ask_code(query: QueryRequest):
    question = query.question
    question_embedding = embed_text([question])[0]
    # Changed top_k to 10 to retrieve more context for the LLM
    results = query_chroma(question_embedding, top_k=10)
    context = "\n\n".join(results["documents"][0])
    answer = generate_answer_ollama(context, question)
    return {
        "answer": answer,
        "snippets": results["documents"][0],
        "files": results["metadatas"][0]
    }

# --- Static Files and Root Endpoint ---
# This section serves your frontend application

# Mount the 'chat_web_app' directory as static files
# The path "../chat_web_app" assumes your 'backend' and 'chat_web_app' folders are siblings.
# Adjust the path if your directory structure is different.
static_files_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chat_web_app"))
app.mount("/static", StaticFiles(directory=static_files_path), name="static")


@app.get("/")
async def read_index():
    # Serve the index.html file from the chat_web_app directory
    return FileResponse(os.path.join(static_files_path, "index.html"))