import os
from agents.issue_parser import parse_issue
from agents.navigator import navigate
from agents.coder import generate_fix
from agents.test_runner import apply_and_test
from agents.debugger import diagnose
from agents.navigator import get_file_structure


def run(issue_text: str, repo_path: str, test_file: str = "test_target.py", max_attempts: int = 3):
    print("\n" + "="*50)
    print("SELF-HEALING AGENT STARTING")
    print("="*50)

    # --- Phase A: runs once ---

    # Step 1: parse the issue
    print("\n[Step 1/5] Parsing issue...")

    # first do a quick scan to get available files
    structure = get_file_structure(repo_path)
    available_files = [
        f for f in structure.keys()
        if not f.startswith("test_")
        and not f.startswith("agents/")
        and f.endswith(".py")
        and f not in ("orchestrator.py", "agent.py")
    ]
    print(f"  Available files: {available_files}")

    issue = parse_issue(issue_text, available_files=available_files)

    print(f"  Intent: {issue['intent']}")
    print(f"  Affected files: {issue['affected_files']}")

    # Step 2: navigate the codebase
    print("\n[Step 2/5] Navigating codebase...")
    nav_result = navigate(repo_path, issue["affected_files"])
    relevant_code = nav_result["relevant_code"]

    if not relevant_code:
        print("Navigator found no relevant files. Aborting.")
        return False

    # --- Phase B: retry loop ---

    previous_diagnoses = []
    previous_fix = None

    for attempt in range(1, max_attempts + 1):
        print(f"\n{'='*50}")
        print(f"ATTEMPT {attempt}/{max_attempts}")
        print("="*50)

        # Step 3: generate a fix
        print("\n[Step 3/5] Generating fix...")
        diagnosis_text = previous_diagnoses[-1] if previous_diagnoses else None
        fixed_code = generate_fix(
            issue=issue,
            relevant_code=relevant_code,
            previous_attempt=previous_fix,
            diagnosis=diagnosis_text
        )

        # Step 4: apply fix and run tests
        print("\n[Step 4/5] Applying fix and running tests...")
        test_result = apply_and_test(fixed_code, repo_path, test_file)

        # Step 5: check result
        if test_result["passed"]:
            print("\n" + "="*50)
            print(f"SUCCESS on attempt {attempt}!")
            print("All tests passing.")
            print("="*50)
            return True

        print(f"\n[Step 5/5] Tests failed. Running debugger...")

        # get the fixed code as a string for the debugger
        previous_fix = list(fixed_code.values())[0] if fixed_code else ""

        # read original code for comparison
        original_file = issue["affected_files"][0]
        original_path = os.path.join(repo_path, original_file)
        with open(original_path, "r") as f:
            original_code = f.read()

        # diagnose the failure
        debug_result = diagnose(
            original_code=original_code,
            fixed_code=previous_fix,
            test_output=test_result["output"],
            previous_diagnoses=previous_diagnoses
        )

        previous_diagnoses.append(debug_result.get("diagnosis", ""))

        # update relevant_code with current state of the file for next attempt
        with open(original_path, "r") as f:
            relevant_code[original_file] = f.read()

    print("\n" + "="*50)
    print(f"FAILED: Could not fix all tests in {max_attempts} attempts.")
    print("="*50)
    return False


if __name__ == "__main__":
    issue_text = """
    The calculate_average function crashes with ZeroDivisionError when given an empty list.
    The reverse_string function returns only the last character instead of the full reversed string.
    The count_vowels function does not count uppercase vowels like A, E, I, O, U.
    All three functions need to be fixed.
    """

    repo_path = os.path.dirname(os.path.abspath(__file__))

    run(
        issue_text=issue_text,
        repo_path=repo_path,
        test_file="test_target.py",
        max_attempts=3
    )