import ollama


def generate_fix(issue: dict, relevant_code: dict, test_files: dict = None,
                 previous_attempt: str = None, diagnosis: str = None) -> dict:
    """
    Takes the parsed issue + relevant code, returns fixed code.
    
    If previous_attempt and diagnosis are provided, the coder
    knows what was tried before and why it failed.
    
    Returns { filename: fixed_code } for each affected file.
    Now receives test file contents so it knows
    exactly what assertions it needs to satisfy.
    """
    results = {}

    # build test context string
    test_context = ""
    if test_files:
        test_context = "\n\nHere are the actual test assertions you must satisfy:\n"
        for test_filename, test_source in test_files.items():
            test_context += f"\n{test_filename}:\n```python\n{test_source}\n```"

    for filename, source_code in relevant_code.items():

        if previous_attempt and diagnosis:
            retry_context = f"""
A previous fix attempt failed.

Previous fix:
```python
{previous_attempt}
```

Diagnosis of why it failed:
{diagnosis}

Use this diagnosis to guide a different approach."""
        else:
            retry_context = "This is the first attempt."

        prompt = f"""You are a Python debugging expert.

Issue to fix:
{issue['intent']}

Expected behavior:
{issue['expected_behavior']}

Edge cases to handle:
{', '.join(issue.get('test_hints', []))}
{test_context}

Current code in {filename}:
```python
{source_code}
```

{retry_context}

Return ONLY the complete fixed Python code for {filename}.
No explanation. No markdown fences. Raw Python only."""

        print(f"\n[Coder] Generating fix for {filename}...")

        response = ollama.chat(
            model="qwen2.5-coder:7b",
            messages=[
                {
                    "role": "system",
                    "content": "You are a Python debugging expert. Return ONLY raw Python code. No markdown. No explanation."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        raw = response["message"]["content"].strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1])

        results[filename] = raw

    return results