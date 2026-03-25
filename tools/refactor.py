import json
import subprocess
from pathlib import Path

from xai_sdk.chat import user


def refactor(
    target_dir: Path, filename: str, client, model: str, apply_fixes: bool = False
) -> str:
    path = target_dir / filename
    if not path.exists():
        return json.dumps({"error": f"File not found: {filename}"})
    if not filename.endswith(".py"):
        return json.dumps({"error": "Only Python files supported."})
    code = path.read_text(encoding="utf-8", errors="replace")

    # Run pylint
    try:
        result = subprocess.run(
            ["pylint", "--output-format=json", filename],
            cwd=str(target_dir),
            capture_output=True,
            text=True,
            timeout=60,
        )
        issues_raw = result.stdout.strip()
        issues = json.loads(issues_raw) if issues_raw else []
    except FileNotFoundError:
        return json.dumps(
            {"error": "pylint not found. Run `uv add --dev pylint` in project root."}
        )
    except json.JSONDecodeError:
        issues = []
    except Exception as e:
        return json.dumps({"error": f"Pylint error: {str(e)}"})

    if not issues:
        return json.dumps(
            {"issues": 0, "message": "No pylint issues found. Code is good!"}
        )

    issues_summary = "\\n".join(
        [
            f"{issue.get('message', 'Unknown')} [{issue.get('symbol', '')}] at line {issue.get('location', {}).get('line', '?')}"
            for issue in issues[:10]
        ]
    )

    prompt = f"""Fix these pylint issues in {filename}:
{issues_summary}

Full code:
```python
{code}
```

Output ONLY the full refactored Python code. Fix all issues without changing functionality. Add minimal docstrings if missing, remove unused, fix style.

"""

    try:
        chat = client.chat.create(model=model, temperature=0.1)
        chat.append(user(prompt))
        response = chat.sample()
        suggested_code = response.content.strip()

        # Try to extract code from markdown
        start_marker = "```python"
        end_marker = "```"
        if start_marker in suggested_code:
            start = suggested_code.find(start_marker) + len(start_marker)
            end = suggested_code.find(end_marker, start)
            if end != -1:
                suggested_code = suggested_code[start:end].strip()
        elif end_marker in suggested_code:
            start = suggested_code.find(end_marker) + len(end_marker)
            end = suggested_code.find(end_marker, start)
            if end != -1:
                suggested_code = suggested_code[start:end].strip()

        result = {
            "issues_found": len(issues),
            "preview": (
                suggested_code[:200] + "..."
                if len(suggested_code) > 200
                else suggested_code
            ),
            "fix_length": len(suggested_code),
        }

        if apply_fixes:
            path.write_text(suggested_code, encoding="utf-8")
            result["status"] = "fixes_applied"

        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Grok API error: {str(e)}"})
