# backend/app.py
from fastapi import FastAPI
from pydantic import BaseModel
from backend.chunker import load_c_code_files, chunk_code
from backend.embedder import embed_text
from backend.retriever import add_to_chroma, query_chroma
from backend.llm import generate_answer_ollama

app = FastAPI()

class QueryRequest(BaseModel):
    question: str

@app.on_event("startup")
def index_code():
    print("🔄 Indexing C/C++ codebase...")
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
    results = query_chroma(question_embedding, top_k=3)
    context = "\n\n".join(results["documents"][0])
    answer = generate_answer_ollama(context, question)
    return {
        "answer": answer,
        "snippets": results["documents"][0],
        "files": results["metadatas"][0]
    }
