import ast
import os
import chromadb
from chromadb.utils import embedding_functions


def extract_functions(source_code: str, filename: str) -> list:
    """
    Parse a Python file and extract individual functions as chunks.
    Returns list of { name, code, docstring, filename }
    """
    chunks = []

    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        # unparseable file — treat whole file as one chunk
        return [{
            "name": filename,
            "code": source_code,
            "docstring": "",
            "filename": filename
        }]

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        # extract the source lines for just this function
        start = node.lineno - 1
        end = node.end_lineno
        lines = source_code.split("\n")[start:end]
        func_code = "\n".join(lines)

        # extract docstring if present
        docstring = ast.get_docstring(node) or ""

        chunks.append({
            "name": node.name,
            "code": func_code,
            "docstring": docstring,
            "filename": filename
        })

    return chunks


def build_index(repo_path: str, collection_name: str = "codebase") -> chromadb.Collection:
    """
    Walk the repo, extract all functions, embed them, store in chromadb.
    Returns the collection for querying.
    """
    client = chromadb.Client()

    # delete existing collection if it exists
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    # use chromadb's built-in sentence transformer embeddings
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()

    collection = client.create_collection(
        name=collection_name,
        embedding_function=embedding_fn
    )

    documents = []
    metadatas = []
    ids = []

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [
            d for d in dirs
            if not d.startswith(".")
            and d not in ("venv", "__pycache__", "node_modules")
        ]

        for filename in files:
            if not filename.endswith(".py"):
                continue
            # skip test files and infrastructure files
            if filename.startswith("test_") or filename in ("orchestrator.py", "agent.py"):
                continue

            filepath = os.path.join(root, filename)
            relative = os.path.relpath(filepath, repo_path)

            with open(filepath, "r") as f:
                source = f.read()

            chunks = extract_functions(source, relative)

            for chunk in chunks:
                # the document is what gets embedded
                # combine name + docstring + code for richer embedding
                document = f"Function: {chunk['name']}\n{chunk['docstring']}\n{chunk['code']}"
                doc_id = f"{relative}::{chunk['name']}"

                documents.append(document)
                metadatas.append({
                    "filename": chunk["filename"],
                    "function_name": chunk["name"],
                    "code": chunk["code"]
                })
                ids.append(doc_id)

    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"[Retriever] Indexed {len(documents)} functions from repo")
    else:
        print("[Retriever] Warning: no functions found to index")

    return collection


def retrieve_relevant_code(collection: chromadb.Collection, issue_text: str, top_k: int = 5) -> dict:
    """
    Query the collection with the issue text.
    Returns { filename: code_snippet } for the top_k most relevant functions.
    """
    results = collection.query(
        query_texts=[issue_text],
        n_results=min(top_k, collection.count())
    )

    relevant = {}

    if not results or not results["metadatas"]:
        return relevant

    for metadata in results["metadatas"][0]:
        filename = metadata["filename"]
        code = metadata["code"]

        # group by file — append functions from same file together
        if filename not in relevant:
            relevant[filename] = ""
        relevant[filename] += code + "\n\n"

    print(f"[Retriever] Retrieved {len(results['metadatas'][0])} relevant functions")
    for meta in results["metadatas"][0]:
        print(f"  - {meta['filename']}::{meta['function_name']}")

    return relevant