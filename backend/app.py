from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import time
import uuid

from .chunker import chunk_code
from .embedder import embed_text
from .retriever import create_temp_collection, add_to_collection, query_collection
from .llm import generate_answer_ollama, extract_code_and_question

app = FastAPI()

# --- Configuration ---
SIMILARITY_THRESHOLD = 1.2

# --- CORS Middleware ---
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextAskRequest(BaseModel):
    prompt: str

@app.post("/ask")
async def ask_code(question: str = Form(...), file: UploadFile = File(...)):
    total_start_time = time.time()
    print("\n\n" + "="*80)
    print("--- New File Query Received ---")
    print(f"🤖 Processing uploaded file: {file.filename}")

    try:
        file_content = (await file.read()).decode("utf-8")
    except Exception as e:
        return {"answer": f"Error processing file: {e}", "snippets": [], "files": []}

    code_data = [{"file": file.filename, "content": file_content}]
    chunks = chunk_code(code_data)
    if not chunks:
        return {"answer": "I could not find any functions in the uploaded file.", "snippets": [], "files": []}

    collection_name = f"temp_collection_{uuid.uuid4().hex}"
    collection = create_temp_collection(collection_name)
    contents = [c["content"] for c in chunks]
    embeddings = embed_text(contents)
    add_to_collection(collection, chunks, embeddings)
    print(f"✅ File processed with {len(chunks)} chunks.")

    embedding_start_time = time.time()
    question_embedding = embed_text([question])[0]
    embedding_end_time = time.time()
    embedding_took = embedding_end_time - embedding_start_time

    retrieval_start_time = time.time()
    raw_results = query_collection(collection, question_embedding, top_k=10)
    retrieval_end_time = time.time()
    retrieval_took = retrieval_end_time - retrieval_start_time
    
    print(f"\n--- RAG Pipeline Details ---")
    print(f"⏱️ Question embedding took: {embedding_took:.2f}s")
    print(f"⏱️ ChromaDB query took: {retrieval_took:.2f}s")

    print(f"\n🔍 Similarity Threshold set to: {SIMILARITY_THRESHOLD}")
    print(f"🔍 Top {len(raw_results.get('documents', [[]])[0])} chunks retrieved from ChromaDB (before filtering):")
    documents = raw_results.get("documents", [[]])[0]
    distances = raw_results.get("distances", [[]])[0]
    
    if not documents:
        print("  - No chunks found in ChromaDB.")
    else:
        for i, doc in enumerate(documents):
            log_doc = doc.replace('\n', ' ').strip()
            print(f"  - Chunk {i+1:2} (Distance: {distances[i]:.4f}): {log_doc[:90]}...")

    filtered_docs = []
    filtered_metadatas = []
    for i, dist in enumerate(distances):
        if dist <= SIMILARITY_THRESHOLD:
            filtered_docs.append(documents[i])
            filtered_metadatas.append(raw_results["metadatas"][0][i])
    
    print(f"\n✅ Found {len(filtered_docs)} relevant snippets below the threshold.")

    if not filtered_docs:
        return {"answer": "I found code, but none of it seemed relevant to your question based on the similarity threshold. Try rephrasing your question.", "snippets": [], "files": []}

    context = "\n\n".join(filtered_docs)
    llm_start_time = time.time()
    answer = generate_answer_ollama(context, question)
    llm_end_time = time.time()
    llm_took = llm_end_time - llm_start_time
    
    total_end_time = time.time()
    
    print(f"\n--- Performance Summary ---")
    rag_took = embedding_took + retrieval_took
    print(f"⏱️ RAG Time (Embedding + Retrieval): {rag_took:.2f}s")
    print(f"⏱️ LLM Generation Time: {llm_took:.2f}s")
    print(f"⏱️ Total Request Time: {total_end_time - total_start_time:.2f}s")
    print("="*80 + "\n")

    return {"answer": answer, "snippets": filtered_docs, "files": filtered_metadatas}


