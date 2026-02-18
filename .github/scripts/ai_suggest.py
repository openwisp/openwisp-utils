import os

from google import genai
from google.genai import types


def get_error_logs():
    log_file = "failed_logs.txt"
    if not os.path.exists(log_file):
        return "No failed logs found."
    try:
        with open(log_file, "r") as f:
            content = f.read()
            return content[-15000:]
    except Exception as e:
        return f"Error reading logs: {e}"


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Skipping: No API Key found.")
        return

    client = genai.Client(api_key=api_key)

    repo_context = "No repository context available."
    if os.path.exists("repo_context.xml"):
        try:
            with open("repo_context.xml", "r") as f:
                repo_context = f.read()
        except Exception:
            pass

    error_log = get_error_logs()

    system_instruction = """
    You are an automated CI Triage Bot for the OpenWISP project.
    Your goal is to analyze CI failure logs and provide helpful, actionable feedback.

    Categorize the failure into one of these types:
    1. **Code Style/QA**: (flake8, isort, black). Remediation: Run `openwisp-qa-format`.
    2. **Commit Message**: (checkcommit). Remediation: Propose a correct message.
    3. **Test Failure**: (incorrect test, incorrect logic).
       - Compare function logic vs test assertion.
       - If logic matches name but test is impossible, fix test.
       - If logic is wrong, fix code.

    Response Format:
    - Friendly greeting.
    - Clearly state WHAT failed.
    - Provide the command to fix it or the code snippet.
    - Use Markdown.
    """

    prompt = f"""
    Fix this failing test.

    FAILURE LOGS:
    {error_log}

    CODE CONTEXT:
    {repo_context}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction, temperature=0.4
            ),
        )
        print(f"## Report\n\n{response.text}")
    except Exception as e:
        print(f"Generation Failed: {e}")


if __name__ == "__main__":
    main()
