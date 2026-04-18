import ollama
import json
import re


def parse_issue(issue_text: str, available_files: list = None) -> dict:
    """
    Takes raw issue text, returns structured JSON.

    Output shape:
    {
        "intent": "what the issue is asking to fix",
        "affected_files": ["list of files likely involved"],
        "expected_behavior": "what correct behavior looks like",
        "test_hints": ["edge cases the fix should handle"]
    }
    """

    files_context = ""
    if available_files:
        files_context = f"""
The repository contains these Python files:
{chr(10).join(f'- {f}' for f in available_files)}

You MUST only reference files from this list in affected_files.
"""

    prompt = f"""You are a software engineering assistant that reads bug reports.

Analyze this GitHub issue and extract structured information.

Issue:
{issue_text}
{files_context}
Return ONLY a JSON object with these exact keys:
- intent: one sentence describing what needs to be fixed
- affected_files: list of Python filenames likely involved (only from the list above)
- expected_behavior: what the code should do when fixed
- test_hints: list of edge cases the fix must handle

Return raw JSON only. No explanation. No markdown fences."""

    print(f"\n[Issue Parser] Sending prompt to LLM...")

    response = ollama.chat(
        model="qwen2.5-coder:7b",
        messages=[
            {
                "role": "system",
                "content": "You are a precise software engineering assistant. Return only valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    raw = response["message"]["content"].strip()

    print(f"[Issue Parser] Raw response:\n{raw}\n")

    if raw.startswith("```"):
        raw = re.sub(r"```(?:json)?\n?", "", raw)
        raw = raw.replace("```", "").strip()

    try:
        parsed = json.loads(raw)

        # normalize test_hints — always a list of strings
        if "test_hints" in parsed:
            normalized = []
            for hint in parsed["test_hints"]:
                if isinstance(hint, str):
                    normalized.append(hint)
                elif isinstance(hint, dict):
                    # flatten dict hint into a readable string
                    normalized.append(
                        hint.get("description", str(hint))
                    )
                else:
                    normalized.append(str(hint))
            parsed["test_hints"] = normalized
        # safety check: filter affected_files to only existing ones
        if available_files and "affected_files" in parsed:
            parsed["affected_files"] = [
                f for f in parsed["affected_files"]
                if f in available_files
            ]
            # if model still returned nothing valid, fall back
            if not parsed["affected_files"]:
                parsed["affected_files"] = available_files

        return parsed

    except json.JSONDecodeError:
        print(f"[Issue Parser] Warning: invalid JSON returned. Raw output:\n{raw}")
        return {
            "intent": issue_text,
            "affected_files": available_files or ["target.py"],
            "expected_behavior": "code should pass all tests",
            "test_hints": []
        }