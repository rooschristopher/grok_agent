import argparse
import subprocess
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from xai_sdk import Client
from xai_sdk.chat import user
from rich.console import Console
from rich.panel import Panel

from tools.refactor import refactor

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

def main():
    parser = argparse.ArgumentParser(description="Autonomous TDD using Grok")
    parser.add_argument("--spec", required=True, help="Feature specification")
    parser.add_argument("--module", required=True, help="Module path e.g. utils.calc (without .py)")
    parser.add_argument("--cov", action="store_true", help="Enable pytest-cov reporting")
    parser.add_argument("--max-iters", type=int, default=10)
    parser.add_argument("--max-refactors", type=int, default=3)
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
        console.print(Panel(f"🟩 GREEN #{i}: Testing", title="TDD"))
        pytest_cmd = ["pytest", str(test_file), "-v", "--tb=short"]
        result = subprocess.run(pytest_cmd, text=True, capture_output=True, cwd=".")
        if result.returncode == 0:
            console.print(Panel("✅ GREEN PASSED! Starting refactor phase", title="TDD", style="green"))
            break
        failures = result.stdout + result.stderr
        current_code = impl_file.read_text(encoding="utf-8") if impl_file.exists() else ""
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
        console.print(Panel("🖊️  Generate code", title="TDD"))
        new_code = generate_code(fix_prompt)
        impl_file.write_text(new_code, encoding="utf-8")
        console.print(f"[blue]Impl updated: {impl_file}[/blue]")
    else:
        console.print(Panel("⚠️ Max iters reached", title="TDD", style="yellow"))
        return

    # Refactor phase - enhanced with multiple passes
    target_dir = Path(".")
    impl_filename = args.module + ".py"
    refactors_done = 0
    for refactors_done in range(args.max_refactors):
        console.print(Panel(f"🔄 REFRACTOR #{refactors_done+1}/{args.max_refactors}: pylint + grok fixes", title="TDD"))
        refactor_json = refactor(target_dir, impl_filename, client, MODEL, apply_fixes=True)
        try:
            data = json.loads(refactor_json)
            issues = data.get('issues_found', 0)
            console.print(f"[cyan]Fixed {issues} pylint issues[/cyan]")
            if issues == 0:
                console.print(Panel("✨ Refactor complete: Clean code!", title="TDD", style="bright_green"))
                break
        except Exception as e:
            console.print(f"[red]Refactor error: {e}[/red]")
        refactors_done += 1  # redundant

    # Retest after refactor
    console.print(Panel("🔄 Retest after refactor", title="TDD"))
    result = subprocess.run(["pytest", str(test_file), "-v", "--tb=short"], text=True, capture_output=True, cwd=".")
    if result.returncode != 0:
        console.print(Panel("❌ Tests broke after refactor! Manual review needed.", title="TDD", style="red"))
        return
    console.print("[green]✅ Still green after refactor![/green]")

    # Coverage phase
    if args.cov:
        console.print(Panel("📊 COVERAGE: pytest-cov report", title="TDD"))
        cov_cmd = ["pytest", str(test_file), "-v", "--tb=no",
                   f"--cov={args.module}",
                   "--cov-report=term-missing",
                   "--cov-report=html:htmlcov"]
        result_cov = subprocess.run(cov_cmd, text=True, capture_output=True, cwd=".")
        console.print(result_cov.stdout)
        if result_cov.returncode != 0:
            console.print("[yellow]Coverage command warnings, but check report.[/yellow]")
        else:
            console.print(Panel("📈 Coverage HTML in htmlcov/index.html", title="TDD", style="green"))

    console.print(Panel("🎉 TDD CYCLE COMPLETE: Red-Green-Refactor-Cov!", title="TDD", style="bright_green"))

if __name__ == "__main__":
    main()