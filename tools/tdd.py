import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from xai_sdk import Client
from xai_sdk.chat import user

load_dotenv()
console = Console()
client = Client(api_key=os.getenv("XAI_API_KEY"))
MODEL = os.getenv("GROK_MODEL", "grok-beta")


def generate_code(chat_prompt: str) -> str:
    chat = client.chat.create(model=MODEL)
    chat.append(user(chat_prompt))
    msg = chat.sample()
    content = msg.content or ""
    # Strip code block markers
    if "```python" in content.lower():
        lines = content.splitlines()
        start_i = 0
        for i, line in enumerate(lines):
            if "```python" in line.lower():
                start_i = i + 1
                break
        end_i = len(lines)
        for i in range(start_i, len(lines)):
            if "```" in lines[i].lower():
                end_i = i
                break
        content = "\n".join(lines[start_i:end_i]).strip()
    return content


def get_failing_test_name(failures: str) -> str:
    for line in failures.splitlines():
        if "FAILED " in line:
            try:
                after_failed = line.split("FAILED ", 1)[1]
                before_dash = after_failed.split(" - ", 1)[0].strip()
                test_name = before_dash.split("::")[-1].strip()
                return test_name
            except IndexError:
                pass
    return "failing tests"


def spawn_subagent_and_wait(goal: str, max_steps: int = 10) -> str:
    shared_dir = Path("agent_shared")
    shared_dir.mkdir(exist_ok=True, parents=True)
    agent_id = str(uuid.uuid4())
    status_file = shared_dir / f"{agent_id}.json"
    init_status = {
        "agent_id": agent_id,
        "status": "spawning",
        "goal": goal[:200],
        "timestamp": time.time(),
    }
    status_file.write_text(json.dumps(init_status, indent=2), encoding="utf-8")
    cmd = [
        sys.executable,
        "agent.py",
        "--target_dir",
        ".",
        "--agent_id",
        agent_id,
        "--goal",
        goal,
        "--max_steps",
        str(max_steps),
        "--model",
        MODEL,
    ]
    proc = subprocess.Popen(cmd, cwd=".")
    timeout = 600  # 10 minutes
    polled = 0
    while polled < timeout:
        time.sleep(5)
        polled += 5
        if not status_file.exists():
            continue
        try:
            st = json.loads(status_file.read_text(encoding="utf-8"))
            status = st.get("status", "unknown")
            if status in ("done", "error", "timeout"):
                output = st.get("output", "")
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                console.print(Panel(f"Subagent {agent_id[:8]}... done ({status})", title="🤖", style="cyan"))
                return output
        except (json.JSONDecodeError, KeyError):
            pass
    console.print(Panel("Subagent timeout", title="⚠️", style="yellow"))
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    return "Timeout - subagent did not complete"


def main():
    parser = argparse.ArgumentParser(description="Autonomous TDD using Grok")
    parser.add_argument("--spec", required=True, help="Feature specification")
    parser.add_argument(
        "--module", required=True, help="Module path e.g. utils.calc (without .py)"
    )
    parser.add_argument("--max-iters", type=int, default=10)
    parser.add_argument("--agent-mode", action="store_true", help="Use sub-agents to debug/fix failures")
    args = parser.parse_args()

    impl_file = Path(args.module + ".py")
    test_file = Path("tests", f"test_{args.module}.py")

    impl_file.parent.mkdir(exist_ok=True, parents=True)
    test_file.parent.mkdir(exist_ok=True, parents=True)

    # Red phase
    test_prompt = f"""Generate comprehensive pytest unit tests for module '{args.module}'.

Specification:
{args.spec}

Output ONLY the code for tests/test_{args.module}.py"""
    console.print(Panel("🟥 RED: Generating tests", title="TDD"))
    tests_code = generate_code(test_prompt)
    test_file.write_text(tests_code, encoding="utf-8")
    console.print(f"[green]Tests written: {test_file}[/green]")

    # Green loop
    for i in range(1, args.max_iters + 1):
        console.print(Panel(f"🟩 GREEN #{i}/{args.max_iters}: Testing", title="TDD"))
        result = subprocess.run(
            ["pytest", str(test_file), "-v", "--tb=short"],
            text=True,
            capture_output=True,
            cwd=".",
        )
        if result.returncode == 0:
            console.print(Panel("✅ ALL TESTS PASSED!", title="TDD", style="green"))
            if args.agent_mode:
                try:
                    subprocess.run(["git", "add", "."], cwd=".", check=False, capture_output=True)
                    commit_msg = f"TDD: Green on {args.spec[:80]}"
                    commit_result = subprocess.run(
                        ["git", "commit", "-m", commit_msg],
                        cwd=".", capture_output=True, text=True
                    )
                    if commit_result.returncode == 0:
                        console.print(Panel(f"✅ Git committed: {commit_msg}", title="Git", style="green"))
                    else:
                        console.print(Panel("No changes to commit.", title="Git", style="yellow"))
                except Exception as e:
                    console.print(f"[red]Git error: {e}[/red]")
            return
        failures = result.stdout + result.stderr
        console.print(f"[red]Tests failed. Failures preview:\n{failures[:400]}...[/red]")
        current_code = impl_file.read_text(encoding="utf-8") if impl_file.exists() else ""
        if args.agent_mode:
            test_name = get_failing_test_name(failures)
            goal = f"Debug and fix failing test: {test_name}"
            console.print(Panel(f"🤖 Spawning sub-agent: {goal}", title="Agent Mode"))
            sub_output = spawn_subagent_and_wait(goal, max_steps=10)
            console.print(f"[blue]Sub-agent output preview: {sub_output[:300]}...[/blue]")
        else:
            fix_prompt = f"""Implement '{args.module}.py' to pass these tests:

Tests:
```
{test_file.read_text(encoding="utf-8")}
```

Failures:
```
{failures}
```

Current code:
```
{current_code}
```

Output ONLY the code for '{args.module}.py'."""
            console.print(Panel("🖊️ REF: Generate impl code", title="TDD"))
            new_code = generate_code(fix_prompt)
            impl_file.write_text(new_code, encoding="utf-8")
            console.print(f"[blue]Impl updated: {impl_file}[/blue]")

    console.print(Panel("⚠️ Max iterations reached without passing tests", title="TDD", style="yellow"))


if __name__ == "__main__":
    main()
