import os
import ast


def get_file_structure(repo_path: str) -> dict:
    """
    Walk the repo and extract function/class signatures from Python files.
    Returns { filename: [list of function names] }
    Does NOT read full file contents — just the map.
    """
    structure = {}

    for root, dirs, files in os.walk(repo_path):
        # skip hidden folders, venv, pycache
        dirs[:] = [
            d for d in dirs
            if not d.startswith(".")
            and d not in ("venv", "__pycache__", "node_modules")
        ]

        for filename in files:
            if not filename.endswith(".py"):
                continue

            filepath = os.path.join(root, filename)
            relative_path = os.path.relpath(filepath, repo_path)

            try:
                with open(filepath, "r") as f:
                    source = f.read()

                tree = ast.parse(source)
                functions = [
                    node.name for node in ast.walk(tree)
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                ]
                structure[relative_path] = functions

            except Exception:
                structure[relative_path] = []

    return structure


def get_relevant_code(repo_path: str, affected_files: list) -> dict:
    """
    Read the full content of files the issue parser flagged as relevant.
    Returns { filename: full_source_code }
    """
    relevant = {}

    for filename in affected_files:
        filepath = os.path.join(repo_path, filename)

        if not os.path.exists(filepath):
            print(f"Warning: {filename} not found in repo.")
            continue

        with open(filepath, "r") as f:
            relevant[filename] = f.read()

    return relevant


def navigate(repo_path: str, affected_files: list) -> dict:
    """
    Main entry point for the navigator agent.
    Returns both the file structure map and the relevant code.
    """
    print(f"\n[Navigator] Scanning repo: {repo_path}")

    structure = get_file_structure(repo_path)
    print(f"[Navigator] Found files: {list(structure.keys())}")

    relevant_code = get_relevant_code(repo_path, affected_files)
    print(f"[Navigator] Loaded relevant files: {list(relevant_code.keys())}")

    return {
        "structure": structure,
        "relevant_code": relevant_code
    }