@app.post("/ask_text")
async def ask_text(request: TextAskRequest):
    total_start_time = time.time()
    print("\n\n" + "="*80)
    print("--- New Text Prompt Received ---")
    
    print("🤖 Using LLM to extract code and question from prompt...")
    code_content, question = extract_code_and_question(request.prompt)

    if not code_content or not question:
        return {"answer": "I had trouble understanding the prompt.", "snippets": [], "files": []}
    
    print(f"✅ Extracted Question: {question}")

    code_data = [{"file": "pasted_code.cpp", "content": code_content}]
    chunks = chunk_code(code_data)
    if not chunks:
        return {"answer": "I couldn't find any valid C/C++ functions in the code you pasted.", "snippets": [], "files": []}

    collection_name = f"temp_collection_{uuid.uuid4().hex}"
    collection = create_temp_collection(collection_name)
    contents = [c["content"] for c in chunks]
    embeddings = embed_text(contents)
    add_to_collection(collection, chunks, embeddings)
    print(f"✅ Processed pasted code with {len(chunks)} chunks.")

    embedding_start_time = time.time()
    question_embedding = embed_text([question])[0]
    embedding_end_time = time.time()
    embedding_took = embedding_end_time - embedding_start_time

    retrieval_start_time = time.time()
    raw_results = query_collection(collection, question_embedding, top_k=10)
    retrieval_end_time = time.time()
    retrieval_took = retrieval_end_time - retrieval_start_time
    
    print(f"\n--- RAG Pipeline Details ---")
    print(f"⏱️ Question embedding took: {embedding_took:.2f}s")
    print(f"⏱️ ChromaDB query took: {retrieval_took:.2f}s")

    print(f"\n🔍 Similarity Threshold set to: {SIMILARITY_THRESHOLD}")
    print(f"🔍 Top {len(raw_results.get('documents', [[]])[0])} chunks retrieved from ChromaDB (before filtering):")
    documents = raw_results.get("documents", [[]])[0]
    distances = raw_results.get("distances", [[]])[0]
    
    if not documents:
        print("  - No chunks found in ChromaDB.")
    else:
        for i, doc in enumerate(documents):
            log_doc = doc.replace('\n', ' ').strip()
            print(f"  - Chunk {i+1:2} (Distance: {distances[i]:.4f}): {log_doc[:90]}...")

    filtered_docs = []
    filtered_metadatas = []
    for i, dist in enumerate(distances):
        if dist <= SIMILARITY_THRESHOLD:
            filtered_docs.append(documents[i])
            filtered_metadatas.append({"file": "pasted_code.cpp"})
    
    print(f"\n✅ Found {len(filtered_docs)} relevant snippets below the threshold.")

    # --- THIS IS THE NEW FALLBACK LOGIC ---
    context_docs_for_llm = []
    if filtered_docs:
        print("✅ Using similarity search results for context.")
        context_docs_for_llm = filtered_docs
    elif chunks:
        print("⚠️ No chunks met similarity threshold. Falling back to using ALL extracted code for context.")
        context_docs_for_llm = [c["content"] for c in chunks]
        # We need to rebuild the metadata to match
        filtered_metadatas = [{"file": "pasted_code.cpp"} for _ in chunks]
    else:
        # This case should not be reached if the check for chunks at the top works, but it's good practice.
        return {"answer": "I couldn't find any code to analyze, so I can't answer the question.", "snippets": [], "files": []}
    # --- END OF NEW LOGIC ---

    context = "\n\n".join(context_docs_for_llm)
    llm_start_time = time.time()
    answer = generate_answer_ollama(context, question)
    llm_end_time = time.time()
    llm_took = llm_end_time - llm_start_time
    
    total_end_time = time.time()
    
    print(f"\n--- Performance Summary ---")
    rag_took = embedding_took + retrieval_took
    print(f"⏱️ RAG Time (Embedding + Retrieval): {rag_took:.2f}s")
    print(f"⏱️ LLM Generation Time: {llm_took:.2f}s")
    print(f"⏱️ Total Request Time: {total_end_time - total_start_time:.2f}s")
    print("="*80 + "\n")

    # We return the docs we actually used for the context
    return {"answer": answer, "snippets": context_docs_for_llm, "files": filtered_metadatas}

# --- Static Files and Root Endpoint ---
static_files_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chat_web_app"))
app.mount("/static", StaticFiles(directory=static_files_path), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(static_files_path, "index.html"))