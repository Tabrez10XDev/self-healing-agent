import ollama
import json
import re


def parse_issue(issue_text: str) -> dict:
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

    prompt = f"""You are a software engineering assistant that reads bug reports.

Analyze this GitHub issue and extract structured information.

Issue:
{issue_text}

Return ONLY a JSON object with these exact keys:
- intent: one sentence describing what needs to be fixed
- affected_files: list of Python filenames likely involved
- expected_behavior: what the code should do when fixed
- test_hints: list of edge cases the fix must handle

Return raw JSON only. No explanation. No markdown fences."""

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

    # strip markdown fences if model ignores instructions
    if raw.startswith("```"):
        raw = re.sub(r"```(?:json)?\n?", "", raw)
        raw = raw.replace("```", "").strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # if model returns garbage, return a safe fallback
        print(f"Warning: issue parser returned invalid JSON. Raw output:\n{raw}")
        return {
            "intent": issue_text,
            "affected_files": ["target.py"],
            "expected_behavior": "code should pass all tests",
            "test_hints": []
        }