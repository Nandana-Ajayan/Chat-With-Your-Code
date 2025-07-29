# backend/chunker.py
import os
import clang.cindex
from clang.cindex import CursorKind

# On Windows, you might need to specify the path to the libclang.dll file.
# If you installed with `pip install libclang`, it's often handled automatically.
# If not, you may need to find the path to "libclang.dll" in your Python environment's
# site-packages and uncomment the following line:
# clang.cindex.Config.set_library_file('C:/path/to/your/python/Lib/site-packages/clang/libclang.dll')

def load_c_code_files(directory):
    """
    Loads all C/C++ and header files from a directory.
    """
    code_data = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith((".c", ".cpp", ".h")):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        code_data.append({
                            "file": path,
                            "content": content
                        })
                except Exception as e:
                    print(f"Error reading file {path}: {e}")
    return code_data

def chunk_code(code_data):
    """
    Chunks the C/C++ code by function definitions.
    """
    chunks = []
    for item in code_data:
        try:
            index = clang.cindex.Index.create()
            # The file path is provided to libclang, along with the content in-memory.
            # This allows libclang to resolve headers if needed, while still working on the file content.
            tu = index.parse(item['file'], args=['-x', 'c++'], unsaved_files=[(item['file'], item['content'])])

            for cursor in tu.cursor.walk_preorder():
                # We are looking for function definitions.
                if cursor.kind == CursorKind.FUNCTION_DECL and cursor.is_definition():
                    # We only want to extract functions from the file we are currently processing,
                    # not from included headers.
                    if cursor.location.file and cursor.location.file.name == item['file']:
                        # Get the start and end of the function code from the Abstract Syntax Tree.
                        start = cursor.extent.start.offset
                        end = cursor.extent.end.offset
                        function_code = item['content'][start:end]

                        chunks.append({
                            "file": item["file"],
                            "content": function_code
                        })
        except Exception as e:
            print(f"Error parsing file {item['file']} with libclang: {e}")

    return chunks