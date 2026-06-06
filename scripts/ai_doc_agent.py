import os
import subprocess
from openai import OpenAI

def get_git_diff():
    try:
        result = subprocess.run(['git', 'diff', 'HEAD~1', 'HEAD'], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        print(f"Error getting git diff: {e}")
        return ""

def generate_summary(diff_text, api_key):
    if not diff_text or not diff_text.strip():
        return "No significant changes detected."

    try:
        client = OpenAI(api_key=api_key)

        prompt = f"""
        You are an AI Repository Documentation Agent.
        Review the following git diff and provide a highly professional architectural summary and changelog.
        The summary should focus on structural modifications, new dependencies, and system architecture changes.
        Format your response in Markdown, suitable for a README.md changelog section.

        Git Diff:
        ```diff
        {diff_text}
        ```
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Using 3.5 turbo for speed/cost efficiency in CI
            messages=[
                {"role": "system", "content": "You are a senior software architect documenting repository changes."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"OpenAI API Error: {e}")
        # Fallback to local parsing if API fails
        return fallback_summary(diff_text)

def fallback_summary(diff_text):
    lines = diff_text.split('\n')
    files_changed = []
    for line in lines:
        if line.startswith('diff --git'):
            parts = line.split(' ')
            if len(parts) >= 3:
                files_changed.append(parts[2][2:])

    if not files_changed:
        return "No specific files could be parsed from diff."

    summary = f"### Recent Automated Updates (Fallback)\n\n"
    summary += f"The AI documentation agent detected changes in the following files:\n"
    for f in files_changed:
        summary += f"- `{f}`\n"

    return summary

def update_readme_changelog(summary):
    import re
    readme_path = 'README.md'
    section_marker = 'CHANGELOG'
    try:
        with open(readme_path, 'r') as f:
            content = f.read()

        start_marker = f"<!-- {section_marker}_START -->"
        end_marker = f"<!-- {section_marker}_END -->"

        pattern = re.compile(f"({start_marker}).*?({end_marker})", re.DOTALL)

        if pattern.search(content):
            new_readme_content = pattern.sub(rf"\1\n{summary}\n\2", content)
            with open(readme_path, 'w') as f:
                f.write(new_readme_content)
            print(f"Updated {section_marker} in README.md")
        else:
            print(f"Markers for {section_marker} not found in README.md")

    except FileNotFoundError:
        print(f"{readme_path} not found.")

if __name__ == "__main__":
    print("Running AI Documentation Agent...")

    api_key = os.environ.get('OPENAI_API_KEY')
    diff = get_git_diff()

    if not api_key:
        print("OPENAI_API_KEY not found. Using fallback summarization.")
        summary = fallback_summary(diff)
    else:
        print("OPENAI_API_KEY found. Calling OpenAI API...")
        summary = generate_summary(diff, api_key)

    update_readme_changelog(summary)
    print("AI Documentation update complete.")
