import json
import subprocess
from pathlib import Path
from xai_sdk import Client
from xai_sdk.chat import user

def hypothesize_fix(client: Client, error_info: dict, context: str) -> dict:
    prompt = f'''You are an expert code debugger. Analyze the following error from a shell command and suggest precise, actionable fixes to make the command succeed.

Command executed: {error_info.get("cmd", "")}

Return code: {error_info.get("rc", 0)}

Stdout (truncated): {error_info.get("stdout", "")[:500]}

Stderr (truncated): {error_info.get("stderr", "")[:1000]}

Relevant context from files:
{context}

Your response must be *ONLY* a valid JSON object with no additional text, code blocks, or explanations outside the JSON. Use this exact schema:

{{
  "hypothesis": "Brief explanation of the problem and proposed solution (1-2 sentences).",
  "fix_actions": [
    {{
      "type": "write_file",
      "filename": "relative/path/to/file.py from project root",
      "content": "the FULL new content of the file as a single string. Use \\\\n for newlines."
    }},
    {{
      "type": "run_shell",
      "cmd": "exact shell command to run, e.g. pip install -r requirements.txt"
    }},
    {{
      "type": "delete_file",
      "filename": "relative/path/to/file"
    }}
  ]
}}

If you cannot determine a fix, use empty fix_actions. Do not add extra fields.'''

    chat = client.chat.create(model="grok-4-1-fast-reasoning", temperature=0.0)
    chat.append(user(prompt))
    try:
        msg = chat.sample()
        content = msg.content.strip()
        # Extract JSON if in code block
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            parts = content.split('```')
            for p in parts:
                if p.strip().startswith('{'):
                    content = p.strip()
                    break
        fix_json = json.loads(content)
        return fix_json
    except json.JSONDecodeError as e:
        return {"error": "JSON parse failed", "raw": content}
    except Exception as e:
        return {"error": str(e), "raw_response": getattr(msg, 'content', '') if 'msg' in locals() else ""}

def auto_debug(client: Client, target_dir: Path, cmd: str, context_files: list[str] = [], max_iters: int = 5) -> dict:
    log = []
    target_dir = Path(target_dir)
    for iter_num in range(1, max_iters + 1):
        log.append(f"=== Debug Iteration {iter_num}/{max_iters} ===")
        # Run the command
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60, cwd=str(target_dir))
        except subprocess.TimeoutExpired:
            return {"success": False, "reason": "Command timed out", "log": "\n".join(log)}
        except Exception as e:
            return {"success": False, "reason": str(e), "log": "\n".join(log)}
        error_info = {
            "cmd": cmd,
            "rc": r.returncode,
            "stdout": r.stdout,
            "stderr": r.stderr
        }
        log.append(f"RC: {r.returncode}\nSTDOUT: {r.stdout.strip()}\nSTDERR: {r.stderr.strip()}")
        if r.returncode == 0:
            log.append("✅ COMMAND SUCCEEDED!")
            return {"success": True, "iterations": iter_num, "log": "\n".join(log)}
        # Gather context
        context = ""
        for fname in context_files:
            fpath = target_dir / fname
            if fpath.is_file():
                try:
                    ctx = fpath.read_text(encoding='utf-8', errors='replace')[:4000]
                    context += f"\n=== {fname} ===\n{ctx}"
                except Exception as e:
                    context += f"\n=== {fname} (error: {e}) ==="
        # Get fix hypothesis
        fix = hypothesize_fix(client, error_info, context)
        log.append(f"Hypothesis: {fix.get('hypothesis', 'N/A')}")
        actions = fix.get('fix_actions', [])
        log.append(f"Proposed {len(actions)} actions")
        if not actions:
            log.append("No actions proposed.")
            break
        # Apply actions
        applied = 0
        for action in actions:
            atype = action.get('type')
            log.append(f"Applying {atype}: {action}")
            try:
                if atype == 'write_file':
                    filename = action['filename']
                    content = action['content'].replace('\\\\n', '\n')
                    path = target_dir / filename
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content, encoding='utf-8')
                    applied += 1
                elif atype == 'run_shell':
                    ar = subprocess.run(action['cmd'], shell=True, cwd=str(target_dir), capture_output=True, text=True, timeout=60)
                    log.append(f"  Shell RC: {ar.returncode}, out: {ar.stdout.strip() or ar.stderr.strip()}")
                    applied += 1
                elif atype == 'delete_file':
                    (target_dir / action['filename']).unlink(missing_ok=True)
                    applied += 1
                else:
                    log.append(f"Unknown action: {atype}")
            except Exception as e:
                log.append(f"Apply error: {e}")
        log.append(f"Applied {applied}/{len(actions)} actions successfully")
    return {"success": False, "reason": f"Failed after {max_iters} iterations", "iterations": max_iters, "log": "\n".join(log)}
