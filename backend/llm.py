import requests
import json

def extract_code_and_question(prompt):
    """
    Uses an LLM to separate a block of code from a question in a single prompt.
    It also instructs the LLM to clean up the code to be syntactically valid.
    """
    # This "meta-prompt" is now more detailed.
    extraction_prompt = f"""
You are an expert text analysis tool. A user will provide a text containing a block of C/C++ code and a question about that code.
Your task is to identify and separate the code from the question.
Crucially, you must also clean and format the extracted code so it is syntactically valid C++. Add newlines after headers or function definitions where appropriate. Fix obvious typos like missing newlines.

You must respond with only a valid JSON object containing two keys: "code" and "question".

Example User Text: "hey can u tell me what this function does? #include<stdio.h>void main() {{ printf("hello"); }} "
Your JSON Response:
{{
  "code": "#include <stdio.h>\\n\\nvoid main() {{\\n    printf(\\"hello\\");\\n}}",
  "question": "can you tell me what this function does?"
}}

---
Now, analyze and clean the following user text:
---
{prompt}
---
Your JSON Response:
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": extraction_prompt,
            "stream": False,
            "options": {
                "temperature": 0.0 # Make the output more deterministic for JSON
            }
        }
    )
    
    try:
        response_text = response.json()["response"]
        if response_text.startswith("```json"):
            response_text = response_text.strip("```json\n").strip("```")
            
        data = json.loads(response_text)
        
        if "code" in data and "question" in data:
            print(f"✅ LLM Cleaned Code:\n---\n{data['code']}\n---")
            return data["code"], data["question"]
        else:
            return None, None
            
    except (json.JSONDecodeError, KeyError) as e:
        print(f"LLM did not return valid JSON for extraction: {e}")
        print(f"Raw LLM response: {response.json().get('response')}")
        return prompt, prompt

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