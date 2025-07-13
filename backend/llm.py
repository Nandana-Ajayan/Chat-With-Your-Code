# backend/llm.py
import requests

def generate_answer_ollama(context, question):
    prompt = f"""You are an expert C/C++ developer.
Use the below code snippet(s) to answer the question.

--- CODE SNIPPETS ---
{context}

--- QUESTION ---
{question}

--- ANSWER ---"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]
