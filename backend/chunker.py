# backend/chunker.py
import os

def load_c_code_files(directory):
    code_data = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith((".c", ".cpp", ".h")):
                path = os.path.join(root, file)
                with open(path, "r", errors="ignore") as f:
                    content = f.read()
                    code_data.append({
                        "file": path,
                        "content": content
                    })
    return code_data

def chunk_code(code_data, max_lines=20):
    chunks = []
    for item in code_data:
        lines = item["content"].splitlines()
        for i in range(0, len(lines), max_lines):
            chunk = "\n".join(lines[i:i + max_lines])
            chunks.append({
                "file": item["file"],
                "content": chunk
            })
    return chunks
